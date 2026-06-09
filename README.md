# Batch PDF Printer

Batch PDF Printer is a powerful, Python-based desktop application designed to streamline the process of printing multiple PDF documents. Inspired by enterprise solutions like Print Conductor, this tool offers a modern, dark-mode ready User Interface built with `customtkinter`.

## 📥 Download (Ready to Use)

[**⬇️ Download Batch PDF Printer (Latest Version)**](https://github.com/maulido/BatchPDFPrinter/releases/latest)

Tersedia 2 pilihan file di halaman download tersebut:
- **Versi Installer (`BatchPDFPrinter-Setup.exe`)** - *Rekomendasi!* Menginstal aplikasi di komputer Anda dan membuat *shortcut* Desktop.
- **Versi Portable (`BatchPDFPrinter-Portable.exe`)** - *Praktis!* Hanya 1 file `.exe`, tanpa perlu instalasi, langsung jalan. Cocok dibawa di Flashdisk.

## 🌟 Key Features

* **File Import via Drag & Drop**: Easily drag multiple PDF files or entire folders into the application.
* **Drag & Drop Reordering**: Grab the `☰` grip handle next to any document to seamlessly drag and drop files into your preferred printing order.
* **Dynamic PDF Watermarking**: Apply custom text watermarks to your documents on-the-fly. Adjust text, color, and opacity from the Settings menu, and preview the stamp before printing.
* **Table View with Auto-Page Count**: Displays a clean list of queued documents along with their exact page counts and modification dates.
* **Live Visual Print Preview**: A dynamic canvas in the Settings menu that visually demonstrates how your document will fit on the paper based on your orientation, dimensions, and scaling choices.
* **Single Print Job (Auto-Merge)**: Optionally merge hundreds of PDFs into a single continuous print job to prevent other users from interrupting your print queue on a shared network printer.
* **Pause & Resume**: Full control over your print queue. Pause the batch printing process at any time and resume when ready.
* **Detailed Print Logs**: Generates a success/failure report window after printing, with the option to export the log to a `.txt` file.
* **Granular Printer Settings**: Customize Copies, Paper Size (A4, A6, Custom, etc.), Orientation, Scaling, Color Mode, and Duplex Mode. All settings are automatically saved for your next session.

## 🛠️ Prerequisites

1. **Python 3.8+**
2. **SumatraPDF**: This application requires the portable version of `SumatraPDF.exe` to function. It must be placed inside a folder named `bin` in the root directory:
   ```
   BatchPDFPrinter/
   ├── app.py
   └── bin/
       └── SumatraPDF.exe
   ```

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/maulido/BatchPDFPrinter.git
   cd BatchPDFPrinter
   ```

2. Install the required Python dependencies:
   ```bash
   pip install customtkinter pypdf pywin32 tkinterdnd2 reportlab
   ```

## 🚀 Usage

To run the application locally from the source code:
```bash
python app.py
```

## 🏗️ Building to .EXE (Windows)

To compile the application into a single, standalone executable that can be shared without requiring Python to be installed:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. We have provided an automated build script. Simply run:
   ```bash
   python build_exe.py
   ```
   *(This script will automatically detect your python environment, include all necessary libraries like `reportlab` and `customtkinter`, and generate the `.exe` file).*

3. The final compiled standalone application will be located at `dist/BatchPDFPrinter-Portable.exe`.

## 📝 License

This project is created for personal/commercial productivity enhancement.
