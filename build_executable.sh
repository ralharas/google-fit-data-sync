#!/bin/bash
# Build script for Google Fit Data Sync executables
# Works on both Mac and Windows (with Git Bash)

echo "Building Google Fit Data Sync executable..."
echo "Platform: $(uname -s)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Mac/Linux
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv pandas pyinstaller

# Build executable
echo "Building executable..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows build
    pyinstaller --onefile --windowed --name "GoogleFitSync-Windows" main.py
    echo "Windows executable created: dist/GoogleFitSync-Windows.exe"
else
    # Mac build
    pyinstaller --onefile --windowed --name "GoogleFitSync-Mac" main.py
    echo "Mac executable created: dist/GoogleFitSync-Mac"
    echo "Mac app bundle created: dist/GoogleFitSync-Mac.app"
fi

echo "Build complete!"
echo ""
echo "To run the executable:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  Double-click: dist/GoogleFitSync-Windows.exe"
else
    echo "  Double-click: dist/GoogleFitSync-Mac.app"
    echo "  Or terminal: ./dist/GoogleFitSync-Mac"
fi
echo ""
echo "Remember to set up OAuth credentials:"
echo "  export GOOGLE_CLIENT_ID='your_client_id'"
echo "  export GOOGLE_CLIENT_SECRET='your_client_secret'"

