#!/bin/bash
# Fix macOS Security Warning for GoogleFitSync
# Run this script after downloading a new version

echo "🔧 Fixing macOS security warning for GoogleFitSync..."

# Find GoogleFitSync in Downloads folder
GOOGLEFITSYNC_FILE=$(find ~/Downloads -name "GoogleFitSync" -type f 2>/dev/null | head -1)

if [ -z "$GOOGLEFITSYNC_FILE" ]; then
    echo "❌ GoogleFitSync not found in Downloads folder"
    echo "Please make sure you've extracted GoogleFitSync from the zip file"
    exit 1
fi

# Remove quarantine attributes
xattr -cr "$GOOGLEFITSYNC_FILE"

echo "✅ Security warning fixed!"
echo "📱 You can now run GoogleFitSync normally by double-clicking it"
echo ""
echo "File location: $GOOGLEFITSYNC_FILE"

