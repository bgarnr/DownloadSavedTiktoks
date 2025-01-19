import os
import requests
import zipfile
import sys
from io import BytesIO
import winreg

def download_chromedriver():
    # Get the installed Chrome version from Windows registry
    chrome_version = get_chrome_version()
    if chrome_version is None:
        print("Could not detect Chrome version. Using default version.")
        version = "131.0.6778.264"
    else:
        version = f"{chrome_version}.0.0.0"

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

def get_chrome_version():
    """Get the installed Chrome version from Windows registry."""
    try:
        # Open the registry key for Chrome
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        major_version = version.split('.')[0]  # Get major version number
        return int(major_version)
    except Exception as e:
        print(f"Could not detect Chrome version: {e}")
        return None

def get_chrome_path():
    """Get Chrome executable path from registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        chrome_path, _ = winreg.QueryValueEx(key, None)
        return chrome_path
    except Exception as e:
        print(f"Could not find Chrome path: {e}")
        return None

def get_user_data_dir():
    """Get Chrome user data directory."""
    return os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')

if __name__ == "__main__":
    download_chromedriver()
