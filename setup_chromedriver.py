import os
import requests
import zipfile
import sys
from io import BytesIO

def download_chromedriver():
    # Chrome version 131.0.6778.265 needs ChromeDriver 131.0.6778.264
    version = "131.0.6778.264"
    print(f"Downloading ChromeDriver version {version}...")
    
    # URL for the ChromeDriver download
    url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/win64/chromedriver-win64.zip"
    
    try:
        # Download the zip file
        response = requests.get(url)
        response.raise_for_status()
        
        # Create chromedriver directory if it doesn't exist
        if not os.path.exists('chromedriver'):
            os.makedirs('chromedriver')
        
        # Extract the zip file
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extractall('chromedriver')
        
        # The chromedriver.exe will be in a subdirectory, let's move it up
        chromedriver_dir = os.path.join('chromedriver', 'chromedriver-win64')
        if os.path.exists(chromedriver_dir):
            os.rename(
                os.path.join(chromedriver_dir, 'chromedriver.exe'),
                os.path.join('chromedriver', 'chromedriver.exe')
            )
        
        print("ChromeDriver downloaded and extracted successfully!")
        print(f"ChromeDriver location: {os.path.abspath(os.path.join('chromedriver', 'chromedriver.exe'))}")
        
    except Exception as e:
        print(f"Error downloading ChromeDriver: {str(e)}")
        sys.exit(1)

def get_chrome_path():
    """Get the path to Chrome executable"""
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        raise Exception("Chrome not found in default location!")
    return chrome_path

def get_user_data_dir():
    """Get the Chrome user data directory"""
    user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
    return os.path.normpath(user_data_dir)

if __name__ == "__main__":
    download_chromedriver()
