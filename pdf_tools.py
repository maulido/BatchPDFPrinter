import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pypdf import PdfWriter, PdfReader
from tkinterdnd2 import TkinterDnD, DND_FILES
import io
from tooltip import add_tooltip

try:
    from reportlab.pdfgen import canvas
except ImportError:
    canvas = None

class TkinterDnD_CTkToplevel(ctk.CTkToplevel, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PDFToolsWindow(TkinterDnD_CTkToplevel):
    """
    PDFToolsWindow provides a separate UI containing utilities to manipulate PDF files.
    Features:
      - Merge PDFs: Combine multiple PDFs into one file.
      - Split PDF: Extract all single pages or specific page ranges.
      - Bates Numbering: Stamp sequential numbering onto multiple PDF files.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("PDF Tools (Splitter & Merger)")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        
        # UI Structure
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("Merge PDFs")
        self.tabview.add("Split PDF")
        self.tabview.add("Bates Numbering")
        
        # --- TAB 1: MERGE PDFs ---
        self.merge_tab = self.tabview.tab("Merge PDFs")
        self.merge_files = [] # list of paths
        
        # Toolbar
        merge_tb = ctk.CTkFrame(self.merge_tab, fg_color="transparent")
        merge_tb.pack(fill="x", pady=5)
        
        btn_add = ctk.CTkButton(merge_tb, text="Add PDFs", command=self.add_merge_files)
        btn_add.pack(side="left", padx=5)
        add_tooltip(btn_add, "Add PDF files to combine.")
        
        btn_clr = ctk.CTkButton(merge_tb, text="Clear", command=self.clear_merge_files, fg_color="#D32F2F", hover_color="#B71C1C")
        btn_clr.pack(side="left", padx=5)
        add_tooltip(btn_clr, "Clear the merge list.")
        
        btn_merge = ctk.CTkButton(merge_tb, text="Merge & Save", command=self.do_merge, fg_color="#388E3C", hover_color="#2E7D32")
        btn_merge.pack(side="right", padx=5)
        add_tooltip(btn_merge, "Combine all listed PDFs into a single file.")
        
        self.merge_listbox = ctk.CTkTextbox(self.merge_tab, state="disabled")
        self.merge_listbox.pack(fill="both", expand=True, pady=5)
        
        # Using master.tk because DnDWrapper expects master.tk or self.tk
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop_merge)
        
        # --- TAB 2: SPLIT PDF ---
        self.split_tab = self.tabview.tab("Split PDF")
        
        split_frame = ctk.CTkFrame(self.split_tab, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.split_target_var = ctk.StringVar()
        target_frame = ctk.CTkFrame(split_frame, fg_color="transparent")
        target_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(target_frame, text="Target PDF:").pack(side="left", padx=5)
        ctk.CTkEntry(target_frame, textvariable=self.split_target_var, state="disabled").pack(side="left", fill="x", expand=True, padx=5)
        btn_brws = ctk.CTkButton(target_frame, text="Browse", width=80, command=self.browse_split_target)
        btn_brws.pack(side="left", padx=5)
        add_tooltip(btn_brws, "Select a PDF file to extract pages from.")
        
        self.split_mode_var = ctk.StringVar(value="single")
        ctk.CTkRadioButton(split_frame, text="Split into Single Pages (Extract all pages to a folder)", variable=self.split_mode_var, value="single").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(split_frame, text="Extract Specific Pages (e.g. 1-5, 8)", variable=self.split_mode_var, value="extract").pack(anchor="w", pady=5)
        
        self.extract_range_entry = ctk.CTkEntry(split_frame, placeholder_text="e.g. 1-3, 5")
        self.extract_range_entry.pack(fill="x", padx=(30, 0), pady=5)
        
        btn_split = ctk.CTkButton(split_frame, text="Split & Save", command=self.do_split, fg_color="#F57C00", hover_color="#E65100")
        btn_split.pack(pady=30)
        add_tooltip(btn_split, "Execute the split/extraction process based on the selected mode.")
        
        # --- TAB 3: BATES NUMBERING ---
        self.bates_tab = self.tabview.tab("Bates Numbering")
        self.bates_files = []
        
        bates_tb = ctk.CTkFrame(self.bates_tab, fg_color="transparent")
        bates_tb.pack(fill="x", pady=5)
        
        btn_add_b = ctk.CTkButton(bates_tb, text="Add PDFs", command=self.add_bates_files, width=100)
        btn_add_b.pack(side="left", padx=5)
        add_tooltip(btn_add_b, "Add multiple PDFs to be stamped.")
        
        btn_clr_b = ctk.CTkButton(bates_tb, text="Clear", command=self.clear_bates_files, fg_color="#D32F2F", hover_color="#B71C1C", width=80)
        btn_clr_b.pack(side="left", padx=5)
        add_tooltip(btn_clr_b, "Clear the Bates Numbering queue.")
        
        btn_proc = ctk.CTkButton(bates_tb, text="Process & Save", command=self.do_bates, fg_color="#00695C", hover_color="#004D40")
        btn_proc.pack(side="right", padx=5)
        add_tooltip(btn_proc, "Apply Bates numbering to all pages across the queued PDFs.")
        
        self.bates_listbox = ctk.CTkTextbox(self.bates_tab, state="disabled", height=150)
        self.bates_listbox.pack(fill="x", pady=5)
        self.dnd_bind('<<Drop>>', self.on_drop_bates)
        
        # Settings Frame
        bates_settings = ctk.CTkFrame(self.bates_tab, fg_color="transparent")
        bates_settings.pack(fill="both", expand=True, pady=10)
        
        row1 = ctk.CTkFrame(bates_settings, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        ctk.CTkLabel(row1, text="Prefix:", width=60, anchor="e").pack(side="left", padx=5)
        self.bates_prefix_var = ctk.StringVar(value="DOC-")
        ctk.CTkEntry(row1, textvariable=self.bates_prefix_var, width=100).pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Start Number:", width=80, anchor="e").pack(side="left", padx=5)
        self.bates_start_var = ctk.StringVar(value="1")
        ctk.CTkEntry(row1, textvariable=self.bates_start_var, width=60).pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Padding (Zeros):", width=100, anchor="e").pack(side="left", padx=5)
        self.bates_pad_var = ctk.StringVar(value="5")
        ctk.CTkEntry(row1, textvariable=self.bates_pad_var, width=50).pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(bates_settings, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        ctk.CTkLabel(row2, text="Suffix:", width=60, anchor="e").pack(side="left", padx=5)
        self.bates_suffix_var = ctk.StringVar(value="")
        ctk.CTkEntry(row2, textvariable=self.bates_suffix_var, width=100).pack(side="left", padx=5)
        
        ctk.CTkLabel(row2, text="Position:", width=80, anchor="e").pack(side="left", padx=5)
        self.bates_pos_var = ctk.StringVar(value="Bottom-Right")
        ctk.CTkOptionMenu(row2, values=["Bottom-Right", "Bottom-Center", "Top-Right"], variable=self.bates_pos_var, width=120).pack(side="left", padx=5)
        
    def add_merge_files(self):
        """
        Opens a file dialog to allow the user to select multiple PDFs to append to the merge list.
        """
        files = filedialog.askopenfilenames(title="Select PDF files", filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*")))
        if files:
            self.merge_files.extend(files)
            self._update_merge_listbox()
            
    def on_drop_merge(self, event):
        """
        Handles Drag-and-Drop events on the merge listbox to add dropped PDFs.
        """
        files = self.master.tk.splitlist(event.data)
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self.merge_files.extend(pdf_files)
            self._update_merge_listbox()
            
    def clear_merge_files(self):
        """
        Empties the current list of PDF files scheduled for merging.
        """
        self.merge_files.clear()
        self._update_merge_listbox()
        
    def _update_merge_listbox(self):
        """
        Refreshes the display of the merge listbox to reflect current selected files.
        """
        self.merge_listbox.configure(state="normal")
        self.merge_listbox.delete("1.0", "end")
        for i, f in enumerate(self.merge_files):
            self.merge_listbox.insert("end", f"{i+1}. {os.path.basename(f)}\n")
        self.merge_listbox.configure(state="disabled")
        
    def do_merge(self):
        """
        Executes the PDF merging process.
        Combines all files in the `merge_files` list sequentially and prompts for a save location.
        """
        if len(self.merge_files) < 2:
            messagebox.showwarning("Warning", "Please add at least 2 PDF files to merge.")
            return
            
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="Save Merged PDF")
        if save_path:
            try:
                merger = PdfWriter()
                for pdf in self.merge_files:
                    merger.append(pdf)
                with open(save_path, "wb") as f_out:
                    merger.write(f_out)
                messagebox.showinfo("Success", f"Merged PDF saved to:\n{save_path}")
            except Exception as e:
                import traceback
                messagebox.showerror("Error", f"Failed to merge:\n{str(e)}\n{traceback.format_exc()}")
                
    def browse_split_target(self):
        """
        Opens a file dialog to select the single source PDF that needs to be split or extracted.
        """
        f = filedialog.askopenfilename(title="Select PDF to split", filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*")))
        if f:
            self.split_target_var.set(f)
            
    def do_split(self):
        """
        Executes the PDF splitting or extraction logic.
        Modes:
          - single: Extracts every page into a standalone PDF inside a selected directory.
          - extract: Uses master's parsing logic to extract specific ranges into one new PDF.
        """
        target = self.split_target_var.get()
        if not target or not os.path.exists(target):
            messagebox.showwarning("Warning", "Please select a valid PDF file to split.")
            return
            
        mode = self.split_mode_var.get()
        try:
            reader = PdfReader(target)
            total_pages = len(reader.pages)
            
            if mode == "single":
                save_dir = filedialog.askdirectory(title="Select Folder to save Single Pages")
                if not save_dir: return
                
                base_name = os.path.splitext(os.path.basename(target))[0]
                for i in range(total_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    out_path = os.path.join(save_dir, f"{base_name}_page_{i+1}.pdf")
                    with open(out_path, "wb") as f_out:
                        writer.write(f_out)
                messagebox.showinfo("Success", f"Successfully split {total_pages} pages into folder:\n{save_dir}")
                
            elif mode == "extract":
                range_str = self.extract_range_entry.get()
                if not range_str.strip():
                    messagebox.showwarning("Warning", "Please specify a page range (e.g. 1-5).")
                    return
                
                # Use the master's parser
                if hasattr(self.master, "parse_page_range"):
                    pages_to_extract = sorted(list(self.master.parse_page_range(range_str, total_pages)))
                else:
                    messagebox.showerror("Error", "Page parser not found.")
                    return
                
                if not pages_to_extract:
                    messagebox.showwarning("Warning", "Invalid page range or no pages found.")
                    return
                    
                save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="Save Extracted PDF")
                if save_path:
                    writer = PdfWriter()
                    for p in pages_to_extract:
                        writer.add_page(reader.pages[p])
                    with open(save_path, "wb") as f_out:
                        writer.write(f_out)
                    messagebox.showinfo("Success", f"Successfully extracted {len(pages_to_extract)} pages into:\n{save_path}")
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Failed to split PDF:\n{str(e)}\n{traceback.format_exc()}")

    def add_bates_files(self):
        """
        Opens a file dialog for the user to add PDF files to the Bates Numbering queue.
        """
        files = filedialog.askopenfilenames(title="Select PDF files", filetypes=(("PDF Files", "*.pdf"), ("All Files", "*.*")))
        if files:
            self.bates_files.extend(files)
            self._update_bates_listbox()
            
    def on_drop_bates(self, event):
        """
        Handles Drag-and-Drop events for files. Automatically routes the dropped files
        to either the Bates Numbering list or Merge list depending on the active tab.
        """
        files = self.master.tk.splitlist(event.data)
        pdf_files = []
        for f in files:
            if os.path.isdir(f):
                for root, _, filenames in os.walk(f):
                    for name in filenames:
                        if name.lower().endswith(".pdf"):
                            pdf_files.append(os.path.join(root, name))
            elif f.lower().endswith(".pdf"):
                pdf_files.append(f)
                
        if pdf_files:
            # Check which tab is active before assigning
            current_tab = self.tabview.get()
            if current_tab == "Bates Numbering":
                self.bates_files.extend(pdf_files)
                self._update_bates_listbox()
            elif current_tab == "Merge PDFs":
                self.merge_files.extend(pdf_files)
                self._update_merge_listbox()

    def clear_bates_files(self):
        """
        Empties the Bates Numbering file queue.
        """
        self.bates_files.clear()
        self._update_bates_listbox()
        
    def _update_bates_listbox(self):
        """
        Refreshes the UI listbox displaying the queue of files for Bates Numbering.
        """
        self.bates_listbox.configure(state="normal")
        self.bates_listbox.delete("1.0", "end")
        for i, f in enumerate(self.bates_files):
            self.bates_listbox.insert("end", f"{i+1}. {os.path.basename(f)}\n")
        self.bates_listbox.configure(state="disabled")
        
    def do_bates(self):
        """
        Executes the Bates Numbering process.
        Iterates over all queued PDFs and their pages, using ReportLab to generate a text overlay
        containing the formatted sequential number, and merges it onto the original page using PyPDF.
        Saves modified files with a '-Bates.pdf' suffix in the user-selected output directory.
        """
        if canvas is None:
            messagebox.showerror("Dependency Error", "ReportLab is not installed. Bates numbering cannot proceed.")
            return
            
        if not self.bates_files:
            messagebox.showwarning("Warning", "Please add at least 1 PDF file to process.")
            return
            
        save_dir = filedialog.askdirectory(title="Select Folder to save Bates Numbered PDFs")
        if not save_dir: return
        
        prefix = self.bates_prefix_var.get()
        suffix = self.bates_suffix_var.get()
        pos = self.bates_pos_var.get()
        
        try:
            start_num = int(self.bates_start_var.get())
            pad = int(self.bates_pad_var.get())
        except ValueError:
            messagebox.showerror("Error", "Start Number and Padding must be integers.")
            return
            
        current_num = start_num
        processed_count = 0
        
        try:
            for filepath in self.bates_files:
                reader = PdfReader(filepath)
                writer = PdfWriter()
                total_pages = len(reader.pages)
                
                for i in range(total_pages):
                    page = reader.pages[i]
                    
                    # Generate the bates string
                    num_str = str(current_num).zfill(pad)
                    bates_text = f"{prefix}{num_str}{suffix}"
                    
                    # Get page size to calculate coordinates
                    mbox = page.mediabox
                    width = float(mbox.width)
                    height = float(mbox.height)
                    
                    # Generate an overlay PDF using reportlab
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(width, height))
                    can.setFont("Helvetica-Bold", 12)
                    can.setFillColorRGB(0, 0, 0) # Black
                    
                    # Calculate position
                    x = width - 70
                    y = 20
                    if pos == "Bottom-Right":
                        can.drawRightString(width - 20, 20, bates_text)
                    elif pos == "Bottom-Center":
                        can.drawCentredString(width / 2, 20, bates_text)
                    elif pos == "Top-Right":
                        can.drawRightString(width - 20, height - 30, bates_text)
                        
                    can.save()
                    packet.seek(0)
                    
                    overlay_pdf = PdfReader(packet)
                    overlay_page = overlay_pdf.pages[0]
                    
                    page.merge_page(overlay_page)
                    writer.add_page(page)
                    
                    current_num += 1
                
                # Save the file
                base_name = os.path.basename(filepath)
                out_path = os.path.join(save_dir, f"{os.path.splitext(base_name)[0]}-Bates.pdf")
                with open(out_path, "wb") as f_out:
                    writer.write(f_out)
                processed_count += 1
                
            messagebox.showinfo("Success", f"Bates numbering applied to {processed_count} files.\nSaved to:\n{save_dir}")
            self.bates_files.clear()
            self._update_bates_listbox()
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Failed during Bates Numbering:\n{str(e)}\n{traceback.format_exc()}")
