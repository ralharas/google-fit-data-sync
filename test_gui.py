#!/usr/bin/env python3
"""
Quick test script to verify cross-platform GUI functionality
Run this to test the GUI without needing OAuth credentials
"""

import platform
import tkinter as tk
from tkinter import messagebox

def test_gui():
    """Test the basic GUI functionality"""
    root = tk.Tk()
    root.title("Cross-Platform GUI Test")
    root.geometry("400x300")
    
    # Get system info
    system = platform.system()
    python_version = platform.python_version()
    
    # Create test UI
    tk.Label(root, text=f"🧪 Cross-Platform Test", 
             font=("Arial", 16, "bold")).pack(pady=20)
    
    tk.Label(root, text=f"System: {system}", 
             font=("Arial", 12)).pack(pady=5)
    
    tk.Label(root, text=f"Python: {python_version}", 
             font=("Arial", 12)).pack(pady=5)
    
    # Test checkboxes
    tk.Label(root, text="Testing Checkboxes:", 
             font=("Arial", 11, "bold")).pack(pady=(20, 5))
    
    test_vars = []
    for i, item in enumerate(["Steps", "Calories", "Heart Rate"]):
        var = tk.IntVar()
        test_vars.append(var)
        if system == "Windows":
            text = f"[{i+1}] {item}"
        else:
            icons = ["👟", "🔥", "❤️"]
            text = f"{icons[i]} {item}"
        
        tk.Checkbutton(root, text=text, variable=var).pack()
    
    def test_complete():
        selected = [f"Item {i+1}" for i, var in enumerate(test_vars) if var.get()]
        if selected:
            messagebox.showinfo("Test Result", f"✅ Selected: {', '.join(selected)}")
        else:
            messagebox.showwarning("Test Result", "⚠️ No items selected")
    
    tk.Button(root, text="Test Selection", 
              command=test_complete,
              bg="#3498db", fg="white",
              font=("Arial", 11, "bold"),
              padx=20, pady=5).pack(pady=20)
    
    tk.Label(root, text=f"✅ GUI test successful on {system}!", 
             fg="green", font=("Arial", 10)).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print(f"🔍 Testing GUI on {platform.system()}...")
    try:
        test_gui()
        print("✅ GUI test completed successfully!")
    except Exception as e:
        print(f"❌ GUI test failed: {e}")

