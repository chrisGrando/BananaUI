"""Custom exceptions for BananaUI / NanoBanana."""
import traceback
from pathlib import Path


class NanoBananaAPIError(Exception):
    """Custom exception for NanoBanana API errors."""
    def __init__(self, message):
        # Save exception report to log file
        self.message = message
        error_file = Path(__file__).resolve().parent / "error.log"
        with open(error_file, "a") as f:
            txt = self.message + "\n" + "----------------------------------------------------------------------------------" + "\n"
            print(txt)
            f.write(txt)
            f.write(str(traceback.format_exc()) + "\n" + "----------------------------------------------------------------------------------" + "\n")

        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)
