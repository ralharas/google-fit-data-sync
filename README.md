# Google Fit Data Sync

A cross-platform application to sync and export your Google Fit step count data to CSV files.

## Features

- 🏃‍♂️ Sync Google Fit step count data
- 😴 Sync Google Fit sleep data  
- ❤️ Sync heart rate data
- ⚖️ Sync weight data
- 🔥 Sync calories burned data
- 📏 Sync distance traveled data
- 📊 Export to CSV format
- 🔄 Historical data import (from 2022)
- ⏰ Daily automatic sync
- 🖥️ Cross-platform support (Windows, macOS, Linux)
- ✅ **No setup required** - OAuth credentials built-in!

## Quick Start for Windows Users

### Download and Run - That's It!

1. Go to the [Releases](../../releases) page
2. Download `GoogleFitSync-Windows.zip`
3. Extract the zip file
4. Double-click `GoogleFitSync.exe`
5. Sign in with your Google account when prompted
6. Click "Start Full Import + Daily Auto"

**No technical setup needed!** OAuth credentials are embedded in the app.

### Usage

1. Double-click the executable file
2. Click "Authorize with Google" when prompted
3. Click "Start Full Import + Daily Auto" to begin syncing
4. Data will be saved to:
   - `Steps/Raw/` - Step count data
   - `Sleep/Raw/` - Sleep tracking data
   - `HeartRate/Raw/` - Heart rate measurements
   - `Weight/Raw/` - Weight measurements
   - `Calories/Raw/` - Calories burned data
   - `Distance/Raw/` - Distance traveled data
   
   Each folder contains both `*_full.csv` (historical) and `*_daily.csv` (daily updates)

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

