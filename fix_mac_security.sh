#!/bin/bash
# Fix macOS security issues for GoogleFitSync executable
# Run this script after downloading the executable from GitHub

echo "Fixing macOS security for GoogleFitSync..."

# Check if executable exists
if [ ! -f "GoogleFitSync" ]; then
    echo "Error: GoogleFitSync executable not found in current directory"
    echo "Please download it from GitHub Actions artifacts first"
    exit 1
fi

# Make executable
chmod +x GoogleFitSync
echo "Made GoogleFitSync executable"

# Remove quarantine attribute
xattr -d com.apple.quarantine GoogleFitSync 2>/dev/null || true
echo "Removed quarantine attribute"

# Try to remove all extended attributes
xattr -c GoogleFitSync 2>/dev/null || true
echo "Cleared extended attributes"

echo ""
echo "Fix complete! You should now be able to run GoogleFitSync"
echo ""
echo "If you still get security warnings:"
echo "1. Right-click GoogleFitSync → Open"
echo "2. Click 'Open' in the security dialog"
echo "3. Or go to System Preferences → Security & Privacy → General"
echo "   and click 'Open Anyway' next to the GoogleFitSync message"
echo ""
echo "To run: ./GoogleFitSync"

