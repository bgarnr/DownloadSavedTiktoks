"""
Manages interactions with Airtable for storing TikTok video metadata and file links.
"""

import os
import socketserver
import threading
from urllib.parse import quote
from pyairtable import Table
from drive_manager import DriveManager
from file_handlers import SimpleHTTPRequestHandlerWithCORS

class AirtableManager:
    """Manages interactions with Airtable for storing TikTok video data."""
    
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
