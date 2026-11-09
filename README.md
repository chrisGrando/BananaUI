# BananaUI 🍌

**BananaUI** is a modern, high-performance desktop application built in Python for generating and editing images with Google's **NanoBanana** models powered by the **Gemini API**. It features an elegant dark-themed graphical interface, non-blocking asynchronous generation, support for up to eight multimodal image reference attachments, dynamic form validation, and integrated output preview management.

BananaUI runs seamlessly on **Windows** and **Linux** (x86_64), offering automated offline setup routines and standalone packaging scripts powered by **PyPy 3.11** for lightning-fast execution.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported NanoBanana Models](#supported-nanobanana-models)
- [Application Architecture](#application-architecture)
  - [Repository Structure](#repository-structure)
  - [Detailed Component Breakdown](#detailed-component-breakdown)
- [Getting Started](#getting-started)
  - [System Requirements & Prerequisites](#system-requirements--prerequisites)
  - [Setup & Execution on Windows](#setup--execution-on-windows)
  - [Setup & Execution on Linux](#setup--execution-on-linux)
  - [Manual & Cross-Platform Setup](#manual--cross-platform-setup)
- [Standalone Packaging & Distribution](#standalone-packaging--distribution)
  - [Building for Windows (Portable EXE)](#building-for-windows-portable-exe)
  - [Building for Linux (Portable App & Runtime)](#building-for-linux-portable-app--runtime)
- [Environment Configuration](#environment-configuration)
- [Usage Guide](#usage-guide)
- [Output Management & Naming Convention](#output-management--naming-convention)
- [Error Handling & Diagnostics](#error-handling--diagnostics)

---

## Overview

BananaUI provides an intuitive studio workspace for creative prompting, multimodal image editing, and instant visual verification without needing heavy external dependencies or complicated command-line setups. By communicating directly with the Gemini API via optimized standard library networking (`urllib.request`) and rendering via Tkinter and Pillow, BananaUI achieves rapid startup times, minimal overhead, and full portability—especially when executed under **PyPy 3.11**.

Whether generating brand-new visual concepts from descriptive prompts or performing multimodal editing guided by reference images, BananaUI streamlines the entire generative workflow into a responsive two-column desktop canvas.

---

## Key Features

- **🍌 Multimodal Gemini Image Generation & Editing**:
  - Full support for text-to-image prompts as well as image-to-image / reference-based editing using Gemini's native `inlineData` parts.
  - Automatically handles MIME detection and Base64 conversion for JPEG, PNG, WebP, GIF, and BMP formats.
- **⚡ Asynchronous Non-Blocking Worker Architecture**:
  - Image generation runs in a dedicated background daemon thread (`threading.Thread`), keeping the graphical user interface fluid and responsive at all times.
  - Thread-safe UI synchronization via a task queue (`queue.Queue`) polled on the main event loop every 50ms.
- **🖼️ Up to 8 Multimodal Reference Attachments**:
  - 2-column grid offering 8 independent attachment slots for reference artwork, style targets, or source photos.
  - Generates instant live thumbnail previews and truncated file labels for loaded images.
  - Individual one-click clear (`✕`) controls to remove slots selectively.
- **🎨 Modern Dark Studio UI**:
  - Custom dark theme built on TTK's `clam` engine, featuring high-contrast banana-gold accents (`#FFD21E`), cyan highlights (`#00D2FF`), and card-based panels.
  - Cross-platform typography automatically utilizing native sans-serif fonts: `Segoe UI` (Windows), `Helvetica Neue` (macOS), or `DejaVu Sans` (Linux).
  - Custom styled vertical scrollbars and smooth cross-platform mouse wheel scrolling.
- **🔒 Secure API Key Management**:
  - Masked password entry field (`•`) with a quick visibility toggle button (`👁` / `🔒`).
  - Automatic pre-fill on startup when the `GEMINI_API_KEY` environment variable is detected.
- **✅ Intelligent Dynamic Validation**:
  - The `⚡ GENERATE` action button automatically enables only when all required parameters (API Key, Model selection, and Prompt) are valid and no generation is in progress.
  - Contextual status messages indicate missing prerequisites in real time.
- **🔍 Responsive Image Preview Canvas**:
  - Centered preview canvas that recalculates aspect ratio dynamically with high-quality Lanczos resampling on window resize events.
  - Includes a quick **"View Full Size"** button to open the generated image in the system's default viewer (`os.startfile` / `open` / `xdg-open`).
  - Includes an **"Open Output Folder"** shortcut to inspect output assets directly in the operating system's file explorer.
- **🍌 Procedural Vector Logo Engine**:
  - Automatically generates an anti-aliased, supersampled cybernetic banana logo with glowing radial gradients, circuit traces, and Gemini-style sparkles if assets are missing.
  - Gracefully displays previous generation results or the generated logo as a fallback upon startup.
- **🪟 Windows Desktop Attachment & High-DPI Polish**:
  - Includes `ensure_interactive_desktop` Win32 routines to bind threads to `WinSta0` / `default`, preventing window suppression when invoked from background task runners or automated wrappers.
  - Native window maximization support (`zoomed` / `-zoomed` / full display geometry).
- **📦 Fully Bundled Portable Runtimes**:
  - Includes pre-packaged PyPy 3.11 runtimes for both **Windows** (`.7z`) and **Linux** (`.tar.xz`), enabling zero-configuration offline setup and distribution.

---

## Supported NanoBanana Models

BananaUI includes built-in configurations for Google's NanoBanana image generation and editing models:

| Model Display Name | Model Identifier | Status / Tier | Description |
| :--- | :--- | :--- | :--- |
| **Nano Banana 2.1** | `gemini-nano-banana-2.1` | **Flagship (Current)** | Recommended high-efficiency image generation and multimodal editing model (131k token context, multi-image reference fusion, enhanced rendering). |
| **Nano Banana Pro** | `gemini-3-pro-image` | **Production (Pro)** | Professional high-detail model optimized for precision reasoning and complex visual generation. |
| **Nano Banana 2** | `gemini-3.1-flash-image` | *Legacy (Deprecated)* | Previous-generation high-efficiency model (deprecated in October 2026; upgrade to Nano Banana 2.1 recommended). |
| **Nano Banana 2 Lite** | `gemini-3.1-flash-lite-image` | **Active (Lightweight)** | Ultra-fast lightweight model designed for rapid iterative concepting. |
| **Nano Banana** | `gemini-2.5-flash-image` | *Legacy (Deprecated)* | Original preview model (retained for backward compatibility). |

> [!TIP]
> The model selector starts on `[SELECT A MODEL HERE]` to ensure an explicit model choice before triggering generation. You can also input or pass custom model identifiers supported by the Gemini API endpoint.

---

## Application Architecture

### Repository Structure

```
BananaUI/
├── app/
│   ├── assets/                 # Branding assets and generated application icons
│   │   ├── nanobanana_icon.png
│   │   └── nanobanana_logo.png
│   ├── output/                 # Timestamped output directory for generated pictures
│   ├── api_client.py           # Gemini REST client, base64 encoder, and response parser
│   ├── config.py               # App constants, model registries, paths, and limits
│   ├── exceptions.py           # Custom exception types and persistent error logging
│   ├── logo.py                 # Procedural vector logo generator and Pillow graphics
│   ├── Main.py                 # Application entry point and interactive desktop setup
│   └── ui.py                   # Tkinter GUI, background worker threads, layout, and styling
├── bin/                        # Local environments and exported standalone distributions
│   ├── BananaUI_Linux_x64/     # Standalone portable Linux distribution (created by export script)
│   ├── BananaUI_Win_x64/       # Standalone portable Windows distribution (created by export script)
│   ├── PY_BIN/                 # Local Linux Python/PyPy virtual environment
│   └── pypy/                   # Local Windows PyPy runtime directory
├── powershell/                 # Windows packaging and launcher scripts
│   ├── app_icon.ico            # Windows icon resource for PS2EXE compilation
│   ├── BananaUI.ps1            # Standalone Windows launcher script
│   └── EXPORT_PROJECT_WINDOWS.ps1 # Standalone Windows executable export script
├── utils/                      # Bundled offline archives and binaries
│   ├── 7zr.exe                 # Standalone lightweight 7-Zip executable for Windows
│   ├── pillow-12.3.0-pp311-pypy311_pp80-win_amd64.whl # Pre-compiled Pillow wheel for Windows
│   ├── pypy-3.11-linux.tar.xz  # Bundled PyPy 3.11 runtime archive for Linux x86_64
│   └── pypy-3.11-windows.7z    # Bundled PyPy 3.11 runtime archive for Windows x64
├── EXPORT_PROJECT_LINUX.sh     # Linux portable build packaging script
├── EXPORT_PROJECT_WINDOWS.bat  # Windows build and executable packaging script
├── RUN_PROJECT_LINUX.sh        # Linux launch script using local environment
├── RUN_PROJECT_WINDOWS.bat     # Windows launch script using local PyPy runtime
├── SETUP_PROJECT_LINUX.sh      # Linux initial environment setup script
├── SETUP_PROJECT_WINDOWS.bat   # Windows initial environment extraction and setup script
├── AGENTS.md                   # Agentic guidelines and repository rules
├── LICENSE                     # Software license
└── README.md                   # Project documentation
```

### Detailed Component Breakdown

#### `app/Main.py`
- Serves as the primary execution entry point.
- Cleans up stale `error.log` files from previous sessions.
- Calls `ensure_interactive_desktop()` to guarantee display visibility on Windows before creating the root Tk window.
- Instantiates `BananaUIApp(root)` and starts the Tkinter event loop.

#### `app/ui.py`
- Implements `BananaUIApp`, orchestrating the full graphical experience.
- Implements the two-column interface:
  - **Left Column**: Title header, masked API key entry, model selection combobox, prompt text editor, 8 attachment slots, animated progress bar, real-time status label, and the `⚡ GENERATE` button.
  - **Right Column**: Live preview canvas, status badge, filename label, and quick action launch buttons ("View Full Size" and "Open Output Folder").
- Runs asynchronous generation via `threading.Thread` and routes callbacks back to the main thread via a synchronized `queue.Queue`.
- Manages dynamic preview scaling, window states (`zoomed`), and cross-platform keyboard / mouse bindings.

#### `app/api_client.py`
- Directly interfaces with the Gemini API endpoint (`https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`).
- Constructs payload structures with `responseModalities: ["IMAGE"]`.
- Encodes image attachments into standard `inlineData` Base64 JSON structures.
- Parses responses to extract image bytes, detects safety block reasons (`promptFeedback.blockReason`), and surfaces clear error messages.
- Manages output file writing and retrieves the most recently created image for instant display on startup.

#### `app/config.py`
- Centralized configuration file declaring constants such as `APP_VERSION = "v1.0"`, `MAX_ATTACHMENTS = 8`, and `GEMINI_API_BASE_URL`.
- Maintains the `AVAILABLE_MODELS` list and provides helper functions (`is_proper_model`, `get_model_id_from_display`).
- Resolves and auto-creates the `output/` and `assets/` directories.

#### `app/logo.py`
- Standalone procedural graphics generator using `Pillow` (`PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFilter`).
- Renders an anti-aliased cybernetic banana emblem with radial glow, metallic rims, cyan circuit traces, and four-point Gemini sparkles.
- Serves both as the application window icon and the default placeholder image on the preview canvas.

#### `app/exceptions.py`
- Defines `NanoBananaAPIError`.
- Automatically logs traceback details and error messages to `app/error.log` with formatted separators for debugging and support.

---

## Getting Started

### System Requirements & Prerequisites

- **Operating System**: Windows 10/11, Linux (glibc-based distributions), or macOS.
- **CPU Architecture**: **x86_64** (AMD64).
- **Python Runtime**: **PyPy 3.11** (recommended and pre-bundled in `utils/`) or standard **Python 3.10+**.
- **Dependencies**: `Pillow` (pre-bundled as an offline wheel for Windows; auto-installed during Linux setup).
- **Windows Only**: PowerShell 5.1+ (for packaging/export, the `ps2exe` module is required).
- **Linux Only**: Standard shell tools (`bash`, `tar`, `xz`). Optional GUI dialog tools (`zenity`, `kdialog`, or `xmessage`) for graphical error reporting in the exported launcher.

---

### Setup & Execution on Windows

The repository includes a portable PyPy 3.11 runtime and a pre-compiled Pillow wheel inside the `utils/` directory.

#### 1. Extract and configure the runtime
Double-click or run from Command Prompt / PowerShell:
```cmd
SETUP_PROJECT_WINDOWS.bat
```
*This extracts PyPy into `bin/pypy/` using the bundled 7-Zip utility and installs the local Pillow wheel.*

#### 2. Launch the application
```cmd
RUN_PROJECT_WINDOWS.bat
```
*This verifies the runtime in `bin/pypy/`, sets the session `PATH`, and launches `app/Main.py`.*

---

### Setup & Execution on Linux

#### 1. Configure the local environment
Run from terminal:
```bash
./SETUP_PROJECT_LINUX.sh
```
*This automatically detects system `pypy` or `python3`, generates a virtual environment in `bin/PY_BIN/`, and installs Pillow.*

#### 2. Launch the application
```bash
./RUN_PROJECT_LINUX.sh
```
*This activates `bin/PY_BIN/` and launches `app/Main.py`.*

---

### Manual & Cross-Platform Setup

If you prefer to run BananaUI directly with an existing Python or PyPy installation:

1. **Install Pillow**:
   ```bash
   # Standard Python
   pip install --user pillow
   
   # Or with PyPy
   pypy -m pip install pillow
   ```

2. **Run BananaUI**:
   ```bash
   # Standard Python
   python app/Main.py
   
   # Or with PyPy
   pypy app/Main.py
   ```

---

## Standalone Packaging & Distribution

BananaUI includes comprehensive scripts to export completely standalone, portable distributions with self-contained runtimes ready for deployment on other machines.

### Building for Windows (Portable EXE)

Run:
```cmd
EXPORT_PROJECT_WINDOWS.bat
```

**How it works**:
1. Invokes `powershell/EXPORT_PROJECT_WINDOWS.ps1`.
2. Verifies the `ps2exe` module (install via `Install-Module -Name ps2exe -Scope CurrentUser` if needed).
3. Performs a clean extraction of PyPy from `utils/pypy-3.11-windows.7z` into `bin/BananaUI_Win_x64/runtime/`.
4. Installs the bundled Pillow wheel (`utils/pillow-12.3.0-pp311-pypy311_pp80-win_amd64.whl`).
5. Copies all Python source files and `app/assets/` into `bin/BananaUI_Win_x64/app/`.
6. Compiles `powershell/BananaUI.ps1` into a 64-bit windowed executable (`BananaUI.exe`) embedded with `powershell/app_icon.ico`.

**Resulting Output**:
- Directory: `bin/BananaUI_Win_x64/`
- Launcher: `BananaUI.exe`

---

### Building for Linux (Portable App & Runtime)

Run:
```bash
./EXPORT_PROJECT_LINUX.sh
```
*(Pass `-y` or `--no-pause` for non-interactive / CI execution: `./EXPORT_PROJECT_LINUX.sh --no-pause`)*

**How it works**:
1. Verifies non-root execution.
2. Extracts the bundled offline runtime from `utils/pypy-3.11-linux.tar.xz` into `bin/BananaUI_Linux_x64/runtime/` (or generates a standalone virtual environment if the archive is absent).
3. Bootstraps `pip` via `ensurepip` if needed and installs/verifies Pillow.
4. Copies all application code and assets into `bin/BananaUI_Linux_x64/app/`.
5. Generates the standalone `BananaUI` shell executable (and `BananaUI.sh` symlink) with GUI dialog error handlers (`zenity` / `kdialog` / `xmessage`).

**Resulting Output**:
- Directory: `bin/BananaUI_Linux_x64/`
- Launcher: `./BananaUI` (or `./BananaUI.sh`)

---

## Environment Configuration

BananaUI can automatically read your Gemini API key from the environment on launch:

### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
.\RUN_PROJECT_WINDOWS.bat
```

### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY=your-gemini-api-key
RUN_PROJECT_WINDOWS.bat
```

### Linux
```bash
export GEMINI_API_KEY="your-gemini-api-key"
./RUN_PROJECT_LINUX.sh
```

> [!NOTE]
> You can also enter or paste your API key directly into the application field at any time. The input remains masked (`•`) by default and can be unmasked using the eye toggle (`👁` / `🔒`).

---

## Usage Guide

1. **Enter API Key**: Input your Gemini API key in the password field or ensure `GEMINI_API_KEY` is exported in your environment.
2. **Select Model**: Choose an active model from the dropdown (e.g., `Nano Banana 2.1` for flagship image generation and editing, or `Nano Banana Pro` for intricate detail).
3. **Draft Prompt**: Describe your desired image in detail inside the **Image Prompt** text box.
4. **Attach Reference Images (Optional)**:
   - Click **📁 Select Image** on any of the 8 attachment slots to supply reference pictures, source images for editing, or style guides.
   - Click **✕** on any slot to discard an attachment.
5. **Generate**: Click **⚡ GENERATE** (activated once API Key, Model, and Prompt are populated).
6. **Inspect & Export**:
   - The generated artwork immediately displays in the right preview canvas.
   - Click **🔍 View Full Size** to open the full-resolution file in your default image viewer.
   - Click **📂 Open Output Folder** to reveal the image file inside `app/output/`.

---

## Output Management & Naming Convention

- Generated images are saved automatically to the `app/output/` directory.
- **Naming format**: File names are set to the exact UNIX integer timestamp captured at the moment the **GENERATE** button is clicked:
  ```
  app/output/<timestamp>.png
  app/output/<timestamp>.jpg
  app/output/<timestamp>.webp
  ```
- When BananaUI launches, it automatically checks `app/output/` and displays the most recent image on the preview canvas. If no images exist, it displays the procedural cybernetic banana logo.

---

## Error Handling & Diagnostics

- **Graceful UI Alerts**: In case of rate limits, invalid requests, safety filter blocks (`promptFeedback.blockReason`), or network disconnects, clear dialog messages explain the error.
- **Persistent Diagnostics**: Full traceback logs are recorded automatically in:
  ```
  app/error.log
  ```
  *This file is cleanly purged upon new successful application startups to keep your workspace tidy.*
