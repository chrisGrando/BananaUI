"""Main entry point for the NanoBanana Gemini Image Generator application."""
from inspect import getsourcefile
import os
import sys
import tkinter as tk
from ui import BananaUIApp, ensure_interactive_desktop

def main():
    """Initializes and runs the BananaUI front-end application."""
    # Ensure current thread is attached to the interactive 'default' desktop on 'WinSta0'
    ensure_interactive_desktop()

    # Delete error log file if exists
    appRunningDir = (os.path.dirname(getsourcefile(lambda:0))).replace("\\", "/")
    errorFile = appRunningDir + "/error.log"
    if os.path.exists(errorFile):
        os.remove(errorFile)
    
    # Run app
    root = tk.Tk()
    app = BananaUIApp(root)
    root.mainloop()

# Call main function
if __name__ == "__main__":
    main()
