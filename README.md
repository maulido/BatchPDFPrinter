# Batch PDF Printer

Batch PDF Printer is a powerful, Python-based desktop application designed to streamline the process of printing multiple PDF documents. Inspired by enterprise solutions like Print Conductor, this tool offers a modern, dark-mode ready User Interface built with `customtkinter`.

## 📥 Download (Ready to Use)
Kini tersedia dalam 2 versi untuk kemudahan Anda:

*   [**⬇️ Download Versi Installer (BatchPDFPrinter-Setup.exe)**](https://github.com/maulido/BatchPDFPrinter/releases/latest) - *Rekomendasi!* Menginstal aplikasi di komputer Anda, membuat *shortcut* Desktop, dan memuat aplikasi dalam hitungan milidetik.
*   [**⬇️ Download Versi Portable (BatchPDFPrinter-Portable.exe)**](https://github.com/maulido/BatchPDFPrinter/releases/latest) - *Praktis!* Hanya 1 file `.exe`, tanpa perlu instalasi, langsung jalan. Cocok dibawa di Flashdisk.

*(Silakan kunjungi link di atas dan unduh file `.exe` yang Anda inginkan dari menu Releases).*

## 🌟 Key Features

* **Drag & Drop Interface**: Easily drag multiple PDF files or entire folders into the application.
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
   pip install customtkinter pypdf pywin32 tkinterdnd2
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
2. Run the build command (it will automatically bundle the UI libraries and `SumatraPDF.exe`):
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "C:/Users/Egogohub/AppData/Local/Programs/Python/Python311/Lib/site-packages/customtkinter;customtkinter/" --add-data "C:/Users/Egogohub/AppData/Local/Programs/Python/Python311/Lib/site-packages/tkinterdnd2;tkinterdnd2/" --add-data "bin/SumatraPDF.exe;bin/" app.py
   ```
   *(Note: Ensure the paths to `customtkinter` and `tkinterdnd2` match your actual Python installation path).*

3. The final `.exe` application will be located inside the `dist/app/` folder.

## 📝 License

This project is created for personal/commercial productivity enhancement.
