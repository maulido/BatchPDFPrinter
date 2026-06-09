import os
import sys
import subprocess
import threading
import tempfile
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
import win32print
from pypdf import PdfWriter, PdfReader
from tkinterdnd2 import TkinterDnD, DND_FILES

class TkinterDnD_CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# Set appearance mode and color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BatchPDFPrinterApp(TkinterDnD_CTk):
    def __init__(self):
        super().__init__()

        self.title("Batch PDF Printer")
        self.geometry("900x600")
        self.minsize(900, 500)
        
        # Set icon
        try:
            self.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
        except Exception:
            pass

        # Get the path to SumatraPDF
        self.sumatra_path = self.get_sumatra_path()

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_variables()
        self.setup_ui()
        # Load previous settings
        self.load_settings()
        
        # Start background printer status monitor
        self.check_printer_status()

        # Patch messagebox to always center on this window
        self._patch_messagebox()

        # Save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _patch_messagebox(self):
        _orig_showinfo = messagebox.showinfo
        _orig_showerror = messagebox.showerror
        _orig_showwarning = messagebox.showwarning
        _orig_askyesno = messagebox.askyesno

        messagebox.showinfo = lambda title, message, **kwargs: _orig_showinfo(title, message, parent=self, **kwargs)
        messagebox.showerror = lambda title, message, **kwargs: _orig_showerror(title, message, parent=self, **kwargs)
        messagebox.showwarning = lambda title, message, **kwargs: _orig_showwarning(title, message, parent=self, **kwargs)
        messagebox.askyesno = lambda title, message, **kwargs: _orig_askyesno(title, message, parent=self, **kwargs)

    def center_window(self, win, width, height):
        win.update_idletasks()
        # Calculate coordinates relative to the main window
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def check_printer_status(self):
        printer_name = self.printer_var.get()
        if not printer_name or printer_name == "No Printer Found":
            self.printer_status_var.set("Status: No Printer Selected")
            return
            
        try:
            hprinter = win32print.OpenPrinter(printer_name)
            info = win32print.GetPrinter(hprinter, 2)
            status_code = info['Status']
            attributes = info['Attributes']
            win32print.ClosePrinter(hprinter)
            
            # Decode common status codes
            # Windows caching often leaves status=0 but sets WORK_OFFLINE (0x400) in Attributes
            if status_code & 0x00000080 or attributes & 0x00000400: # PRINTER_STATUS_OFFLINE or PRINTER_ATTRIBUTE_WORK_OFFLINE
                self.printer_status_var.set("Status: 🔴 Offline / Disconnected")
            elif status_code == 0:
                self.printer_status_var.set("Status: 🟢 Ready")
            elif status_code & 0x00000010: # PRINTER_STATUS_PAPER_OUT
                self.printer_status_var.set("Status: 🔴 Out of Paper")
            elif status_code & 0x00000002: # PRINTER_STATUS_ERROR
                self.printer_status_var.set("Status: 🔴 Error")
            elif status_code & 0x00000008: # PRINTER_STATUS_PAPER_JAM
                self.printer_status_var.set("Status: 🔴 Paper Jam")
            elif status_code & 0x00000400: # PRINTER_STATUS_PRINTING
                self.printer_status_var.set("Status: 🟡 Printing")
            elif status_code & 0x00000200: # PRINTER_STATUS_BUSY
                self.printer_status_var.set("Status: 🟡 Busy")
            elif status_code & 0x00000001: # PRINTER_STATUS_PAUSED
                self.printer_status_var.set("Status: 🟡 Paused")
            else:
                self.printer_status_var.set(f"Status: 🟡 Other (Code {status_code})")
                
        except Exception:
            self.printer_status_var.set("Status: 🔴 Unknown / Unreachable")

    def get_sumatra_path(self):
        # When bundled with PyInstaller, the base path is sys._MEIPASS
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        sumatra_exe = os.path.join(base_path, "bin", "SumatraPDF.exe")
        if not os.path.exists(sumatra_exe):
            print(f"Warning: SumatraPDF.exe not found at {sumatra_exe}")
        return sumatra_exe

    def setup_variables(self):
        # Print Settings Variables
        self.copies_var = ctk.StringVar(value="1")
        self.paper_size_var = ctk.StringVar(value="A4")
        self.custom_width_var = ctk.StringVar(value="")
        self.custom_height_var = ctk.StringVar(value="")
        self.orientation_var = ctk.StringVar(value="As in Document (Auto)")
        self.page_range_var = ctk.StringVar(value="")
        self.color_var = ctk.StringVar(value="Color")
        self.scale_var = ctk.StringVar(value="Fit to Printable Area")
        self.duplex_var = ctk.StringVar(value="1-Sided (Simplex)")
        self.single_job_var = ctk.BooleanVar(value=False)
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.is_paused = False
        self.print_log = []

    def setup_ui(self):
        # Header Toolbar (mimicking Print Conductor)
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        add_btn = ctk.CTkButton(toolbar_frame, text="Add Documents", command=self.add_files, width=120)
        add_btn.pack(side="left", padx=(0, 5))

        add_folder_btn = ctk.CTkButton(toolbar_frame, text="Add Folder", command=self.add_folder, width=120)
        add_folder_btn.pack(side="left", padx=5)

        remove_btn = ctk.CTkButton(toolbar_frame, text="Remove Selected", command=self.remove_unchecked, fg_color="#D32F2F", hover_color="#B71C1C", width=120)
        remove_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(toolbar_frame, text="Clear List", command=self.clear_all, fg_color="#F57C00", hover_color="#E65100", width=100)
        clear_btn.pack(side="left", padx=5)
        
        update_btn = ctk.CTkButton(toolbar_frame, text="Check for Updates", command=self.check_for_updates, fg_color="#00695C", hover_color="#004D40", width=120)
        update_btn.pack(side="right", padx=5)

        # Main Content (File List)
        self.listbox_frame = ctk.CTkScrollableFrame(self, label_text="Document List")
        self.listbox_frame.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        self.listbox_frame.grid_columnconfigure(0, weight=1)
        
        # Enable Drag and Drop on the entire window
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)
        
        self.file_items = []
        
        # Table Header
        self.table_header = ctk.CTkFrame(self.listbox_frame, fg_color="transparent")
        self.table_header.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="ew")
        self.table_header.grid_columnconfigure(0, weight=1) # Filename
        self.table_header.grid_columnconfigure(1, minsize=80) # Pages
        self.table_header.grid_columnconfigure(2, minsize=130) # Date
        self.table_header.grid_columnconfigure(3, minsize=80) # Actions
        
        ctk.CTkLabel(self.table_header, text="File Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.table_header, text="Pages", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.table_header, text="Date", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", padx=5)
        ctk.CTkLabel(self.table_header, text="Actions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        # Placeholder label for empty state
        self.empty_label = ctk.CTkLabel(self.listbox_frame, text="Drop PDF files here\nor use 'Add Documents'", text_color="gray", font=ctk.CTkFont(size=14, slant="italic"))
        self.empty_label.grid(row=1, column=0, pady=50)

        # Bottom Controls
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(2, weight=1)

        printer_label = ctk.CTkLabel(bottom_frame, text="Printer:")
        printer_label.grid(row=0, column=0, padx=(10, 5), pady=15, sticky="e")

        printers = self.get_installed_printers()
        default_printer = win32print.GetDefaultPrinter()
        
        self.printer_var = ctk.StringVar(value=default_printer if default_printer in printers else (printers[0] if printers else "No Printer Found"))
        self.printer_dropdown = ctk.CTkOptionMenu(bottom_frame, values=printers, variable=self.printer_var, width=250, command=lambda _: self.check_printer_status())
        self.printer_dropdown.grid(row=0, column=1, padx=5, pady=(15, 0), sticky="w")
        
        self.printer_status_var = ctk.StringVar(value="Status: 🔍 Checking...")
        self.printer_status_label = ctk.CTkLabel(bottom_frame, textvariable=self.printer_status_var, font=ctk.CTkFont(size=12), text_color="gray")
        self.printer_status_label.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="nw")

        # Right side actions
        right_actions_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        right_actions_frame.grid(row=0, column=2, sticky="e", padx=10)

        self.single_job_cb = ctk.CTkCheckBox(right_actions_frame, text="Single Print Job", variable=self.single_job_var)
        self.single_job_cb.pack(side="left", padx=10)

        self.settings_btn = ctk.CTkButton(right_actions_frame, text="⚙ Settings", command=self.open_settings_dialog, width=100, fg_color="#455A64", hover_color="#37474F")
        self.settings_btn.pack(side="left", padx=5)

        self.preview_btn = ctk.CTkButton(right_actions_frame, text="Preview", command=self.preview_file, fg_color="#1976D2", hover_color="#1565C0", width=80)
        self.preview_btn.pack(side="left", padx=5)

        self.print_btn = ctk.CTkButton(right_actions_frame, text="Start Printing", command=self.start_print_thread, fg_color="#388E3C", hover_color="#2E7D32", width=180, font=ctk.CTkFont(weight="bold"))
        self.print_btn.pack(side="left", padx=5)
        
        # Status Bar
        self.status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", text_color="gray")
        status_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

    def open_settings_dialog(self):
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("Print Settings")
        self.center_window(settings_win, 800, 480)
        settings_win.attributes("-topmost", True)
        settings_win.grab_set()
        
        main_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left side: Form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(side="left", fill="y", padx=(0, 20))
        form_frame.grid_columnconfigure(1, weight=1)

        # Copies
        ctk.CTkLabel(form_frame, text="Copies:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkEntry(form_frame, textvariable=self.copies_var, width=60).grid(row=0, column=1, sticky="w")

        # Page Range
        ctk.CTkLabel(form_frame, text="Page Range:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkEntry(form_frame, textvariable=self.page_range_var, placeholder_text="e.g. 1-3, 5").grid(row=1, column=1, sticky="ew")

        # Paper Size
        ctk.CTkLabel(form_frame, text="Paper Size:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        paper_options = [
            "A4 (210 x 297 mm)", "A0 (841 x 1189 mm)", "A1 (594 x 841 mm)", 
            "A2 (420 x 594 mm)", "A3 (297 x 420 mm)", "A5 (148 x 210 mm)", 
            "A6 (105 x 148 mm)", "B4 (250 x 353 mm)", "B5 (176 x 250 mm)", 
            "Letter (216 x 279 mm)", "Legal (216 x 356 mm)", "Tabloid (279 x 432 mm)", 
            "Executive (184 x 267 mm)", "Custom"
        ]
        paper_dropdown = ctk.CTkOptionMenu(form_frame, values=paper_options, variable=self.paper_size_var, command=self.on_paper_change)
        paper_dropdown.grid(row=2, column=1, sticky="ew")

        # Custom Paper Size (hidden by default)
        self.custom_paper_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        ctk.CTkEntry(self.custom_paper_frame, textvariable=self.custom_width_var, placeholder_text="W (mm)", width=60).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(self.custom_paper_frame, text="x").pack(side="left")
        ctk.CTkEntry(self.custom_paper_frame, textvariable=self.custom_height_var, placeholder_text="H (mm)", width=60).pack(side="left", padx=(2, 0))
        if self.paper_size_var.get() == "Custom":
            self.custom_paper_frame.grid(row=3, column=1, sticky="w", pady=(0, 10))

        # Orientation
        ctk.CTkLabel(form_frame, text="Orientation:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkOptionMenu(form_frame, values=["As in Document (Auto)", "Portrait", "Landscape"], variable=self.orientation_var, command=self.update_preview).grid(row=4, column=1, sticky="ew")

        # Color
        ctk.CTkLabel(form_frame, text="Color Mode:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkOptionMenu(form_frame, values=["Color", "Monochrome / B&W"], variable=self.color_var).grid(row=5, column=1, sticky="ew")

        # Scaling
        ctk.CTkLabel(form_frame, text="Scaling:").grid(row=6, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkOptionMenu(form_frame, values=["Fit to Printable Area", "Fit to Page", "Actual Size"], variable=self.scale_var, command=self.update_preview).grid(row=6, column=1, sticky="ew")

        # Duplex
        ctk.CTkLabel(form_frame, text="Duplex Mode:").grid(row=7, column=0, padx=10, pady=10, sticky="e")
        ctk.CTkOptionMenu(form_frame, values=["1-Sided (Simplex)", "2-Sided (Long Edge)", "2-Sided (Short Edge)"], variable=self.duplex_var).grid(row=7, column=1, sticky="ew")

        # OK Button
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_frame, text="OK", command=settings_win.destroy, width=150).pack()

        # Right side: Visual Preview
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(preview_frame, text="Paper Preview", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.preview_canvas = ctk.CTkCanvas(preview_frame, width=350, height=380, bg="#2b2b2b", highlightthickness=0)
        self.preview_canvas.pack(padx=20, pady=10, expand=True)
        
        # Trace custom entries
        self.custom_width_var.trace_add("write", lambda *args: self.update_preview())
        self.custom_height_var.trace_add("write", lambda *args: self.update_preview())
        
        # Initial draw
        self.update_preview()

    def load_settings(self):
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    settings = json.load(f)
                
                if "printer" in settings: self.printer_var.set(settings["printer"])
                if "single_job" in settings: self.single_job_var.set(settings["single_job"])
                if "paper_size" in settings: 
                    self.paper_size_var.set(settings["paper_size"])
                    self.on_paper_change(settings["paper_size"])
                if "copies" in settings: self.copies_var.set(settings["copies"])
                if "custom_width" in settings: self.custom_width_var.set(settings["custom_width"])
                if "custom_height" in settings: self.custom_height_var.set(settings["custom_height"])
                if "orientation" in settings: self.orientation_var.set(settings["orientation"])
                if "page_range" in settings: self.page_range_var.set(settings["page_range"])
                if "color" in settings: self.color_var.set(settings["color"])
                if "scale" in settings: self.scale_var.set(settings["scale"])
                if "duplex" in settings: self.duplex_var.set(settings["duplex"])
            except Exception as e:
                print(f"Failed to load settings: {e}")

    def on_closing(self):
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        settings = {
            "printer": self.printer_var.get(),
            "single_job": self.single_job_var.get(),
            "paper_size": self.paper_size_var.get(),
            "copies": self.copies_var.get(),
            "custom_width": self.custom_width_var.get(),
            "custom_height": self.custom_height_var.get(),
            "orientation": self.orientation_var.get(),
            "page_range": self.page_range_var.get(),
            "color": self.color_var.get(),
            "scale": self.scale_var.get(),
            "duplex": self.duplex_var.get()
        }
        try:
            with open(config_file, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")
            
        self.destroy()

    def check_for_updates(self):
        import urllib.request
        import json
        import webbrowser
        from packaging import version
        
        CURRENT_VERSION = "1.0.0"
        url = "https://api.github.com/repos/maulido/BatchPDFPrinter/releases/latest"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")
            
            if latest_version and version.parse(latest_version) > version.parse(CURRENT_VERSION):
                answer = messagebox.askyesno(
                    "Update Available", 
                    f"Versi baru (v{latest_version}) tersedia!\n\nVersi saat ini: v{CURRENT_VERSION}\n\nApakah Anda ingin mengunduh pembaruan ini sekarang?"
                )
                if answer and html_url:
                    webbrowser.open(html_url)
            else:
                messagebox.showinfo(
                    "Check for Updates", 
                    f"Versi saat ini: v{CURRENT_VERSION}\n\nAnda sedang menggunakan versi terbaru aplikasi. Tidak ada pembaruan yang tersedia saat ini."
                )
        except Exception as e:
            # If no releases are found (e.g. 404 because no release has been made yet)
            messagebox.showinfo(
                "Check for Updates", 
                f"Versi saat ini: v{CURRENT_VERSION}\n\nBelum ada rilis versi terbaru di server atau tidak ada koneksi internet."
            )

    def on_paper_change(self, choice):
        if hasattr(self, 'custom_paper_frame') and self.custom_paper_frame.winfo_exists():
            if choice == "Custom":
                self.custom_paper_frame.grid(row=3, column=1, sticky="w", pady=(0, 10))
            else:
                self.custom_paper_frame.grid_remove()
        self.update_preview()

    def update_preview(self, *args):
        if not hasattr(self, 'preview_canvas') or not self.preview_canvas.winfo_exists():
            return
            
        self.preview_canvas.delete("all")
        
        # Parse paper dimensions
        paper_sel = self.paper_size_var.get()
        w_mm, h_mm = 210, 297 # Default A4
        
        if paper_sel == "Custom":
            try:
                w_mm = float(self.custom_width_var.get() or 210)
                h_mm = float(self.custom_height_var.get() or 297)
            except ValueError:
                w_mm, h_mm = 210, 297
        else:
            import re
            match = re.search(r'\((\d+)\s*x\s*(\d+)\s*mm\)', paper_sel)
            if match:
                w_mm, h_mm = float(match.group(1)), float(match.group(2))
                
        # Handle orientation
        orient = self.orientation_var.get()
        if orient == "Landscape":
            if w_mm < h_mm:
                w_mm, h_mm = h_mm, w_mm
        elif orient == "Portrait":
            if w_mm > h_mm:
                w_mm, h_mm = h_mm, w_mm
        # If Auto, we just assume portrait for the preview unless paper is inherently landscape
                
        # Calculate drawing scale to fit in canvas (max 300x320)
        max_w, max_h = 280, 320
        scale = min(max_w / max(1, w_mm), max_h / max(1, h_mm))
        
        draw_w = w_mm * scale
        draw_h = h_mm * scale
        
        cx, cy = 350/2, 380/2
        x1, y1 = cx - draw_w/2, cy - draw_h/2
        x2, y2 = cx + draw_w/2, cy + draw_h/2
        
        # Draw paper (white)
        self.preview_canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="gray")
        
        # Draw document bounding box (blue/gray to show scaling)
        scale_mode = self.scale_var.get()
        
        margin = 0
        if scale_mode == "Fit to Printable Area":
            margin = 15 # Simulate hardware margins
        elif scale_mode == "Fit to Page":
            margin = 0 # No margins
        elif scale_mode == "Actual Size":
            # For actual size, let's assume a dummy document size of A5 (148x210)
            doc_w_mm, doc_h_mm = 148, 210
            if orient == "Landscape":
                doc_w_mm, doc_h_mm = 210, 148
            doc_w = doc_w_mm * scale
            doc_h = doc_h_mm * scale
            self.preview_canvas.create_rectangle(cx - doc_w/2, cy - doc_h/2, cx + doc_w/2, cy + doc_h/2, fill="#e1f5fe", outline="#0288d1", dash=(4,4))
            
        if scale_mode != "Actual Size":
            self.preview_canvas.create_rectangle(x1 + margin, y1 + margin, x2 - margin, y2 - margin, fill="#e1f5fe", outline="#0288d1")
            
        # Add labels
        self.preview_canvas.create_text(cx, cy - 20, text=f"{paper_sel.split()[0]}", fill="#01579b", font=("Arial", 16, "bold"))
        self.preview_canvas.create_text(cx, cy + 10, text=f"{w_mm:g} x {h_mm:g} mm", fill="#01579b", font=("Arial", 12))
        self.preview_canvas.create_text(cx, cy + 30, text=f"{orient}", fill="gray", font=("Arial", 10))

    def get_installed_printers(self):
        printers = []
        try:
            # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            enum_printers = win32print.EnumPrinters(flags)
            for printer in enum_printers:
                printers.append(printer[2])
        except Exception as e:
            print(f"Error enumerating printers: {e}")
        return printers if printers else ["No Printers Found"]

    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self._add_files_to_list(pdf_files)

    def _refresh_list(self):
        if self.file_items:
            if hasattr(self, 'empty_label') and self.empty_label.winfo_exists():
                self.empty_label.grid_remove()
        else:
            if hasattr(self, 'empty_label') and self.empty_label.winfo_exists():
                self.empty_label.grid(row=1, column=0, pady=50)
                
        for i, item in enumerate(self.file_items):
            item["frame"].grid(row=i+2, column=0, padx=10, pady=2, sticky="ew")

    def move_up(self, path):
        idx = next((i for i, item in enumerate(self.file_items) if item["path"] == path), -1)
        if idx > 0:
            self.file_items[idx], self.file_items[idx-1] = self.file_items[idx-1], self.file_items[idx]
            self._refresh_list()

    def move_down(self, path):
        idx = next((i for i, item in enumerate(self.file_items) if item["path"] == path), -1)
        if idx >= 0 and idx < len(self.file_items) - 1:
            self.file_items[idx], self.file_items[idx+1] = self.file_items[idx+1], self.file_items[idx]
            self._refresh_list()

    def _add_files_to_list(self, files):
        import datetime
        existing_files = {item["path"] for item in self.file_items}
        for f in files:
            f = os.path.normpath(f)
            if f not in existing_files:
                file_name = os.path.basename(f)
                
                try:
                    with open(f, "rb") as pdf_file:
                        pages = len(PdfReader(pdf_file).pages)
                except Exception:
                    pages = "?"
                    
                try:
                    mtime = os.path.getmtime(f)
                    date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    date_str = "Unknown"
                
                item_frame = ctk.CTkFrame(self.listbox_frame, fg_color="transparent")
                item_frame.grid_columnconfigure(0, weight=1)
                item_frame.grid_columnconfigure(1, minsize=80)
                item_frame.grid_columnconfigure(2, minsize=130)
                item_frame.grid_columnconfigure(3, minsize=80)
                
                cb = ctk.CTkCheckBox(item_frame, text=file_name)
                cb.grid(row=0, column=0, sticky="w", padx=5)
                cb.select()  # Checked by default
                
                pages_lbl = ctk.CTkLabel(item_frame, text=str(pages))
                pages_lbl.grid(row=0, column=1, sticky="w", padx=5)
                
                date_lbl = ctk.CTkLabel(item_frame, text=date_str, text_color="gray")
                date_lbl.grid(row=0, column=2, sticky="w", padx=5)
                
                action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                action_frame.grid(row=0, column=3, sticky="w", padx=5)
                
                up_btn = ctk.CTkButton(action_frame, text="↑", width=30, command=lambda p=f: self.move_up(p))
                up_btn.pack(side="left", padx=2)
                
                down_btn = ctk.CTkButton(action_frame, text="↓", width=30, command=lambda p=f: self.move_down(p))
                down_btn.pack(side="left", padx=2)
                
                self.file_items.append({
                    "path": f,
                    "frame": item_frame,
                    "checkbox": cb
                })
        self._refresh_list()
        self.status_var.set(f"Loaded {len(self.file_items)} files.")

    def add_files(self):
        try:
            files = filedialog.askopenfilenames(
                title="Select PDF files",
                filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*"))
            )
            if files:
                self._add_files_to_list(files)
        except Exception as e:
            import traceback
            messagebox.showerror("Error Adding Files", f"{str(e)}\n{traceback.format_exc()}")

    def add_folder(self):
        try:
            folder = filedialog.askdirectory(title="Select Folder containing PDFs")
            if folder:
                pdf_files = []
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, file))
                self._add_files_to_list(pdf_files)
        except Exception as e:
            import traceback
            messagebox.showerror("Error Adding Folder", f"{str(e)}\n{traceback.format_exc()}")

    def remove_unchecked(self):
        to_keep = []
        for item in self.file_items:
            if item["checkbox"].get() == 1:
                to_keep.append(item)
            else:
                item["frame"].destroy()
        self.file_items = to_keep
        self._refresh_list()
        self.status_var.set(f"Loaded {len(self.file_items)} files.")

    def clear_all(self):
        for item in self.file_items:
            item["frame"].destroy()
        self.file_items.clear()
        self._refresh_list()
        self.status_var.set("Loaded 0 files.")

    def preview_file(self):
        files_to_print = [item["path"] for item in self.file_items if item["checkbox"].get() == 1]
        if not files_to_print:
            messagebox.showwarning("Warning", "Please check at least one PDF file to preview.")
            return
            
        if not os.path.exists(self.sumatra_path):
            messagebox.showerror("Error", f"SumatraPDF.exe not found at:\n{self.sumatra_path}\nCannot preview.")
            return

        is_single_job = self.single_job_var.get()

        try:
            if is_single_job and len(files_to_print) > 1:
                self.status_var.set("Merging PDFs for preview...")
                self.update_idletasks() # Force UI update
                
                merger = PdfWriter()
                for pdf in files_to_print:
                    merger.append(pdf)
                
                fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="BatchPreview_")
                os.close(fd)
                
                with open(temp_pdf_path, "wb") as f_out:
                    merger.write(f_out)
                    
                pdf_to_preview = temp_pdf_path
                self.status_var.set("Ready")
            else:
                # Preview the first checked file
                pdf_to_preview = files_to_print[0]
                
            # Close previous preview if it's still running
            if hasattr(self, 'preview_process') and self.preview_process.poll() is None:
                try:
                    self.preview_process.terminate()
                    self.preview_process.wait(timeout=1)
                except Exception:
                    pass

            self.preview_process = subprocess.Popen([self.sumatra_path, "-new-window", pdf_to_preview])
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            messagebox.showerror("Preview Error", f"Failed to open preview:\n{str(e)}\n{error_msg}")

    def start_print_thread(self):
        files_to_print = [item["path"] for item in self.file_items if item["checkbox"].get() == 1]
        if not files_to_print:
            messagebox.showwarning("Warning", "No PDF files selected to print.")
            return
            
        if not os.path.exists(self.sumatra_path):
            messagebox.showerror("Error", f"SumatraPDF.exe not found at:\n{self.sumatra_path}\nCannot print.")
            return

        selected_printer = self.printer_var.get()
        if not selected_printer or selected_printer == "No Printers Found":
            messagebox.showerror("Error", "No valid printer selected.")
            return
            
        is_single_job = self.single_job_var.get()
        
        # Modify button for pause/resume if not single job
        if not is_single_job:
            self.print_btn.configure(text="Pause", fg_color="#FBC02D", hover_color="#F9A825", command=self.toggle_pause)
            self.is_paused = False
            self.pause_event.set()
        else:
            self.print_btn.configure(state="disabled")
            
        self.status_var.set("Printing... Please wait.")
        
        # Create Progress Window
        self.progress_win = ctk.CTkToplevel(self)
        self.progress_win.title("Printing Status")
        self.center_window(self.progress_win, 500, 250)
        self.progress_win.attributes("-topmost", True)
        self.progress_win.grab_set()
        
        self.progress_label_var = ctk.StringVar(value="Starting print job...")
        lbl = ctk.CTkLabel(self.progress_win, textvariable=self.progress_label_var, wraplength=400)
        lbl.pack(pady=(25, 10), padx=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_win, width=350)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Start printing in a separate thread so UI doesn't freeze
        self.print_log = []
        threading.Thread(target=self.print_files, args=(selected_printer, files_to_print, is_single_job), daemon=True).start()

    def toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.print_btn.configure(text="Pause", fg_color="#FBC02D", hover_color="#F9A825")
        else:
            self.is_paused = True
            self.pause_event.clear()
            self.print_btn.configure(text="Resume", fg_color="#1976D2", hover_color="#1565C0")

    def _get_print_settings(self):
        settings = []
        
        # Copies
        copies = self.copies_var.get().strip()
        if copies.isdigit() and int(copies) > 1:
            settings.append(f"copies={copies}")
            
        # Page Range
        pages = self.page_range_var.get().strip()
        if pages:
            settings.append(f"{pages}")
            
        paper = self.paper_size_var.get()
        if paper == "Custom":
            w = self.custom_width_var.get().strip()
            h = self.custom_height_var.get().strip()
            if w and h:
                settings.append(f"paper={w}x{h}")
        else:
            # Extract just the paper name (e.g., 'A4' from 'A4 (210 x 297 mm)')
            paper_name = paper.split()[0]
            settings.append(f"paper={paper_name}")
            
        orientation = self.orientation_var.get()
        if orientation == "Portrait":
            settings.append("portrait")
        elif orientation == "Landscape":
            settings.append("landscape")
            
        color = self.color_var.get()
        if color == "Monochrome / B&W":
            settings.append("monochrome")
        elif color == "Color":
            settings.append("color")
            
        scale = self.scale_var.get()
        if scale == "Fit to Page":
            settings.append("fit")
        elif scale == "Actual Size":
            settings.append("noscale")
        elif scale == "Fit to Printable Area":
            settings.append("shrink")
            
        duplex = self.duplex_var.get()
        if duplex == "2-Sided (Long Edge)":
            settings.append("duplex")
        elif duplex == "2-Sided (Short Edge)":
            settings.append("duplexshort")
            
        return settings

    def print_files(self, printer_name, files_to_print, is_single_job):
        success_count = 0
        error_count = 0
        
        print_settings_args = self._get_print_settings()
        
        def update_progress(msg, progress_val):
            self.status_var.set(msg)
            if hasattr(self, 'progress_label_var'):
                self.progress_label_var.set(msg)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(progress_val)
        
        if is_single_job:
            self.after(0, update_progress, "Merging PDFs into a single print job...", 0.2)
            try:
                merger = PdfWriter()
                for pdf in files_to_print:
                    merger.append(pdf)
                
                # Create a temporary file
                fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="BatchPrint_")
                os.close(fd) # Close file descriptor so we can write to it
                
                with open(temp_pdf_path, "wb") as f_out:
                    merger.write(f_out)
                    
                self.after(0, update_progress, "Printing single merged document...", 0.6)
                cmd = [
                    self.sumatra_path,
                    "-print-to",
                    printer_name,
                    "-silent"
                ]
                if print_settings_args:
                    cmd.extend(["-print-settings", ",".join(print_settings_args)])
                cmd.append(temp_pdf_path)
                
                subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                success_count = len(files_to_print) # Treat as all successful
                self.after(0, update_progress, "Print job sent successfully!", 1.0)
                
                self.print_log.append({"file": "Single Merged Job", "status": "Success", "error": ""})
                
                # Cleanup temp file
                try:
                    os.remove(temp_pdf_path)
                except:
                    pass
                    
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"Error during single print job:\n{error_msg}")
                cmd_str = str(cmd) if 'cmd' in locals() else "N/A"
                self.print_log.append({"file": "Single Merged Job", "status": "Failed", "error": str(e)})
                messagebox.showerror("Print Error", f"Error during single print job:\n{str(e)}\nCommand: {cmd_str}")
                error_count = len(files_to_print)
                
        else:
            total = len(files_to_print)
            for i, pdf in enumerate(files_to_print):
                # Check for pause
                if self.is_paused:
                    self.after(0, update_progress, f"Paused at {i+1}/{total}... Waiting to resume", i / total)
                    self.pause_event.wait()
                
                filename = os.path.basename(pdf)
                self.after(0, update_progress, f"Printing {i+1}/{total}: {filename}", i / total)
                
                try:
                    cmd = [
                        self.sumatra_path,
                        "-print-to",
                        printer_name,
                        "-silent"
                    ]
                    if print_settings_args:
                        cmd.extend(["-print-settings", ",".join(print_settings_args)])
                    cmd.append(pdf)
                    
                    # We use creationflags=subprocess.CREATE_NO_WINDOW to hide the console window if any
                    subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    success_count += 1
                    self.print_log.append({"file": filename, "status": "Success", "error": ""})
                except subprocess.CalledProcessError as e:
                    print(f"Failed to print {pdf}: {e}")
                    self.print_log.append({"file": filename, "status": "Failed", "error": f"Return Code {e.returncode}"})
                    error_count += 1
                except Exception as e:
                    import traceback
                    error_msg = traceback.format_exc()
                    print(f"Unexpected error printing {pdf}:\n{error_msg}")
                    self.print_log.append({"file": filename, "status": "Failed", "error": str(e)})
                    error_count += 1

        self.after(0, self.print_finished, success_count, error_count)

    def print_finished(self, success_count, error_count):
        if hasattr(self, 'progress_win') and self.progress_win.winfo_exists():
            self.progress_win.destroy()
            
        # Reset button
        self.print_btn.configure(text="Start Printing", fg_color="#388E3C", hover_color="#2E7D32", state="normal", command=self.start_print_thread)
        self.status_var.set("Ready")
        
        # Show Report Window
        self.show_print_report(success_count, error_count)

    def show_print_report(self, success_count, error_count):
        report_win = ctk.CTkToplevel(self)
        report_win.title("Print Report")
        self.center_window(report_win, 700, 500)
        report_win.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(report_win, text=f"Printing Complete!\nSuccess: {success_count} | Failed: {error_count}", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(pady=10)
        
        report_frame = ctk.CTkScrollableFrame(report_win)
        report_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for item in self.print_log:
            color = "green" if item["status"] == "Success" else "red"
            text = f"[{item['status']}] {item['file']}"
            if item["error"]:
                text += f" - {item['error']}"
            ctk.CTkLabel(report_frame, text=text, text_color=color, anchor="w", justify="left").pack(fill="x", pady=2)
            
        btn_frame = ctk.CTkFrame(report_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Save Log", command=self.save_log_to_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", command=report_win.destroy).pack(side="right", padx=5)

    def save_log_to_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], title="Save Print Log")
        if file_path:
            try:
                with open(file_path, "w") as f:
                    for item in self.print_log:
                        f.write(f"[{item['status']}] {item['file']} {(' - ' + item['error']) if item['error'] else ''}\n")
                messagebox.showinfo("Success", "Print log saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log:\n{str(e)}")


if __name__ == "__main__":
    app = BatchPDFPrinterApp()
    app.mainloop()
