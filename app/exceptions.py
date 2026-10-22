"""Custom exceptions for BananaUI / NanoBanana."""
import os
import traceback
from inspect import getsourcefile


class NanoBananaAPIError(Exception):
    """Custom exception for NanoBanana API errors."""
    def __init__(self, message):
        # Save exception report to log file
        self.message = message
        appRunningDir = (os.path.dirname(getsourcefile(lambda: 0))).replace("\\", "/")
        errorFileName = appRunningDir + "/error.log"
        with open(errorFileName, "a") as error_file:
            txt = self.message + "\n" + "----------------------------------------------------------------------------------" + "\n"
            print(txt)
            error_file.write(txt)
            error_file.write(str(traceback.format_exc()) + "\n" + "----------------------------------------------------------------------------------" + "\n")

        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)
