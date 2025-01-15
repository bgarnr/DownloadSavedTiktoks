"""
File system event handlers and HTTP server handlers for the TikTok downloader.
"""

import os
import time
import http.server
from watchdog.events import FileSystemEventHandler

class DownloadHandler(FileSystemEventHandler):
    """Handles file system events for downloaded TikTok videos."""
    
    def __init__(self, airtable_manager, video_id, source_url=None):
        """Initialize with AirtableManager instance and video ID."""
        self.airtable_manager = airtable_manager
        self.video_id = video_id
        self.source_url = source_url
        self.found_file = None
        print(f"\nFile monitoring initialized for video {video_id}")
        
    def on_created(self, event):
        """Called when a file is created in the monitored directory."""
        print(f"\nFile created event detected!")
        print(f"Path: {event.src_path}")
        print(f"Is directory: {event.is_directory}")
        print(f"Source URL for record: {self.source_url}")  # Debug print
        if not event.is_directory:
            print(f"File extension: {os.path.splitext(event.src_path)[1]}")
            
            # If this is a video file, note it but don't create record yet
            if event.src_path.endswith(('.mp4', '.webm')):
                print(f"\nNew video file detected: {event.src_path}")
                self.found_file = event.src_path

    def on_moved(self, event):
        """Called when a file is moved or renamed in the monitored directory."""
        print(f"\nFile moved/renamed event detected!")
        print(f"Source path: {event.src_path}")
        print(f"Destination path: {event.dest_path}")
        
        # If this is the final move (download complete)
        if event.dest_path.endswith('.mp4') and not event.dest_path.endswith('.crdownload'):
            print(f"\nDownload completed: {event.dest_path}")
            self.found_file = event.dest_path  # Use dest_path for final file location

class SimpleHTTPRequestHandlerWithCORS(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support."""
    
    def end_headers(self):
        """Add CORS headers to allow cross-origin requests."""
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
