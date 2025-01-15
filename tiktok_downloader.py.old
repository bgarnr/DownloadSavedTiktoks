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
import setup_chromedriver
from selenium.webdriver.common.keys import Keys
from pyairtable import Table
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import mimetypes
import http.server
import socketserver
import threading
import requests
from urllib.parse import quote
from drive_manager import DriveManager

class DownloadHandler(FileSystemEventHandler):
    def __init__(self, airtable_manager, video_id):
        self.airtable_manager = airtable_manager
        self.video_id = video_id
        self.found_file = None
        print(f"\nFile monitoring initialized for video {video_id}")
        
    def on_created(self, event):
        print(f"\nFile created event detected!")
        print(f"Path: {event.src_path}")
        print(f"Is directory: {event.is_directory}")
        if not event.is_directory:
            print(f"File extension: {os.path.splitext(event.src_path)[1]}")
            
    def on_moved(self, event):
        print(f"\nFile moved/renamed event detected!")
        print(f"Source path: {event.src_path}")
        print(f"Destination path: {event.dest_path}")
        
        if not event.is_directory and event.dest_path.endswith('.mp4'):
            print(f"\nNew video file detected: {event.dest_path}")
            self.found_file = event.dest_path
            # Wait a moment for the file to be fully written
            time.sleep(2)

class SimpleHTTPRequestHandlerWithCORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class AirtableManager:
    def __init__(self):
        """Initialize Airtable connection"""
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.token = os.getenv("AIRTABLE_ACCESS_TOKEN_VALUE")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME")
        self.http_server = None
        self.server_thread = None
        self.drive_manager = DriveManager()
        
        print(f"\nInitializing Airtable connection...")
        print(f"Base ID: {self.base_id}")
        print(f"Token available: {'Yes' if self.token else 'No'}")
        print(f"Table name: {self.table_name}")
        
        if not self.base_id or not self.token:
            print("ERROR: Missing Airtable credentials in .env file!")
            return
            
        try:
            self.table = Table(self.token, self.base_id, self.table_name)
            print("Successfully connected to Airtable!")
        except Exception as e:
            print(f"Error connecting to Airtable: {str(e)}")

    def start_temp_server(self, file_path):
        """Start a temporary HTTP server to serve the file"""
        # Find an available port
        with socketserver.TCPServer(("", 0), None) as s:
            port = s.server_address[1]

        # Set the server's directory to the file's directory
        os.chdir(os.path.dirname(os.path.abspath(file_path)))
        
        # Create and start the server
        handler = SimpleHTTPRequestHandlerWithCORS
        self.http_server = socketserver.TCPServer(("", port), handler)
        
        self.server_thread = threading.Thread(target=self.http_server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        return f"http://localhost:{port}/{quote(os.path.basename(file_path))}"

    def stop_temp_server(self):
        """Stop the temporary HTTP server"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            self.server_thread.join()
            self.http_server = None
            self.server_thread = None

    def create_record(self, video_id, description, uploader, status="Downloaded", video_file=None):
        """Create a record in Airtable for a downloaded video"""
        try:
            print(f"\nCreating Airtable record...")
            print(f"Video ID: {video_id}")
            print(f"Uploader: {uploader}")
            print(f"Description: {description if description else 'No description available'}")
            print(f"Status: {status}")
            
            record_data = {
                "Video Id": video_id,
                "Description": description if description else "No description available",
                "Uploader": uploader,
                "Status": status
            }
            
            # If we have a video file, prepare it for upload
            if video_file and os.path.exists(video_file):
                print(f"Uploading video file: {video_file}")
                file_size = os.path.getsize(video_file)
                print(f"File size: {file_size} bytes")
                
                if file_size < 1000:  # Less than 1KB
                    raise Exception(f"File seems too small ({file_size} bytes), might be corrupted or not fully downloaded")
                
                try:
                    # Upload to Google Drive first
                    print("Uploading to Google Drive...")
                    shareable_link = self.drive_manager.upload_file(video_file)
                    
                    if shareable_link:
                        print(f"File uploaded to Drive: {shareable_link}")
                        record_data["Video File"] = [{"url": shareable_link}]
                    else:
                        print("Failed to upload to Google Drive")

                except Exception as e:
                    raise e
            
            # Create the record with all data
            record = self.table.create(record_data)
            print("Successfully created Airtable record with all data")
            return record
            
        except Exception as e:
            print(f"Error creating Airtable record: {str(e)}")
            print(f"Full error details: {repr(e)}")
            return None

    def update_record_with_file(self, record_id, video_file):
        """Update an existing record with a video file"""
        try:
            print(f"\nUpdating record with video file...")
            # Upload to Google Drive first
            print("Uploading to Google Drive...")
            shareable_link = self.drive_manager.upload_file(video_file)
            
            if shareable_link:
                print(f"File uploaded to Drive: {shareable_link}")
                self.table.update(record_id, {
                    "Video File": [{"url": shareable_link}]
                })
                print("Successfully updated record with video file")
                return True
            else:
                print("Failed to upload to Google Drive")
                return False
            
        except Exception as e:
            print(f"Error updating record with video file: {str(e)}")
            return False

class TikTokDownloader:
    def __init__(self, profile_name=None):
        """Initialize the TikTok downloader with optional profile name"""
        self.profile_name = profile_name
        self.driver = None
        self.airtable = AirtableManager()
        self.download_dir = os.getenv("DOWNLOAD_DIR")
        print(f"Using download directory: {self.download_dir}")
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with the specified profile"""
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
                    // Open in new tab and get the window handle
                    const newWindow = window.open(videoUrl, '_blank');
                    // Signal to Python that we've opened a new tab
                    window.lastOpenedUrl = videoUrl;
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
        
        # Start a background thread to handle downloads
        self.start_download_handler()
        
    def start_download_handler(self):
        """Start a background thread to handle automatic downloads"""
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
                        
                        # Extract video information
                        try:
                            video_id = url.split('/')[-1]
                            uploader = url.split('/@')[1].split('/')[0]
                            print(f"Extracted video ID: {video_id}")
                            print(f"Extracted uploader: {uploader}")
                        except Exception as e:
                            print(f"Error extracting video info: {str(e)}")
                        
                        # Get video description if available
                        print("Attempting to get video description...")
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
                            else:
                                print("No description found in span")
                                description = None
                                
                        except Exception as e:
                            print(f"Error getting description: {str(e)}")
                            print("Page source around description:")
                            try:
                                body = self.driver.find_element(By.TAG_NAME, "body")
                                print(body.get_attribute('innerHTML')[:1000])
                            except:
                                print("Could not get page source")
                            description = None
                        
                        print("\nStarting download process...")
                        # Switch to the new tab
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        try:
                            # Set up file monitoring before starting download
                            download_handler = DownloadHandler(self.airtable, video_id)
                            observer = Observer()
                            observer.schedule(download_handler, self.download_dir, recursive=False)
                            observer.start()
                            
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
                            # Wait for any context menu option to appear
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
                                print("Found Download video option, clicking...")
                                actions.move_to_element(download_option).click().perform()
                                print("Download initiated!")
                            else:
                                print("Download video option not found in context menu")
                                # Create record with Failed status
                                self.airtable.create_record(
                                    video_id=video_id,
                                    description=description if description else "No description available",
                                    uploader=uploader,
                                    status="Failed - No download option"
                                )
                                raise Exception("Download video option not found in context menu")
                            
                            # Wait for file to be downloaded (max 30 seconds)
                            print("Waiting for file download...")
                            start_time = time.time()
                            while not download_handler.found_file and (time.time() - start_time) < 30:
                                time.sleep(0.5)
                            
                            if download_handler.found_file:
                                print(f"File downloaded: {download_handler.found_file}")
                                # Create Airtable record with file
                                self.airtable.create_record(
                                    video_id, 
                                    description if description else "No description available", 
                                    uploader, 
                                    status="Downloaded",
                                    video_file=download_handler.found_file
                                )
                            else:
                                print("File download not detected")
                                self.airtable.create_record(
                                    video_id, 
                                    description if description else "No description available", 
                                    uploader, 
                                    status="Failed"
                                )
                            
                            # Stop file monitoring
                            observer.stop()
                            observer.join()
                            
                        except Exception as e:
                            print(f"\nError during download process: {str(e)}")
                            # Create record with Failed status if not already created
                            if "Download video option not found" not in str(e):
                                self.airtable.create_record(
                                    video_id=video_id,
                                    description=description if description else "No description available",
                                    uploader=uploader,
                                    status=f"Failed - {str(e)}"
                                )
                            
                            # Make sure to stop the observer if it exists
                            try:
                                observer.stop()
                                observer.join()
                            except:
                                pass
                        
                        print("\nClosing video tab...")
                        # Close the tab and switch back
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        print("Download process complete!")
                        print("="*50 + "\n")
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    print(f"Error in download handler: {str(e)}")
                    # If the main window is closed, exit the thread
                    try:
                        self.driver.current_url
                    except:
                        break
                    time.sleep(1)
        
        # Start the background thread
        import threading
        self.download_thread = threading.Thread(target=check_for_downloads, daemon=True)
        self.download_thread.start()

    def browse_favorites(self):
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
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

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
        
        # Initialize downloader with profile
        downloader = TikTokDownloader(profile_name)
        downloader.browse_favorites()
        
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        print("\nScript finished. Thanks for using TikTok Saved Videos Downloader!")

if __name__ == "__main__":
    main()
