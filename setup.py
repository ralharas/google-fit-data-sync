#!/usr/bin/env python3
"""
Cross-platform setup script for Google Fit Data Sync
Works on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version} detected")
    return True

def create_directories():
    """Create necessary directories for data storage"""
    directories = [
        "Steps/Raw",
        "Calories/Raw", 
        "Distance/Raw",
        "HeartRate/Raw",
        "Weight/Raw",
        "Height/Raw",
        "BodyFat/Raw",
        "BloodPressure/Raw",
        "BloodGlucose/Raw",
        "OxygenSaturation/Raw",
        "BodyTemperature/Raw"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Data directories created")

def display_setup_info():
    """Display setup information"""
    system = platform.system()
    print(f"\n🔧 Setting up Google Fit Data Sync for {system}")
    print("=" * 50)
    
    if system == "Windows":
        print("📌 Windows-specific features:")
        print("   • Text-based icons for better compatibility")
        print("   • Windows-optimized scrolling")
        print("   • Segoe UI font")
    elif system == "Darwin":  # macOS
        print("📌 macOS-specific features:")
        print("   • Native emoji support")
        print("   • SF Pro Display font")
        print("   • macOS-optimized UI")
    else:  # Linux
        print("📌 Linux-specific features:")
        print("   • Ubuntu/Noto fonts")
        print("   • Cross-platform emoji support")
    
    print("\n📋 OAuth Setup Required:")
    print("   1. Set GOOGLE_CLIENT_ID environment variable")
    print("   2. Set GOOGLE_CLIENT_SECRET environment variable")
    print("   OR")
    print("   3. Create oauth_config.json with your credentials")

def main():
    """Main setup function"""
    display_setup_info()
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_requirements():
        sys.exit(1)
    
    create_directories()
    
    print("\n🎉 Setup complete!")
    print("\n▶️  To run the application:")
    print("   python main.py")
    print("\n📖 Make sure to configure OAuth credentials before running!")

if __name__ == "__main__":
    main()

