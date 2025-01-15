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
        print("\nInitializing AirtableManager...")
        
        # Get environment variables
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.token = os.getenv("AIRTABLE_ACCESS_TOKEN_VALUE")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME")
        
        # Initialize other attributes
        self.http_server = None
        self.server_thread = None
        self.drive_manager = DriveManager()
        self.table = None  # Initialize to None
        
        print(f"Environment variables loaded:")
        print(f"Base ID: {self.base_id}")
        print(f"Token available: {'Yes' if self.token else 'No'}")
        print(f"Table name: {self.table_name}")
        
        # Validate environment variables
        if not self.base_id:
            raise ValueError("Missing AIRTABLE_BASE_ID in environment variables")
        if not self.token:
            raise ValueError("Missing AIRTABLE_ACCESS_TOKEN_VALUE in environment variables")
        if not self.table_name:
            raise ValueError("Missing AIRTABLE_TABLE_NAME in environment variables")
            
        try:
            print("Attempting to connect to Airtable...")
            self.table = Table(self.token, self.base_id, self.table_name)
            # Test the connection by trying to get one record
            try:
                self.table.first()
                print("Successfully connected to Airtable!")
            except Exception as e:
                print(f"Failed to verify table connection: {str(e)}")
                raise
        except Exception as e:
            print(f"Error connecting to Airtable: {str(e)}")
            print(f"Full error details: {repr(e)}")
            raise

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

    def create_record(self, video_id, description, uploader, status="Downloaded", video_file=None, source_url=None):
        """Create a record in Airtable for a downloaded video"""
        try:
            print(f"\nCreating Airtable record...")
            print(f"Video ID: {video_id}")
            print(f"Uploader: {uploader}")
            print(f"Description: {description if description else 'No description available'}")
            print(f"Status: {status}")
            
            from datetime import datetime
            current_time = datetime.now().isoformat()
            
            record_data = {
                "Video Id": video_id,
                "Description": description if description else "No description available",
                "Uploader": uploader,
                "Status": status,
                "Date Uploaded": current_time
            }
            
            if source_url:
                record_data["Source Url"] = source_url
            
            # Create the record first (fast operation)
            record = self.table.create(record_data)
            print("Successfully created base Airtable record")
            
            # If we have a video file, upload it to Google Drive and update the record
            if video_file and os.path.exists(video_file):
                print(f"\nUploading video file: {video_file}")
                try:
                    # Upload to Google Drive
                    shareable_link = self.drive_manager.upload_file(video_file)
                    
                    if shareable_link:
                        print(f"File uploaded to Drive: {shareable_link}")
                        # Update Airtable record with video file
                        self.table.update(record["id"], {
                            "Video File": [{"url": shareable_link}]
                        })
                        print("Successfully updated record with video file")
                    else:
                        print("Failed to upload to Google Drive")
                except Exception as e:
                    print(f"Error during video upload: {str(e)}")
                    # Don't re-raise, let the record creation succeed
            
            return record
            
        except Exception as e:
            print(f"Error in create_record: {str(e)}")
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
