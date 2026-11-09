#!/bin/bash

# Prevents running the script with admin rights
if [ "$EUID" -eq 0 ]; then
    echo "Running with admin rights may break the project!"
    echo "Aborting..."
    read -n 1 -p "* Press any key to exit *" -s null
    echo -e "\n"
    exit 1
fi

# Absolute path to this shell script
SHELL_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Project paths
PROJECT_ROOT="$SHELL_PATH"
UTILS="$PROJECT_ROOT/utils"
PROJECT_BIN="$PROJECT_ROOT/bin"
SRC_APP="$PROJECT_ROOT/app"
SRC_ASSETS="$SRC_APP/assets"
APP_BIN="$PROJECT_BIN/BananaUI_Linux_x64"
APP_CONTENT="$APP_BIN/app"
RUNTIME_FOLDER="$APP_BIN/runtime"

# Python or PyPy executable
PY_EXEC=/dev/null

# Check if PyPy is installed
IsPyPyAvaliable="$(command -v pypy)"

# Check if Python is installed
IsPythonAvaliable="$(command -v python3)"

# Set corresponding executable (prefer PyPy, fallback to Python3)
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

# Erase last build of the app
if [ -d "$APP_BIN" ]; then
    echo "Deleting last build of BananaUI..."
    rm -rf "$APP_BIN"
    echo "BananaUI deleted!"
fi

# Creating output folder
echo "Creating folders for exported application..."
mkdir -p "$PROJECT_BIN"
mkdir -p "$APP_BIN"
mkdir -p "$APP_CONTENT"
echo "---------------------------------------"

# Perform clean installation of runtime
echo "Executing clean installation of runtime..."

BUNDLED_PYPY_LINUX=""
for archive in "$UTILS"/pypy*linux*.tar* "$UTILS"/pypy*linux*.7z; do
    if [ -f "$archive" ]; then
        BUNDLED_PYPY_LINUX="$archive"
        break
    fi
done

if [ -n "$BUNDLED_PYPY_LINUX" ]; then
    echo "Extracting bundled PyPy from $(basename "$BUNDLED_PYPY_LINUX")..."
    mkdir -p "$RUNTIME_FOLDER"
    if [[ "$BUNDLED_PYPY_LINUX" == *.tar* ]]; then
        if tar -tf "$BUNDLED_PYPY_LINUX" | grep -q "^bin/"; then
            tar -xf "$BUNDLED_PYPY_LINUX" -C "$RUNTIME_FOLDER"
        else
            tar -xf "$BUNDLED_PYPY_LINUX" -C "$RUNTIME_FOLDER" --strip-components=1
        fi
    elif command -v 7z >/dev/null 2>&1; then
        7z x -aoa -y -o"$RUNTIME_FOLDER" "$BUNDLED_PYPY_LINUX"
    fi
else
    echo "Creating virtual environment for portable runtime..."
    $PY_EXEC -m venv --copies "$RUNTIME_FOLDER" 2>/dev/null || $PY_EXEC -m venv "$RUNTIME_FOLDER"
fi
echo "---------------------------------------"

# Determine runtime python binary
RUNTIME_PY=""
for candidate in \
    "$RUNTIME_FOLDER/bin/pypy" \
    "$RUNTIME_FOLDER/bin/pypy3" \
    "$RUNTIME_FOLDER/bin/pypy3.11" \
    "$RUNTIME_FOLDER/bin/python" \
    "$RUNTIME_FOLDER/bin/python3" \
    "$RUNTIME_FOLDER/bin/python3.12" \
    "$RUNTIME_FOLDER/bin/python3.11" \
    "$RUNTIME_FOLDER/pypy" \
    "$RUNTIME_FOLDER/pypy3" \
    "$RUNTIME_FOLDER/python" \
    "$RUNTIME_FOLDER/python3"; do
    if [ -x "$candidate" ]; then
        RUNTIME_PY="$candidate"
        break
    fi
done

if [ -z "$RUNTIME_PY" ]; then
    echo "WARNING: Runtime binary not found in $RUNTIME_FOLDER!"
