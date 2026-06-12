import sys
import threading
import time

def run_test():
    try:
        from app import BatchPDFPrinterApp
        app = BatchPDFPrinterApp()
        
        # Open the PDF Tools window automatically
        app.after(1000, lambda: app.open_pdf_tools())
        # Close the app automatically after 3 seconds
        app.after(3000, lambda: app.destroy())
        
        app.mainloop()
        print("TEST SUCCESS: App opened and PDFToolsWindow opened without crashing.")
    except Exception as e:
        print(f"TEST FAILED: {e}")

if __name__ == "__main__":
    run_test()
