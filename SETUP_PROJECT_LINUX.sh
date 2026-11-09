#!/bin/bash

# Absolute path to this shell script
SHELL_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Python or PyPy executable
PY_EXEC=/dev/null

# Check if PyPy is installed
IsPyPyAvaliable="$(command -v pypy)"

# Check if Python is installed
IsPythonAvaliable="$(command -v python3)"

# Set corresponding executable
if [[ "$IsPyPyAvaliable" != "" ]]; then
    echo "Using pypy..."
    PY_EXEC=pypy
elif [[ "$IsPythonAvaliable" != "" ]]; then
    echo "Using python3..."
    PY_EXEC=python3
else
    echo "ERROR: PyPy and Python not found!"
    echo "Aborting..."

    read -n 1 -p "* Press any key to exit *" -s null
    echo -e "\n"
    exit 1
fi

# Create "bin" folder if it doesn't exists
if [ ! -d "$SHELL_PATH/bin" ]; then
    echo "Creating 'bin' folder..."
    mkdir "$SHELL_PATH/bin"
fi

# Create Python venv "PY_BIN" if it doesn't exists
if [ ! -d "$SHELL_PATH/bin/PY_BIN" ]; then
    echo "Generating Python venv..."
    $PY_EXEC -m venv "$SHELL_PATH/bin/PY_BIN"
fi

# Activate venv
. $SHELL_PATH/bin/PY_BIN/bin/activate

# Install Pillow
echo "Installing 'Pillow' package..."
python -m pip install --force-reinstall pillow --no-cache-dir

# End
echo "Done!"
deactivate

read -n 1 -p "* Press any key to exit *" -s null
echo -e "\n"
exit 0
