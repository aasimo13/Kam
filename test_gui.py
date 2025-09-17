#!/usr/bin/env python3
"""
Simple test to check if Tkinter GUI works
"""
import tkinter as tk
from tkinter import ttk
import sys
import platform

print(f"Python version: {sys.version}")
print(f"Platform: {platform.system()}")

try:
    root = tk.Tk()
    root.title("USB Camera Tester - GUI Test")
    root.geometry("400x300")

    # Create a simple interface
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    label = ttk.Label(frame, text="GUI Test - If you see this, Tkinter is working!")
    label.pack(pady=10)

    button = ttk.Button(frame, text="Click Me", command=lambda: print("Button clicked!"))
    button.pack(pady=10)

    status_label = ttk.Label(frame, text=f"Platform: {platform.system()}")
    status_label.pack(pady=10)

    print("GUI created successfully. Starting mainloop...")
    root.mainloop()
    print("GUI closed.")

except Exception as e:
    print(f"GUI Error: {e}")
    import traceback
    traceback.print_exc()