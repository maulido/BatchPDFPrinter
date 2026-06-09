# Batch PDF Printer

Batch PDF Printer is a powerful, Python-based desktop application designed to streamline the process of printing multiple PDF documents. Inspired by enterprise solutions like Print Conductor, this tool offers a modern, dark-mode ready User Interface built with `customtkinter`.

It utilizes `SumatraPDF` under the hood to perform ultra-fast, silent background printing without cluttering your screen with popup windows.

## 📥 Download (Ready to Use)
[**⬇️ Download BatchPDFPrinter (Windows .exe)**](https://github.com/maulido/BatchPDFPrinter/releases/latest)

*Simply download the latest `.zip` file from the Releases page, extract it, and run `BatchPDFPrinter.exe`. No installation or Python required!*

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
