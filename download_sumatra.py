import os
import requests
import zipfile

def download_sumatra():
    print("Downloading SumatraPDF from sumatrapdfreader.org...")
    url = "https://www.sumatrapdfreader.org/dl/rel/3.6.1/SumatraPDF-3.6.1-64.zip"
    zip_path = "SumatraPDF.zip"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    with open(zip_path, 'wb') as f:
        f.write(response.content)
        
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("bin")
    
    # Clean up
    os.remove(zip_path)
    
    extracted_files = os.listdir("bin")
    for file in extracted_files:
        if file.lower().startswith("sumatrapdf") and file.lower().endswith(".exe"):
            os.rename(os.path.join("bin", file), os.path.join("bin", "SumatraPDF.exe"))
            print("Renamed to SumatraPDF.exe")
            break
            
    print("Done!")

if __name__ == "__main__":
    if not os.path.exists("bin"):
        os.makedirs("bin")
    download_sumatra()
