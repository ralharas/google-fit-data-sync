# 🏃‍♂️ Google Fit Data Sync

A cross-platform desktop application to sync all your Google Fit data with local CSV files. Works seamlessly on **Windows**, **macOS**, and **Linux**.

## ✨ Features

- **Comprehensive Data Import**: Steps, Calories, Distance, Heart Rate, Weight, Height, Body Fat, Blood Pressure, Blood Glucose, Oxygen Saturation, and Body Temperature
- **Selective Import**: Choose which data types to import with checkboxes
- **Cross-Platform GUI**: Native look and feel on Windows, macOS, and Linux
- **Historical & Daily Sync**: Import full history or set up daily automatic syncing
- **User-Friendly Interface**: Modern, intuitive design with visual feedback

## 🔧 Cross-Platform Compatibility

### Windows
- ✅ Text-based icons for maximum compatibility
- ✅ Segoe UI font for native Windows look
- ✅ Windows-optimized mouse wheel scrolling
- ✅ Proper window positioning and sizing

### macOS
- ✅ Native emoji support
- ✅ SF Pro Display system font
- ✅ macOS-optimized UI elements
- ✅ Retina display support

### Linux
- ✅ Ubuntu/Noto font compatibility
- ✅ Cross-platform emoji rendering
- ✅ GTK-compatible styling

## 📋 Requirements

- **Python 3.8+**
- **Google Fit account** with data
- **Google Cloud Project** with Fitness API enabled
- **OAuth 2.0 credentials**

## Quick Setup

### Option 1: Download Pre-built Executable (Recommended)

1. Go to [GitHub Actions](https://github.com/ralharas/google-fit-data-sync/actions)
2. Click on the latest successful workflow run
3. Download the artifact for your platform:
   - `GoogleFitSync-windows-latest` (Windows .exe)
   - `GoogleFitSync-macos-latest` (Mac executable)
   - `GoogleFitSync-ubuntu-latest` (Linux executable)

#### macOS Security Fix
After downloading the Mac executable, you may see a security warning. To fix this:

```bash
# Remove quarantine attribute (recommended)
xattr -d com.apple.quarantine GoogleFitSync-Mac.app

# Or download the fix script
curl -O https://raw.githubusercontent.com/ralharas/google-fit-data-sync/main/fix_mac_security.sh
chmod +x fix_mac_security.sh
./fix_mac_security.sh
```

Or manually:
1. Right-click the executable → "Open"
2. Click "Open" in the security dialog
3. Or go to System Preferences → Security & Privacy → General and click "Open Anyway"

### Option 2: Build from Source

#### 1. Clone the Repository
```bash
git clone https://github.com/ralharas/google-fit-data-sync.git
cd dataAutomationProject
```

### 2. Run Setup Script
```bash
python setup.py
```

This will:
- Check Python version compatibility
- Install all required dependencies
- Create necessary data directories
- Display platform-specific setup information

### 3. Configure OAuth Credentials

#### Option A: Environment Variables
```bash
# Windows (Command Prompt)
set GOOGLE_CLIENT_ID=your_client_id_here
set GOOGLE_CLIENT_SECRET=your_client_secret_here

# Windows (PowerShell)
$env:GOOGLE_CLIENT_ID="your_client_id_here"
$env:GOOGLE_CLIENT_SECRET="your_client_secret_here"

# macOS/Linux
export GOOGLE_CLIENT_ID="your_client_id_here"
export GOOGLE_CLIENT_SECRET="your_client_secret_here"
```

#### Option B: Configuration File
Create `oauth_config.json`:
```json
{
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here"
}
```

### 4. Run the Application
```bash
python main.py
```

## 🎯 Usage

1. **Launch the App**: Run `python main.py`
2. **Select Data Types**: Check the boxes for data you want to import
3. **Quick Selection**: Use "Select All" to choose everything
4. **Start Import**: Click the "Start Import" button
5. **OAuth Authorization**: Complete Google authentication in your browser
6. **Monitor Progress**: Watch real-time status updates

## 📊 Data Output

Data is saved as CSV files in organized folders:
```
dataAutomationProject/
├── Steps/Raw/
├── Calories/Raw/
├── Distance/Raw/
├── HeartRate/Raw/
├── Weight/Raw/
├── Height/Raw/
├── BodyFat/Raw/
├── BloodPressure/Raw/
├── BloodGlucose/Raw/
├── OxygenSaturation/Raw/
└── BodyTemperature/Raw/
```

## 🔒 Security

- OAuth tokens stored securely in user home directory
- No credentials stored in plain text
- Environment variable support for CI/CD
- Local-only data processing

## 🛠️ Development

### Manual Installation
```bash
pip install -r requirements.txt
```

### Dependencies
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth 2.0 flow
- `google-api-python-client` - Google Fit API client
- `pandas` - Data processing
- `tkinter` - GUI framework (built into Python)

## 📱 Platform-Specific Notes

### Windows
- Uses text symbols instead of emojis for better font compatibility
- Optimized for Windows 10/11 styling
- Supports both Command Prompt and PowerShell

### macOS
- Full emoji support with Apple Color Emoji font
- Integrates with macOS design language
- Works on both Intel and Apple Silicon Macs

### Linux
- Tested on Ubuntu, should work on most distributions
- Uses system fonts and color schemes
- Compatible with various desktop environments

## 🔧 Troubleshooting

### Common Issues

**"OAuth credentials not found"**
- Ensure environment variables are set correctly
- Or create `oauth_config.json` file
- Check Google Cloud Console setup

**"No module named 'tkinter'"**
- On Ubuntu/Debian: `sudo apt-get install python3-tk`
- On CentOS/RHEL: `sudo yum install tkinter`

**"Font not found" warnings**
- Install system fonts: Segoe UI (Windows), SF Pro (macOS), Ubuntu/Noto (Linux)

**API rate limits**
- Google Fit API has daily quotas
- Large historical imports may take time

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms
5. Submit a pull request

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check this README and code comments

---

**Made with ❤️ for cross-platform health data automation**

