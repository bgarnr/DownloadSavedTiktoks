"""
Handles TikTok-specific scraping operations.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from watchdog.observers import Observer
import os
import time
from file_handlers import DownloadHandler
import threading

class TikTokScraper:
    """Handles TikTok-specific scraping operations."""
    
    def __init__(self, driver, airtable_manager):
        """Initialize TikTok scraper with WebDriver and AirtableManager."""
        self.driver = driver
        self.airtable_manager = airtable_manager
        self.download_dir = os.getenv("DOWNLOAD_DIR")
        self.download_thread = None
        
    def extract_video_id(self, url):
        """Extract the video ID from a TikTok URL."""
        try:
            # Try to get video ID from URL
            if "/video/" in url:
                video_id = url.split("/video/")[1].split("?")[0]
                return video_id
            return None
        except Exception as e:
            print(f"Error extracting video ID: {str(e)}")
            return None
            
    def get_video_description(self):
        """Get the description of the current video."""
        try:
            # Wait for the content to load
            print("Waiting for content to load...")
            time.sleep(3)  # Give the page time to load
            
            # Try to find the description span
            print("Looking for description span...")
            desc_span = self.driver.find_element(By.CSS_SELECTOR, "span.css-j2a19r-SpanText")
            description = desc_span.text.strip()
            
            if description:
                print(f"Description found: {description[:50]}...")
                return description
            else:
                print("No description found in span")
                return None
                
        except Exception as e:
            print(f"Error getting description: {str(e)}")
            print("Page source around description:")
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                print(body.get_attribute('innerHTML')[:1000])
            except:
                print("Could not get page source")
            return None
            
    def get_uploader_info(self):
        """Get the uploader's information."""
        try:
            # Try to find uploader info
            uploader_element = self.driver.find_element(By.CSS_SELECTOR, "h3[data-e2e='browse-username']")
            return uploader_element.text.strip()
        except Exception as e:
            print(f"Error getting uploader info: {str(e)}")
            return None
            
    def click_download_button(self):
        """Click the download button for the current video."""
        try:
            # Find and click download button
            download_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-e2e='download-icon']")
            download_button.click()
            print("Clicked download button")
            return True
        except Exception as e:
            print(f"Error clicking download button: {str(e)}")
            return False
            
    def start_download_handler(self, video_id):
        """Start monitoring for downloaded video file."""
        try:
            # Create download handler
            handler = DownloadHandler(self.airtable_manager, video_id)
            observer = Observer()
            observer.schedule(handler, self.download_dir, recursive=False)
            observer.start()
            print(f"Started file monitoring in {self.download_dir}")
            
            return handler, observer
            
        except Exception as e:
            print(f"Error setting up download handler: {str(e)}")
            return None, None
            
    def check_for_downloads(self, handler, observer, timeout=30):
        """Check for downloaded files with timeout."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if handler.found_file:
                    print(f"Found downloaded file: {handler.found_file}")
                    return handler.found_file
                time.sleep(1)
                
            print(f"Timeout waiting for download after {timeout} seconds")
            return None
            
        finally:
            observer.stop()
            observer.join()
            
    def download_video(self, url):
        """Download a video from the given URL."""
        try:
            print(f"\nProcessing video URL: {url}")
            
            # Navigate to video page
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Get video information
            video_id = self.extract_video_id(url)
            if not video_id:
                print("Could not extract video ID")
                return False
                
            description = self.get_video_description()
            uploader = self.get_uploader_info()
            
            # Start monitoring for downloads
            handler, observer = self.start_download_handler(video_id)
            if not handler or not observer:
                return False
                
            # Click download button
            if not self.click_download_button():
                observer.stop()
                observer.join()
                return False
                
            # Wait for download
            downloaded_file = self.check_for_downloads(handler, observer)
            if not downloaded_file:
                print("Download failed or timed out")
                self.airtable_manager.create_record(video_id, description, uploader, status="Failed")
                return False
                
            # Create Airtable record
            self.airtable_manager.create_record(video_id, description, uploader, video_file=downloaded_file)
            return True
            
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            return False
            
    def browse_favorites(self):
        """Browse and interact with favorite videos."""
        try:
            # Navigate to your profile page first
            print("\nNavigating to your profile page...")
            tiktok_username = os.getenv("TIKTOK_USERNAME")
            if not tiktok_username:
                print("ERROR: TIKTOK_USERNAME not set in .env file!")
                return
                
            self.driver.get(f'https://www.tiktok.com/@{tiktok_username}')
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
            
        # Add button styles
        print("Adding download button styles...")
        self.driver.execute_script("""
            var style = document.createElement('style');
            style.innerHTML = `
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
            `;
            document.head.appendChild(style);
        """)
        
        # Add buttons to each video
        print("Adding download buttons to videos...")
        self.driver.execute_script("""
            // Find all video containers on the favorites page only
            const videoContainers = document.querySelectorAll('div[class*="DivContainer-StyledDivContainerV2"]');
            
            // Add button to each container
            videoContainers.forEach((container) => {
                // Create button if it doesn't exist
                if (!container.querySelector('.download-btn')) {
                    const btn = document.createElement('button');
                    btn.className = 'download-btn';
                    btn.textContent = 'Download';
                    btn.onclick = function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Get the video link before navigating
                        const videoLink = container.querySelector("a[href*='/video/']");
                        if (videoLink) {
                            window.lastOpenedUrl = videoLink.href;
                            // Open in new tab
                            window.open(videoLink.href, '_blank');
                        }
                    };
                    container.appendChild(btn);
                }
            });
        """)
        
    def setup_download_handler(self):
        """Start background thread to handle downloads"""
        def check_for_downloads():
            while True:
                try:
                    # Check if there's a new URL to process
                    url = self.driver.execute_script("const url = window.lastOpenedUrl; window.lastOpenedUrl = null; return url;")
                    if url:
                        print("\n" + "="*50)
                        print("DOWNLOAD PROCESS STARTED")
                        print("="*50)
                        print(f"Processing URL: {url}")
                        
                        # Extract video ID from URL
                        video_id = url.split('/')[-1].split('?')[0]
                        print(f"Video ID: {video_id}")
                        
                        try:
                            # Switch to the new tab
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            time.sleep(3)  # Wait for page load
                            
                            # Get video description if available
                            print("Attempting to get video description...")
                            try:
                                desc_span = self.driver.find_element(By.CSS_SELECTOR, "span.css-j2a19r-SpanText")
                                description = desc_span.text.strip()
                                print(f"Description found: {description[:50]}...")
                            except:
                                print("No description found")
                                description = None
                                
                            # Set up file monitoring before starting download
                            download_handler = DownloadHandler(self.airtable_manager, video_id)
                            observer = Observer()
                            observer.schedule(download_handler, self.download_dir, recursive=False)
                            observer.start()
                            
                            try:
                                # Wait for video element to be present
                                print("Waiting for video element...")
                                video = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                                )
                                print("Video element found!")
                                
                                # Create ActionChains instance
                                actions = ActionChains(self.driver)
                                
                                # Right click on the video element
                                print("Right clicking video...")
                                actions.context_click(video).perform()
                                time.sleep(1)  # Wait for context menu
                                
                                # Click the Download video option
                                print("Looking for Download option...")
                                menu_items = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.css-108oj9l-SpanItemText"))
                                )
                                
                                # Find the Download video option
                                download_option = None
                                for item in menu_items:
                                    if item.text.strip().lower() == "download video":
                                        download_option = item
                                        break
                                        
                                if download_option:
                                    print("Found Download option, clicking...")
                                    download_option.click()
                                    
                                    # Wait for file to be downloaded
                                    max_wait = 30  # Maximum seconds to wait
                                    start_time = time.time()
                                    
                                    while time.time() - start_time < max_wait:
                                        if download_handler.found_file:
                                            print(f"\nDownload completed: {download_handler.found_file}")
                                            
                                            # Create Airtable record
                                            self.airtable_manager.create_record(
                                                video_id=video_id,
                                                description=description,
                                                uploader=None,  # We'll get this from the URL
                                                video_file=download_handler.found_file
                                            )
                                            break
                                            
                                        time.sleep(1)
                                        
                                    if not download_handler.found_file:
                                        print("\nDownload timeout")
                                        self.airtable_manager.create_record(
                                            video_id=video_id,
                                            status="Failed - Download timeout"
                                        )
                                else:
                                    print("Download option not found in context menu")
                                    raise Exception("Download video option not found")
                                    
                            except Exception as e:
                                print(f"\nError during download: {str(e)}")
                                self.airtable_manager.create_record(
                                    video_id=video_id,
                                    status=f"Failed - {str(e)}"
                                )
                                
                            finally:
                                observer.stop()
                                observer.join()
                                # Close the tab
                                self.driver.close()
                                # Switch back to main window
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                
                        except Exception as e:
                            print(f"\nError setting up download: {str(e)}")
                            self.airtable_manager.create_record(
                                video_id=video_id,
                                status=f"Failed - {str(e)}"
                            )
                            
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    print(f"Error in download handler: {str(e)}")
                    try:
                        self.driver.current_url  # Check if browser still open
                    except:
                        break
                        
        # Start the background thread
        self.download_thread = threading.Thread(target=check_for_downloads, daemon=True)
        self.download_thread.start()