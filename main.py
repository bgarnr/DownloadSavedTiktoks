"""
Main entry point for the TikTok video downloader application.
"""

import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from browser_manager import BrowserManager
from airtable_manager import AirtableManager
from tiktok_scraper import TikTokScraper
import time

def main():
    """Main function to run the TikTok downloader"""
    print("TikTok Saved Videos Downloader")
    print("=============================")
    print("This script will help you download your saved TikTok videos.\n")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Get profile from .env file, or use default
        profile_name = os.getenv('CHROME_PROFILE')
        if profile_name:
            print(f"Using Chrome profile: {profile_name}")
        else:
            print("Using default Chrome profile")
        
        print("\nIMPORTANT: Please make sure ALL Chrome windows are closed!")
        print("Waiting 5 seconds before starting...")
        time.sleep(5)
        
        # Initialize components
        airtable = AirtableManager()
        browser = BrowserManager(profile_name)
        scraper = TikTokScraper(browser.driver, airtable)
        scraper.browse_favorites()
        
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        print("\nScript finished. Thanks for using TikTok Saved Videos Downloader!")

if __name__ == "__main__":
    main()
