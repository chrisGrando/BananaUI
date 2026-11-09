#!/bin/bash

# Absolute path to this shell script
SHELL_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Check if local Python venv doesn't exists
if [ ! -d "$SHELL_PATH/bin/PY_BIN/bin" ]; then
    echo "ERROR: Python venv not found, have you already run the script 'SETUP_PROJECT_LINUX.sh'?"

    read -n 1 -p "* Press any key to exit *" -s null
    echo -e "\n"
    exit 1
fi

# Activate venv
. $SHELL_PATH/bin/PY_BIN/bin/activate

# Run project
python $SHELL_PATH/app/Main.py

# End
deactivate
