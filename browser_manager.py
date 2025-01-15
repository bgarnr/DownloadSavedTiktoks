"""
Manages browser setup and configuration for TikTok video downloading.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import time
import requests
from dotenv import load_dotenv
import sys
import setup_chromedriver
from pyairtable import Table
import threading

class BrowserManager:
    """Manages Chrome browser setup and configuration."""
    
    def __init__(self, profile_name=None):
        """Initialize browser manager with optional profile name."""
        self.profile_name = profile_name
        self.driver = None
        self.download_dir = os.getenv("DOWNLOAD_DIR")
        print(f"Using download directory: {self.download_dir}")
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with the specified profile."""
        print("\nSetting up Chrome driver...")
        
        try:
            # Get Chrome path
            chrome_path = setup_chromedriver.get_chrome_path()
            print(f"Using Chrome from: {chrome_path}")
            
            # Get user data directory
            user_data_dir = setup_chromedriver.get_user_data_dir()
            print(f"Using Chrome profile from: {user_data_dir}")
            
            # Setup Chrome options
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={user_data_dir}")
            if self.profile_name:
                options.add_argument(f"--profile-directory={self.profile_name}")
                print(f"Using profile: {self.profile_name}")
            
            print("Creating Chrome instance...")
            self.driver = uc.Chrome(options=options)
            print("Chrome driver setup successful!")
            
            return self.driver
            
        except Exception as e:
            print(f"\nError setting up Chrome driver: {str(e)}")
            print("\nPlease make sure:")
            print("1. Close ALL Chrome windows before running this script")
            print("2. Your antivirus is not blocking ChromeDriver")
            print("3. You have a stable internet connection")
            print("4. Chrome is installed in the default location")
            if self.driver:
                self.driver.quit()
            raise
    
    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing driver: {str(e)}")
            finally:
                self.driver = None
