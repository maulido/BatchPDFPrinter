import os
import time
import shutil
import threading
import subprocess
import customtkinter as ctk
import win32file
import win32event
import win32con
from tkinter import filedialog, messagebox
from tooltip import add_tooltip

class AutoPrintWindow(ctk.CTkToplevel):
    """
    AutoPrintWindow provides a background daemon (watcher) that polls a specific directory
    for new PDF files. Upon detecting a file, it automatically prints it using SumatraPDF
    and either moves it to a 'Done' subfolder or deletes it permanently.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Auto-Print Monitor (Smart Watcher)")
        self.geometry("600x550")
        self.minsize(500, 450)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        
        self.is_watching = False
        self.watch_thread = None
        self.failed_files = set()
        self.target_folder_var = ctk.StringVar()
        self.action_var = ctk.StringVar(value="move") # 'move' or 'delete'
        
        # Setup UI
        self._build_ui()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _build_ui(self):
        """
        Builds the graphical user interface for the auto-print monitor,
        including folder selection, action radios, and the activity log console.
        """
        # Folder Selection
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(folder_frame, text="Watch Folder:").pack(side="left", padx=5)
        ctk.CTkEntry(folder_frame, textvariable=self.target_folder_var, state="disabled").pack(side="left", fill="x", expand=True, padx=5)
        self.btn_browse = ctk.CTkButton(folder_frame, text="Browse", width=80, command=self.browse_folder)
        self.btn_browse.pack(side="left", padx=5)
        add_tooltip(self.btn_browse, "Select the folder that the robot should monitor.")
        
        # Action After Print
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(action_frame, text="After printing a file:").pack(side="left", padx=5)
        self.rb_move = ctk.CTkRadioButton(action_frame, text="Move to 'Done' sub-folder (Recommended)", variable=self.action_var, value="move")
        self.rb_move.pack(side="left", padx=10)
        add_tooltip(self.rb_move, "Safely archives printed files into a 'Done' subfolder to prevent duplicate printing.")
        
        self.rb_delete = ctk.CTkRadioButton(action_frame, text="Delete permanently", variable=self.action_var, value="delete")
        self.rb_delete.pack(side="left", padx=10)
        add_tooltip(self.rb_delete, "WARNING: Automatically deletes the PDF file from your hard drive after printing.")
        
        # Notice
        info_lbl = ctk.CTkLabel(self, text="ℹ️ The watcher will use the Print Settings (Paper Size, Printer, etc.)\ncurrently configured in the main Batch PDF Printer window.", text_color="#1976D2")
        info_lbl.pack(pady=10)
        
        # Controls
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_toggle = ctk.CTkButton(ctrl_frame, text="▶ Start Watching", font=ctk.CTkFont(weight="bold"), fg_color="#388E3C", hover_color="#2E7D32", command=self.toggle_watch)
        self.btn_toggle.pack(fill="x", ipady=5)
        add_tooltip(self.btn_toggle, "Start/Stop the background polling service.")
        
        # Log Console
        ctk.CTkLabel(self, text="Activity Log:").pack(anchor="w", padx=20)
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_console.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
    def log(self, message):
        """
        Appends a timestamped message to the activity log console.
        This is typically called safely from the main thread using master.after(0, ...)
        
        Args:
            message (str): The text message to log.
        """
        timestamp = time.strftime("[%H:%M:%S]")
        full_msg = f"{timestamp} {message}\n"
        
        self.log_console.configure(state="normal")
        self.log_console.insert("end", full_msg)
        self.log_console.see("end")
        self.log_console.configure(state="disabled")
        
    def browse_folder(self):
        """
        Opens a directory selection dialog for the user to choose the folder to watch.
        """
        folder = filedialog.askdirectory(title="Select folder to watch")
        if folder:
            self.target_folder_var.set(folder)
            
    def toggle_watch(self):
        """
        Starts or stops the background folder watcher thread.
        Validates target folder and printer selection before starting.
        """
        if not self.is_watching:
            folder = self.target_folder_var.get()
            if not folder or not os.path.exists(folder):
                messagebox.showwarning("Warning", "Please select a valid folder to watch.")
                return
                
            # Check if printer is valid in master
            printer = self.master.printer_var.get()
            if not printer or printer == "No Printer Found":
                messagebox.showwarning("Warning", "No valid printer selected in main window.")
                return
                
            self.is_watching = True
            self.failed_files.clear()
            self.btn_browse.configure(state="disabled")
            self.rb_move.configure(state="disabled")
            self.rb_delete.configure(state="disabled")
            self.btn_toggle.configure(text="⏹ Stop Watching", fg_color="#D32F2F", hover_color="#B71C1C")
            
            self.log(f"Started watching folder: {folder}")
            self.log(f"Target Printer: {printer}")
            
            self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
            self.watch_thread.start()
        else:
            self.is_watching = False
            self.btn_toggle.configure(state="disabled", text="Stopping...")
            # Thread will naturally die within 3 seconds
            self.after(3500, self._on_stopped)
            
    def _on_stopped(self):
        """
        Callback executed after the watcher thread completely terminates.
        Re-enables the UI controls.
        """
        self.btn_browse.configure(state="normal")
        self.rb_move.configure(state="normal")
        self.rb_delete.configure(state="normal")
        self.btn_toggle.configure(state="normal", text="▶ Start Watching", fg_color="#388E3C", hover_color="#2E7D32")
        self.log("Watcher stopped.")    
        
    def _scan_and_print(self, folder, done_folder, action):
        try:
            # Re-fetch files
            files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
            for f in files:
                if not self.is_watching: break
                if f in self.failed_files: continue
                
                filepath = os.path.join(folder, f)
                if os.path.isfile(filepath):
                    # Ensure the file is not locked by another process (e.g. still downloading)
                    if not self._is_file_ready(filepath):
                        continue
                        
                    self.master.after(0, self.log, f"Found '{f}', preparing to print...")
                    
                    # Fetch latest settings from master
                    printer = self.master.printer_var.get()
                    settings_args = self.master._get_print_settings()
                    sumatra = self.master.sumatra_path
                    
                    try:
                        # Optionally apply watermark (reuse master logic)
                        target_pdf = filepath
                        is_temp_wm = False
                        if self.master.watermark_enabled_var.get():
                            self.master.after(0, self.log, f"Applying watermark to '{f}'...")
                            wm_text = self.master.watermark_text_var.get().strip()
                            wm_color = self.master.watermark_color_var.get()
                            wm_opacity = self.master.watermark_opacity_var.get()
                            target_pdf = self.master.apply_watermark(filepath, wm_text, wm_color, wm_opacity)
                            is_temp_wm = True
                            
                        self.master.after(0, self.log, f"Printing '{f}' to {printer}...")
                        cmd = [sumatra, "-print-to", printer, "-silent"]
                        if settings_args:
                            cmd.extend(["-print-settings", ",".join(settings_args)])
                        cmd.append(target_pdf)
                        
                        # Print it
                        subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
                        
                        # Cleanup watermark if temp
                        if is_temp_wm:
                            try: os.remove(target_pdf)
                            except: pass
                            
                        # Handle Original File
                        if action == "move":
                            dest = os.path.join(done_folder, f)
                            # Handle name collision
                            if os.path.exists(dest):
                                base, ext = os.path.splitext(f)
                                dest = os.path.join(done_folder, f"{base}_{int(time.time())}{ext}")
                            shutil.move(filepath, dest)
                            self.master.after(0, self.log, f"Success! Moved to Done folder.")
                        elif action == "delete":
                            os.remove(filepath)
                            self.master.after(0, self.log, f"Success! Deleted file.")
                            
                    except subprocess.TimeoutExpired as print_e:
                        self.master.after(0, self.log, f"ERROR: SumatraPDF timed out (60s) for '{f}'")
                        # Rename file so it doesn't get stuck in a loop
                        err_dest = os.path.join(folder, f"{f}.error")
                        try: 
                            os.rename(filepath, err_dest)
                        except: 
                            self.failed_files.add(f)
                            self.master.after(0, self.log, f"Could not rename '{f}'. Ignored in future polling.")
                            
                    except Exception as print_e:
                        self.master.after(0, self.log, f"ERROR processing '{f}': {print_e}")
                        # Cleanup watermark if temp
                        if 'is_temp_wm' in locals() and is_temp_wm and 'target_pdf' in locals():
                            try: os.remove(target_pdf)
                            except: pass
                        # Rename file so it doesn't get stuck in a loop
                        err_dest = os.path.join(folder, f"{f}.error")
                        try: 
                            os.rename(filepath, err_dest)
                        except: 
                            self.failed_files.add(f)
                            self.master.after(0, self.log, f"Could not rename '{f}'. Ignored in future polling.")
                            
        except Exception as e:
            self.master.after(0, self.log, f"Scanner Error: {e}")

    def _watch_loop(self):
        """
        The core background loop running in a separate daemon thread.
        Listens for file system change events to process new PDFs instantly.
        """
        folder = self.target_folder_var.get()
        action = self.action_var.get()
        
        done_folder = os.path.join(folder, "Done")
        if action == "move" and not os.path.exists(done_folder):
            try:
                os.makedirs(done_folder)
            except Exception as e:
                self.master.after(0, self.log, f"ERROR: Could not create Done folder: {e}")
                self.master.after(0, self.toggle_watch)
                return
        
        # Initial scan to catch any PDFs dropped before watching started
        self._scan_and_print(folder, done_folder, action)
        
        # Create the Windows directory change handle
        change_handle = win32file.FindFirstChangeNotification(
            folder,
            0, # Do not watch subtrees
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        )
        
        try:
            while self.is_watching:
                # Wait up to 500ms for an event to fire
                result = win32event.WaitForSingleObject(change_handle, 500)
                
                if result == win32con.WAIT_OBJECT_0:
                    # A file event occurred! Sleep for 3 seconds to let OS finish writing/downloading
                    time.sleep(3)
                    self._scan_and_print(folder, done_folder, action)
                    win32file.FindNextChangeNotification(change_handle)
                    
        finally:
            win32file.FindCloseChangeNotification(change_handle)

    def on_closing(self):
        """
        Intercepts the window close event.
        Ensures the watcher thread is properly stopped before destroying the window.
        """
        if self.is_watching:
            if not messagebox.askyesno("Confirm", "The watcher is currently running. Stop it and close?"):
                return
            self.is_watching = False
        self.destroy()

    def _is_file_ready(self, filepath):
        """
        Checks if a file is completely written and not locked by another process
        by attempting to open it in append mode.
        """
        try:
            with open(filepath, 'a'):
                pass
            return True
        except IOError:
            return False
