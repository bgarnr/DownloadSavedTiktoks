# TikTok Favorites Downloader

A Python script to help download your favorite TikTok videos. The script adds download buttons to your favorites page and automatically handles the download process.

## 👋 For Non-Technical Users

This tool is designed to be user-friendly, even if you're not familiar with programming! We recommend:

1. **Using Windsurf Editor**: 
   - Download and install Windsurf, a smart code editor that can help you set up and run this tool
   - Windsurf will read this README and guide you through the setup process
   - It can help you make necessary changes like setting your TikTok username

2. **Before Running**:
   - You'll need to change the TikTok username in the code from `@dysonsmear` to your username
   - If you're concerned about security, feel free to:
     - Review the code using ChatGPT or Claude
     - Ask questions in the GitHub Issues section
     - Have a tech-savvy friend review it

3. **Safety First**:
   - Only download this code from the official GitHub repository
   - Never enter passwords or sensitive information if prompted
   - The script only needs your Chrome profile to access TikTok as you

## Features

- Uses your existing Chrome profile (no need to log in again)
- Configurable Chrome profile via `.env` file
- Adds download buttons to your favorites page
- Automatically handles the download process
- Visual feedback for downloaded videos
- Works with TikTok's native download feature

## Requirements

- Python 3.7+
- Google Chrome browser
- Chrome profile with TikTok account
- Recommended: Windsurf Editor

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

3. Configure your Chrome profile:
   - Create a `.env` file in the project directory
   - Add your Chrome profile name: `CHROME_PROFILE=your_profile_name`
   - Example: `CHROME_PROFILE=dysonsmear`

4. Update your TikTok username:
   - Open `tiktok_downloader.py` in Windsurf or any text editor
   - Find the line with `@dysonsmear` and replace it with your TikTok username
   - Example: If your profile is at `tiktok.com/@your_name`, change it to `@your_name`

## Usage

1. Close all Chrome windows
2. Run the script:
```bash
python tiktok_downloader.py
```
3. Log in using the QR code if needed
4. Click the download buttons on videos you want to save
5. The script will automatically handle the download process

### Finding Your Chrome Profile Name

To find your Chrome profile name:

1. Open Chrome and go to `chrome://version`
2. Look for "Profile Path" - the last part of the path is your profile name
3. Add this name to your `.env` file

### Common Profile Names

- `Default` - The default Chrome profile
- `Profile 1`, `Profile 2`, etc. - Additional profiles
- Custom named profiles will show their name

## Note

This script is designed for personal use and respects TikTok's native download functionality. Please be mindful of TikTok's terms of service and content creators' rights when downloading videos.

## Getting Help

If you're having trouble:
1. Open this project in Windsurf Editor for guided assistance
2. Create an issue on GitHub with any questions
3. If you're not comfortable with code, ask a technical friend to help review and set it up

Remember: Your safety is important! Always review code or ask for help if you're unsure about running something on your computer.
