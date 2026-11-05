"""Main entry point for the NanoBanana Gemini Image Generator application."""
import sys
from pathlib import Path
import tkinter as tk
from ui import BananaUIApp, ensure_interactive_desktop

def main():
    """Initializes and runs the BananaUI front-end application."""
    # Ensure current thread is attached to the interactive 'default' desktop on 'WinSta0'
    ensure_interactive_desktop()

    # Delete error log file if exists
    error_file = Path(__file__).resolve().parent / "error.log"
    if error_file.exists():
        error_file.unlink()
    
    # Run app
    root = tk.Tk()
    app = BananaUIApp(root)
    root.mainloop()

# Call main function
if __name__ == "__main__":
    main()
