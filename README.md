# BananaUI 🍌

**BananaUI** is a modern, high-performance desktop application built in Python for generating and editing images with Google's **NanoBanana** models powered by the **Gemini API**. It features an elegant dark-themed graphical interface, non-blocking asynchronous generation, support for up to eight multimodal image reference attachments, dynamic form validation, and integrated output preview management.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported NanoBanana Models](#supported-nanobanana-models)
- [Application Architecture](#application-architecture)
  - [Module Structure](#module-structure)
  - [Detailed Component Breakdown](#detailed-component-breakdown)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup on Windows (Automated PyPy)](#setup-on-windows-automated-pypy)
  - [Manual / Cross-Platform Setup](#manual--cross-platform-setup)
- [Environment Configuration](#environment-configuration)
- [Usage Guide](#usage-guide)
- [Output Management & Naming Convention](#output-management--naming-convention)
- [Error Handling & Diagnostics](#error-handling--diagnostics)

---

## Overview

BananaUI provides an intuitive studio workspace for creative prompting, multimodal image editing, and instant visual verification without needing heavy external SDKs or complicated command-line setups. By communicating directly with the Gemini API via optimized standard library networking (`urllib.request`) and rendering via Tkinter and Pillow, BananaUI achieves rapid startup times, minimal overhead, and full portability—especially when executed under **PyPy 3.11**.

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
  - Cross-platform typography automatically utilizing native sans-serif fonts: `Segoe UI` (Windows), `Helvetica Neue` (MacOSX), or `DejaVu Sans` (Linux).
  - Custom styled vertical scrollbars and smooth cross-platform mouse wheel scrolling.
- **🔒 Secure API Key Management**:
  - Masked password entry field (`•`) with a quick visibility toggle button (`👁` / `🔒`).
  - Automatic pre-fill on startup when the `GEMINI_API_KEY` environment variable is detected.
- **✅ Intelligent Dynamic Validation**:
  - The `⚡ GENERATE` action button automatically enables only when all required parameters (API Key, Model, and Prompt) are valid and no generation is in progress.
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

---

## Supported NanoBanana Models

BananaUI includes built-in configurations for Google's NanoBanana image generation and editing models:

| Model Display Name | Model Identifier | Description |
| :--- | :--- | :--- |
| **Nano Banana 2.1** | `gemini-nano-banana-2.1` | Latest flagship image generation and multimodal editing model. |
| **Nano Banana Pro** | `gemini-3-pro-image` | Professional model optimized for high-detail rendering and complex reasoning prompts. |
| **Nano Banana 2** | `gemini-3.1-flash-image` | High-efficiency generation model balancing speed and image fidelity. |
| **Nano Banana 2 Lite** | `gemini-3.1-flash-lite-image` | Ultra-fast lightweight model designed for rapid iterations. |
| **Nano Banana** | `gemini-2.5-flash-image` | Original Nano Banana preview model. |

*Note: Custom model identifiers can also be entered directly or parsed via `get_model_id_from_display`.*

---

## Application Architecture

### Module Structure

```
BananaUI/
├── app/
│   ├── assets/                 # Static branding and generated application icons
│   │   ├── nanobanana_icon.png
│   │   └── nanobanana_logo.png
│   ├── output/                 # Timestamped output directory for generated pictures
│   ├── api_client.py           # Gemini REST client, base64 encoder, and response parser
│   ├── config.py               # App constants, model registries, paths, and limits
│   ├── exceptions.py           # Custom exception types and persistent error logging
│   ├── logo.py                 # Procedural vector logo generator and Pillow graphics
│   ├── Main.py                 # Application entry point and interactive desktop setup
│   └── ui.py                   # Tkinter GUI, background threads, layout, and event handlers
├── bin/                        # Local binaries goes here
├── powershell/                 # Windows packaging and launcher scripts
├── utils/                      # Bundled offline archives (7zr, PyPy 3.11, Pillow wheel)
├── EXPORT_PROJECT_LINUX.sh     # Linux portable build packaging script
├── EXPORT_PROJECT_WINDOWS.bat  # Windows build and executable packaging script
├── RUN_PROJECT_LINUX.sh        # Linux launch script using local environment
├── RUN_PROJECT_WINDOWS.bat     # Launch script using local PyPy runtime
├── SETUP_PROJECT_LINUX.sh      # Linux initial environment setup script
├── SETUP_PROJECT_WINDOWS.bat   # Initial environment extraction and setup script
└── README.md                   # Project documentation
```

### Detailed Component Breakdown

#### `app/Main.py`
- Serves as the primary execution entry point.
- Cleans up stale `error.log` files from previous sessions.
- Calls `ensure_interactive_desktop()` to guarantee display visibility on Windows before creating the root Tk window.
- Instantiates `BananaUIApp(root)` and starts the Tkinter event loop.

#### `app/ui.py`
- Contains `BananaUIApp`, orchestrating the full graphical experience.
- Implements the two-column interface:
  - **Left Column**: Title header, API key entry, model selection combobox, prompt text editor, 8 attachment slots, animated progress bar, real-time status label, and the `⚡ GENERATE` button.
  - **Right Column**: Live preview canvas, status badge, filename label, and quick action launch buttons.
- Runs asynchronous generation via `threading.Thread` and routes callbacks back to the main thread via a synchronized `queue.Queue`.
- Manages dynamic preview scaling, window states, and cross-platform keyboard / mouse bindings.

#### `app/api_client.py`
- Directly interfaces with the Gemini API endpoint (`https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`).
- Constructs payload structures with `responseModalities: ["IMAGE"]`.
- Encodes image attachments into standard `inlineData` Base64 JSON structures.
- Parses responses to extract image bytes, detects safety block reasons (`promptFeedback.blockReason`), and surfaces clear error messages.
- Manages output file writing and retrieves the most recently created image for instant display on startup.

#### `app/config.py`
- Centralized configuration file declaring constants such as `APP_VERSION`, `MAX_ATTACHMENTS = 8`, and `GEMINI_API_BASE_URL`.
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

### Prerequisites

- **Windows, MacOSX, or Linux**.
- **x86_64 CPU** (other types of CPUs are **not** supported)
- **PowerShell 5.1** (for Windows OS only)
- **PyPy 3.11** (already *included* for **windows**) or standard **Python 3.10+**.
- **Pillow** (`PIL`) image processing library (already *included* for **windows**).

### Setup on Windows (Automated PyPy)

The repository comes with a portable PyPy runtime and pre-compiled Pillow wheel inside the `utils/` directory.

1. **Extract and configure the runtime**:
   Double-click or run from PowerShell / Command Prompt:
   ```cmd
   SETUP_PROJECT_WINDOWS.bat
   ```
   *This extracts PyPy into `bin/pypy/` using the bundled 7-Zip utility and installs the local Pillow wheel.*

2. **Launch the application**:
   ```cmd
   RUN_PROJECT_WINDOWS.bat
   ```

### Setup on Linux

1. **Configure the environment**:
   ```bash
   ./SETUP_PROJECT_LINUX.sh
   ```
   *This automatically detects PyPy or Python 3, sets up a virtual environment in `bin/PY_BIN/`, and installs Pillow.*

2. **Launch the application**:
   ```bash
   ./RUN_PROJECT_LINUX.sh
   ```

3. **Export portable Linux build**:
   ```bash
   ./EXPORT_PROJECT_LINUX.sh
   ```
   *This packages a standalone portable distribution into `bin/BananaUI_Linux_x64/` with its own isolated runtime and launcher script (`BananaUI`).*

### Manual / Cross-Platform Setup

If running outside the automated Windows scripts:

1. **Install dependencies**:
   ```bash
   python -m pip install pillow
   # or with PyPy:
   pypy -m pip install pillow
   ```

2. **Run BananaUI**:
   ```bash
   python app/Main.py
   # or with PyPy:
   pypy app/Main.py
   ```

---

## Environment Configuration

BananaUI can automatically read your Gemini API key from the environment on launch:

### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
.\RUN_PROJECT_WINDOWS.bat
```

### Windows (Command Prompt)
```cmd
set GEMINI_API_KEY=your-api-key-here
RUN_PROJECT_WINDOWS.bat
```

### Linux / MacOSX
```bash
export GEMINI_API_KEY="your-api-key-here"
python3 app/Main.py
```

*Note: You can also enter or paste your API key directly into the application field at any time.*

---

## Usage Guide

1. **Enter API Key**: Input your Gemini API key in the password field or ensure `GEMINI_API_KEY` is set in your environment.
2. **Select Model**: Choose a model from the dropdown (e.g., `Nano Banana 2.1` for flagship image editing, or `Nano Banana Pro` for intricate high-detail images).
3. **Draft Prompt**: Describe your image in detail inside the **Image Prompt** text box.
4. **Attach Reference Images (Optional)**:
   - Click **📁 Select Image** on any of the 8 attachment slots to supply reference pictures, source images for editing, or style guides.
   - Click **✕** on any slot to discard an attachment.
5. **Generate**: Click **⚡ GENERATE** (activated once required fields are provided).
6. **Inspect & Export**:
   - The generated artwork immediately displays in the right preview canvas.
   - Click **🔍 View Full Size** to open the full-resolution file in your default image viewer.
   - Click **📂 Open Output Folder** to reveal the image file inside `app/output/`.

---

## Output Management & Naming Convention

- Generated images are saved automatically to the `app/output/` directory.
- **Naming format**: File names are set to the exact UNIX integer timestamp captured at the moment the **GENERATE** button is clicked:
  ```
  app/output/<timestamp>.jpg
  app/output/<timestamp>.png
  app/output/<timestamp>.webp
  ```
- When BananaUI launches, it automatically checks `app/output/` and displays the most recent image on the canvas.

---

## Error Handling & Diagnostics

- In case of API rate limits, bad requests, or network failures, user-friendly alert dialogs display the specific cause (e.g., HTTP error codes or Gemini safety block reasons).
- Detailed exception tracebacks are automatically recorded in:
  ```
  app/error.log
  ```
  *This log file is cleanly purged on new successful application startups to prevent clutter.*
