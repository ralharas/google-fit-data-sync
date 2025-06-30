# Google Fit Data Sync

A cross-platform application to sync and export your Google Fit step count data to CSV files.

## Features

- 🏃‍♂️ Sync Google Fit step count data
- 📊 Export to CSV format
- 🔄 Historical data import (from 2022)
- ⏰ Daily automatic sync
- 🖥️ Cross-platform support (Windows, macOS, Linux)

## Quick Start

### Download Pre-built Executables

1. Go to the [Releases](../../releases) page
2. Download the appropriate file for your operating system:
   - **Windows**: `GoogleFitSync.exe`
   - **macOS**: `GoogleFitSync` (macOS)
   - **Linux**: `GoogleFitSync` (Linux)

### Setup Google Fit API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Fit API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials and rename to `client_secret.json`
6. Copy `client_secret.json.template` to `client_secret.json` and fill in your credentials
7. Place `client_secret.json` in the same directory as the executable

### Usage

1. Double-click the executable file
2. Click "Authorize with Google" when prompted
3. Click "Start Full Import + Daily Auto" to begin syncing
4. Data will be saved to `Steps/Raw/` directory:
   - `steps_data_full.csv` - Complete historical data
   - `steps_data_daily.csv` - Daily updates

## Development

### Requirements

- Python 3.11+
- Google Fit API credentials

### Installation

```bash
git clone <repository-url>
cd dataAutomationProject
pip install -r requirements.txt
```

### Running from Source

```bash
python main.py
```

### Building Executables

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "client_secret.json:." --name "GoogleFitSync" main.py
```

## Data Format

The exported CSV files contain:
- `start`: Start timestamp of the data point
- `end`: End timestamp of the data point  
- `steps`: Number of steps recorded

## Troubleshooting

- **"client_secret.json not found"**: Make sure the credentials file is in the same directory as the executable
- **OAuth errors**: Create a new OAuth client in Google Cloud Console
- **Permission errors**: Make sure the executable has write permissions to the output directory

## License

This project is for personal use. Please respect Google's API terms of service.

