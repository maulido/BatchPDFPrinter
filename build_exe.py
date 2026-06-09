import os
import PyInstaller.__main__
import customtkinter
import tkinterdnd2
import shutil

# Dapatkan lokasi instalasi pustaka
ctk_dir = os.path.dirname(customtkinter.__file__)
tkdnd_dir = os.path.dirname(tkinterdnd2.__file__)

# Konfigurasi args PyInstaller
args = [
    'app.py',
    '--name=BatchPDFPrinter', # Nama file hasil .exe
    '--windowed',             # Hilangkan layar hitam CMD di belakang
    '--noconfirm',            # Timpa file yang sudah ada
    '--clean',                # Bersihkan cache sebelum build
    f'--add-data={ctk_dir};customtkinter/', # Masukkan aset UI
    f'--add-data={tkdnd_dir};tkinterdnd2/', # Masukkan library Drag n Drop
    '--add-data=bin/SumatraPDF.exe;bin/',   # Masukkan mesin printer
    '--add-data=icon.ico;.',                # Bundle icon untuk app.py runtime
    '--icon=icon.ico',                      # Set logo untuk file .exe
]

print("Starting Build Process with PyInstaller...")
print("Includes:")
print(" - CustomTkinter:", ctk_dir)
print(" - TkinterDnD2:", tkdnd_dir)
print(" - SumatraPDF: bin/SumatraPDF.exe")
print("="*40)

# Jalankan PyInstaller
PyInstaller.__main__.run(args)

print("="*40)
print("Build Complete! The .exe is located in the 'dist/BatchPDFPrinter' folder.")
