import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import requests
from dotenv import load_dotenv
import sys

class TikTokDownloader:
    def __init__(self):
        load_dotenv()
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        try:
            print("Setting up Chrome driver...")
            
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            
            # Set Chrome binary location explicitly
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                print(f"Using Chrome from: {chrome_path}")
                options.binary_location = chrome_path
            else:
                print("Chrome not found in default location!")
                print("Please make sure Chrome is installed in the default location.")
                raise Exception("Chrome not found")
            
            # Use your default Chrome profile
            user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
            user_data_dir = os.path.normpath(user_data_dir)  # Normalize path
            print(f"Using Chrome profile from: {user_data_dir}")
            
            # Add the user data directory option
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument('--profile-directory=Default')
            
            # Create new Chrome instance
            print("Creating Chrome instance...")
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True
            )
            self.driver.implicitly_wait(10)
            print("Chrome driver setup successful!")
            
        except Exception as e:
            print("\nError setting up Chrome driver:")
            print(f"Error details: {str(e)}")
            print("\nPlease make sure:")
            print("1. Close ALL Chrome windows before running this script")
            print("2. Your antivirus is not blocking ChromeDriver")
            print("3. You have a stable internet connection")
            print("4. Chrome is installed in the default location")
            if self.driver:
                self.driver.quit()
            raise

    def add_download_buttons(self):
        """Add download buttons to each video in the favorites list"""
        print("Waiting for videos to load...")
        # Wait for at least one video container to appear
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="DivContainer-StyledDivContainerV2"]'))
            )
        except Exception as e:
            print(f"Error waiting for videos: {str(e)}")
            return

        # Inject our custom CSS for the download buttons
        css = """
        .download-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            z-index: 9999;
            font-family: Arial, sans-serif;
            transition: background 0.3s;
        }
        .download-btn:hover {
            background: rgba(0, 0, 0, 0.9);
        }
        .download-btn.downloaded {
            background: rgba(40, 167, 69, 0.7);
        }
        """
        print("Adding download button styles...")
        self.driver.execute_script(f"var style = document.createElement('style'); style.textContent = `{css}`; document.head.appendChild(style);")
        
        # Add download buttons to each video
        js = """
        function addDownloadButtons() {
            console.log('Looking for video containers...');
            const videos = document.querySelectorAll('div[class*="DivContainer-StyledDivContainerV2"]');
            console.log('Found ' + videos.length + ' video containers');
            
            videos.forEach((video, index) => {
                if (!video.querySelector('.download-btn')) {
                    console.log('Adding button to video ' + index);
                    const btn = document.createElement('button');
                    btn.className = 'download-btn';
                    btn.textContent = 'Download';
                    btn.setAttribute('data-video-index', index);
                    
                    // Find the video link
                    const videoLink = video.querySelector('a');
                    if (videoLink) {
                        console.log('Found video link: ' + videoLink.href);
                        btn.setAttribute('data-video-url', videoLink.href);
                    }
                    
                    video.style.position = 'relative';
                    video.appendChild(btn);
                }
            });
        }
        
        // Initial call
        addDownloadButtons();
        
        // Setup observer to watch for new videos
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    addDownloadButtons();
                }
            });
        });

        // Start observing the video container for changes
        const container = document.querySelector('div[class*="DivItemContainer"]') || document.body;
        observer.observe(container, { 
            childList: true, 
            subtree: true 
        });
        
        // Also run periodically to catch any missed videos
        setInterval(addDownloadButtons, 2000);
        
        console.log('Download button setup complete');
        """
        print("Adding download buttons to videos...")
        self.driver.execute_script(js)

    def setup_download_handler(self):
        """Setup the click handler for download buttons"""
        self.driver.execute_script("""
        window.downloadVideo = function(videoElement) {
            const btn = videoElement.querySelector('.download-btn');
            if (btn && !btn.classList.contains('downloaded')) {
                const videoUrl = btn.getAttribute('data-video-url');
                if (videoUrl) {
                    btn.textContent = 'Opening...';
                    // Open in new tab
                    window.open(videoUrl, '_blank');
                    btn.classList.add('downloaded');
                    btn.textContent = 'Downloaded';
                }
            }
        }
        
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('download-btn')) {
                const videoElement = e.target.closest('div[class*="DivContainer-StyledDivContainerV2"]');
                if (videoElement) {
                    downloadVideo(videoElement);
                }
            }
        });
        """)

    def browse_favorites(self):
        try:
            # Navigate to your profile page first
            print("\nNavigating to your profile page...")
            self.driver.get('https://www.tiktok.com/@dysonsmear')
            time.sleep(3)
            
            # Wait for user to log in
            print("\nPlease log in using the QR code...")
            print("Waiting for login to complete...")
            
            # Wait for the favorites tab to appear (indicates successful login)
            max_wait = 120  # Wait up to 2 minutes for login
            start_time = time.time()
            favorites_found = False
            
            while time.time() - start_time < max_wait:
                try:
                    # Try to find the favorites element
                    favorites = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Favorites')]")
                    if favorites.is_displayed():
                        favorites_found = True
                        print("\nLogin successful!")
                        break
                except:
                    time.sleep(2)  # Check every 2 seconds
                    
            if not favorites_found:
                print("\nLogin timeout. Please run the script again and try to log in faster.")
                return
                
            # Give a moment for the page to settle
            time.sleep(3)
            
            # Click on Favorites tab
            print("\nNavigating to favorites...")
            try:
                favorites.click()
                print("Clicked favorites tab!")
            except Exception as e:
                print(f"Error clicking favorites: {str(e)}")
                return
                
            time.sleep(5)
            
            # Add download buttons and setup handlers
            print("\nSetting up interactive download buttons...")
            self.add_download_buttons()
            self.setup_download_handler()
            
            print("\nReady! Click the download buttons on the videos you want to save.")
            print("Close the browser window when you're done.")
            
            # Keep the script running until the browser is closed
            try:
                while True:
                    self.driver.current_url  # Check if browser is still open
                    time.sleep(1)
            except:
                print("\nBrowser closed. Exiting...")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

if __name__ == "__main__":
    print("TikTok Saved Videos Downloader")
    print("=============================")
    print("This script will help you download your saved TikTok videos.")
    print("\nIMPORTANT: Please make sure ALL Chrome windows are closed!")
    print("Waiting 5 seconds before starting...")
    time.sleep(5)
    
    downloader = TikTokDownloader()
    try:
        print("\nStarting interactive mode...")
        downloader.browse_favorites()
        print("\nDownload complete! Check the 'downloads' folder for your videos.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        if downloader.driver:
            downloader.driver.quit()
    finally:
        print("\nScript finished. Thanks for using TikTok Saved Videos Downloader!")
