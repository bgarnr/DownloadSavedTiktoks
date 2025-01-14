# TikTok Favorites Downloader

A Python script to help download your favorite TikTok videos. The script adds download buttons to your favorites page and opens each video in a new tab for easy downloading.

## Features

- Uses your existing Chrome profile (no need to log in again)
- Supports multiple Chrome profiles (enter profile name when prompted)
- Adds download buttons to your favorites page
- Opens videos in new tabs for downloading
- Visual feedback for downloaded videos
- Works with TikTok's native download feature

## Requirements

- Python 3.7+
- Google Chrome browser
- Chrome profile with TikTok account

## Installation

1. Clone this repository:
```bash
git clone https://github.com/bgarnr/DownloadSavedTiktoks.git
cd DownloadSavedTiktoks
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Close all Chrome windows
2. Run the script:
```bash
python tiktok_downloader.py
```
3. When prompted, enter your Chrome profile name or press Enter to use default
4. Log in using the QR code if needed
5. Click the download buttons on videos you want to save
6. Use TikTok's native download button in the new tabs

### Using Different Chrome Profiles

If you have multiple Chrome profiles, you can specify which one to use when running the script. To find your profile name:

1. Open Chrome and go to `chrome://version`
2. Look for "Profile Path" - the last part of the path is your profile name
3. Common profile names are:
   - `Default` - The default Chrome profile
   - `Profile 1`, `Profile 2`, etc. - Additional profiles
   - Custom named profiles will show their name

When running the script, enter this profile name when prompted.

## Note

This script is designed for personal use and respects TikTok's native download functionality. Please be mindful of TikTok's terms of service and content creators' rights when downloading videos.