else
    # Bootstrap pip if missing (standard for newly extracted PyPy distributions)
    if ! "$RUNTIME_PY" -m pip --version >/dev/null 2>&1; then
        echo "Bootstrapping pip in runtime via ensurepip..."
        "$RUNTIME_PY" -m ensurepip --default-pip >/dev/null 2>&1 || "$RUNTIME_PY" -m ensurepip >/dev/null 2>&1
    fi

    echo "Installing 'Pillow' package..."
    if "$RUNTIME_PY" -m pip install --force-reinstall pillow --no-cache-dir; then
        echo "Pillow successfully installed from network!"
    else
        echo "Network installation failed, checking local packages..."
        SITE_DIR="$(find "$RUNTIME_FOLDER" -type d -name "site-packages" 2>/dev/null | head -n 1)"
        if [ -n "$SITE_DIR" ] && [ -d "$SITE_DIR" ]; then
            LOCAL_SITE="$(find "$PROJECT_BIN/PY_BIN" -type d -name "site-packages" 2>/dev/null | head -n 1)"
            if [ -n "$LOCAL_SITE" ] && [ -d "$LOCAL_SITE/PIL" ]; then
                echo "Copying Pillow from local PY_BIN..."
                cp -r "$LOCAL_SITE"/PIL* "$SITE_DIR/" 2>/dev/null || true
                cp -r "$LOCAL_SITE"/pillow* "$SITE_DIR/" 2>/dev/null || true
            elif [ -d "/usr/lib/python3/dist-packages/PIL" ]; then
                echo "Copying Pillow from system packages..."
                cp -r /usr/lib/python3/dist-packages/PIL* "$SITE_DIR/" 2>/dev/null || true
                cp -r /usr/lib/python3/dist-packages/pillow* "$SITE_DIR/" 2>/dev/null || true
            fi
        fi
    fi

    if "$RUNTIME_PY" -c "import PIL" 2>/dev/null; then
        echo "Pillow verified successfully!"
    else
        echo "WARNING: Pillow verification failed. You may need to run 'pip install pillow' inside the runtime."
    fi
fi
echo "---------------------------------------"

# Copying assets
echo "Copying assets..."
cp -r "$SRC_ASSETS" "$APP_CONTENT/"

# Copying code
echo "Copying code..."
echo "---------------------------------------"
(cd "$SRC_APP" && find . -type f -name "*.py" -exec cp --parents {} "$APP_CONTENT" \;)
echo "Application code copied successfully!"
echo "---------------------------------------"

# Generating executable
echo "Generating app executable file..."
echo "---------------------------------------"
EXE_FILE="$APP_BIN/BananaUI"
cat << 'EOF' > "$EXE_FILE"
#!/bin/bash

# Function to display GUI error or console error
show_error() {
    local msg="$1"
    echo "ERROR: $msg" >&2
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        if command -v zenity >/dev/null 2>&1; then
            zenity --error --text="$msg" --title="BananaUI Error" 2>/dev/null
        elif command -v kdialog >/dev/null 2>&1; then
            kdialog --error "$msg" --title "BananaUI Error" 2>/dev/null
        elif command -v xmessage >/dev/null 2>&1; then
            xmessage -center "BananaUI: $msg" 2>/dev/null
        fi
    fi
}

# Prevents running the script with admin rights
if [ "$EUID" -eq 0 ]; then
    show_error "Running with admin rights may break the project!"
    exit 1
fi

# Directory of this launcher script
MY_SCRIPT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
RUNTIME_DIR="$MY_SCRIPT_DIR/runtime"
APP_DIR="$MY_SCRIPT_DIR/app"
MAIN_SCRIPT="$APP_DIR/Main.py"

# Abort if runtime doesn't exist
if [ ! -d "$RUNTIME_DIR" ]; then
    show_error "Runtime folder not found, check if your distribution is intact!"
    exit 1
fi

# Find Python/PyPy executable inside runtime
PY_EXEC=""
for candidate in \
    "$RUNTIME_DIR/bin/pypy" \
    "$RUNTIME_DIR/bin/pypy3" \
    "$RUNTIME_DIR/bin/pypy3.11" \
    "$RUNTIME_DIR/bin/python" \
    "$RUNTIME_DIR/bin/python3" \
    "$RUNTIME_DIR/bin/python3.12" \
    "$RUNTIME_DIR/bin/python3.11" \
    "$RUNTIME_DIR/bin/python3.10" \
    "$RUNTIME_DIR/pypy" \
    "$RUNTIME_DIR/pypy3" \
    "$RUNTIME_DIR/python" \
    "$RUNTIME_DIR/python3"; do
    if [ -x "$candidate" ]; then
        PY_EXEC="$candidate"
        break
    fi
done

if [ -z "$PY_EXEC" ]; then
    show_error "Python or PyPy executable not found in runtime, check if your distribution is intact!"
    exit 1
fi

# Setting up PATH environment variable for the current process session
export PATH="$RUNTIME_DIR/bin:$PATH"

# Running the project
"$PY_EXEC" "$MAIN_SCRIPT" "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    show_error "Something went wrong when trying to run the app... (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
EOF

chmod +x "$EXE_FILE"
ln -sf BananaUI "$APP_BIN/BananaUI.sh"

# End
echo "---------------------------------------"
echo "DONE!"
echo "Portable Linux build created at: $APP_BIN"
echo "You can launch the app by running: $APP_BIN/BananaUI"

# Only pause if running interactively in terminal and no skip flag was provided
if [ -t 0 ] && [ "$1" != "-y" ] && [ "$1" != "--no-pause" ]; then
    read -n 1 -p "* Press any key to exit *" -s null
    echo -e "\n"
fi
exit 0
