"""Main entry point for the NanoBanana Gemini Image Generator application."""
from inspect import getsourcefile
import os
import sys
import tkinter as tk
from ui import BananaUIApp

def main():
    """Initializes and runs the BananaUI front-end application."""
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
