"""User Interface for the NanoBanana Image Generation application."""
import os
import sys
import time
import queue
import threading
import subprocess
from pathlib import Path
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from config import (
    APP_VERSION,
    AVAILABLE_MODELS,
    MODEL_PLACEHOLDER,
    COMBOBOX_MODEL_OPTIONS,
    DEFAULT_MODEL_NAME,
    is_proper_model,
    get_model_id_from_display,
    OUTPUT_DIR,
    MAX_ATTACHMENTS,
    LOGO_PATH,
    ICON_PATH,
    BASE_DIR
)
from logo import get_nanobanana_logo, create_nanobanana_logo
from api_client import (
    generate_nanobanana_image,
    save_generated_image,
    get_most_recent_output_image,
)
from exceptions import NanoBananaAPIError


def _get_platform_font_family() -> str:
    """Returns the preferred sans-serif UI font family for the current platform.

    - Windows: 'Segoe UI'
    - macOS:   'Helvetica Neue'
    - Linux:   'DejaVu Sans'

    Falls back to the Tk built-in 'TkDefaultFont' if none of the above are
    available on the system.
    """
    if sys.platform == "win32":
        return "Segoe UI"
    elif sys.platform == "darwin":
        return "Helvetica Neue"
    else:
        return "DejaVu Sans"


# Resolved once at import time so every widget uses the same family.
PLATFORM_FONT = _get_platform_font_family()


def ensure_interactive_desktop():
    """
    Ensures the calling thread is attached to the visible interactive user desktop ('default'
    on window station 'WinSta0') on Windows. This bypasses window suppression when launched
    from background tools, services, or runners that create processes on hidden desktops.
    MUST be called before any Tkinter / GUI root window is initialized.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # 1. Ensure connected to interactive Window Station 'WinSta0'
        h_winsta = user32.GetProcessWindowStation()
        if h_winsta:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetUserObjectInformationW(h_winsta, 2, buf, 256, None)
            if buf.value.lower() != "winsta0":
                WINSTA_ALL = 0x037F
                hwinsta = user32.OpenWindowStationW("WinSta0", False, WINSTA_ALL)
                if hwinsta:
                    user32.SetProcessWindowStation(hwinsta)

        # 2. Ensure Thread Desktop is set to 'default' (interactive desktop)
        tid = kernel32.GetCurrentThreadId()
        h_desk = user32.GetThreadDesktop(tid)
        if h_desk:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetUserObjectInformationW(h_desk, 2, buf, 256, None)
            if buf.value.lower() != "default":
                DESKTOP_ALL = 0x01FF
                hdesk = user32.OpenDesktopW("default", 0, False, DESKTOP_ALL)
                if hdesk:
                    user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def force_window_visible(root: tk.Tk):
    """
    Bypasses window suppression flags (such as SW_HIDE or CREATE_NO_WINDOW inherited
    from parent background runners). Forces the Tkinter window to unhide, display,
    and bring itself to the foreground.
    """
    try:
        root.update_idletasks()
        root.deiconify()

        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32

            client_hwnd = root.winfo_id()
            top_hwnd = user32.GetParent(client_hwnd) or client_hwnd

            # SW_SHOW = 5, SW_MAXIMIZE = 3
            SW_SHOW = 5
            SW_MAXIMIZE = 3
            try:
                state = root.state()
                if state == "zoomed":
                    user32.ShowWindow(top_hwnd, SW_MAXIMIZE)
                else:
                    user32.ShowWindow(top_hwnd, SW_SHOW)
            except Exception:
                user32.ShowWindow(top_hwnd, SW_SHOW)

            user32.BringWindowToTop(top_hwnd)
            user32.SetForegroundWindow(top_hwnd)

        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.after_idle(lambda: root.attributes("-topmost", False))
    except Exception:
        pass


# Ensure interactive desktop is attached at module load time as early as possible
ensure_interactive_desktop()


class BananaUIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.app_version = APP_VERSION
        self.root.title(f"NanoBanana - Gemini Image Generator - {self.app_version}")
        self.root.geometry("1140x760")
        self.root.minsize(980, 680)

        # Start application in maximized window mode
        # - Windows: state("zoomed") is natively supported.
        # - Linux (X11/Wayland): the "-zoomed" attribute works on most WMs.
        # - macOS (Aqua): neither works reliably; fill the screen via geometry.
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                try:
                    # macOS / generic fallback: resize to fill the screen
                    sw = self.root.winfo_screenwidth()
                    sh = self.root.winfo_screenheight()
                    self.root.geometry(f"{sw}x{sh}+0+0")
                except Exception:
                    pass

        # State variables
        self.task_queue = queue.Queue()
        self.is_generating = False
        self.attachment_paths: List[Optional[str]] = [None] * MAX_ATTACHMENTS
        self.attachment_widgets = []
        self.last_saved_path: Optional[Path] = None
        self.current_preview_pil: Optional[Image.Image] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None

        # Start thread-safe queue polling
        self._poll_task_queue()

        # Theme Colors
        self.COLOR_BG = "#13161C"
        self.COLOR_PANEL = "#1C2029"
        self.COLOR_CARD = "#232834"
        self.COLOR_INPUT_BG = "#2A303E"
        self.COLOR_BORDER = "#353D4F"
        self.COLOR_TEXT = "#F3F5F9"
        self.COLOR_TEXT_MUTED = "#939FB1"
        self.COLOR_ACCENT = "#FFD21E"       # Banana Gold
        self.COLOR_ACCENT_HOVER = "#FFE050"
        self.COLOR_CYAN = "#00D2FF"         # Nano Cyan
        self.COLOR_BTN_DISABLED = "#323846"
        self.COLOR_TEXT_DISABLED = "#5E687A"
        self.COLOR_SUCCESS = "#22C55E"
        self.COLOR_ERROR = "#EF4444"

        self.root.configure(bg=self.COLOR_BG)

        # Set window icon if possible
        self._set_app_icon()

        # Configure custom TTK styles
        self._setup_styles()

        # Build UI Layout
        self._build_layout()

        # Check environment variable on startup once and pre-fill API key if set and non-empty
        self._initialize_api_key_from_env()

        # Initialize image preview on startup: most recent image in output folder if present, else logo
        self._initialize_preview_on_startup()

        # Initial check to set GENERATE button state (DISABLED initially until required fields are filled)
        self.update_generate_button_state()

        # Force window to be unhidden, brought to foreground, and displayed on user desktop
        force_window_visible(self.root)
        self.root.after(150, lambda: force_window_visible(self.root))

    def _set_app_icon(self):
        """Sets window icon to NanoBanana icon or logo if available."""
        try:
            # Generates a new logo if file doesn't exists
            icon_img = None
            if not ICON_PATH.exists():
                if not LOGO_PATH.exists():
                    create_nanobanana_logo(128)
                icon_img = Image.open(LOGO_PATH)
            else:
                icon_img = Image.open(ICON_PATH)
            icon_photo = ImageTk.PhotoImage(icon_img)
            self.root.iconphoto(True, icon_photo)
            # Keep reference to avoid garbage collection
            self._icon_photo_ref = icon_photo
        except Exception:
            pass

    def _setup_styles(self):
        """Configure ttk styles for clean modern widgets."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Ensure dropdown popdown Listbox default cursor is hand2 (clickable style)
        self.root.option_add("*Toplevel*Listbox.cursor", "hand2")
        self.root.option_add("*Listbox.cursor", "hand2")
        self.root.option_add("*ComboboxListbox*cursor", "hand2")

        # Prevent ttk::combobox::Motion from wiping custom cursor on readonly comboboxes
        try:
            self.root.tk.eval('''
                proc ttk::combobox::Motion {w x y} {
                    if {[$w instate {!readonly !disabled}]} {
                        if {[$w identify $x $y] eq "textarea"} {
                            ttk::setCursor $w text
                        } else {
                            ttk::setCursor $w ""
                        }
                    } else {
                        if {[$w cget -cursor] eq ""} {
                            ttk::setCursor $w ""
                        }
                    }
                }
            ''')
        except Exception:
            pass

        # Combobox styling
        self.style.configure(
            "TCombobox",
            fieldbackground=self.COLOR_INPUT_BG,
            background=self.COLOR_CARD,
            foreground=self.COLOR_TEXT,
            arrowcolor=self.COLOR_ACCENT,
            bordercolor=self.COLOR_BORDER,
            darkcolor=self.COLOR_BORDER,
            lightcolor=self.COLOR_BORDER,
            cursor="hand2",
            padding=6
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.COLOR_INPUT_BG), ("focus", self.COLOR_INPUT_BG)],
            foreground=[("readonly", self.COLOR_TEXT), ("focus", self.COLOR_TEXT)],
            cursor=[("readonly", "hand2")]
        )

        # Progressbar styling
        self.style.configure(
            "Banana.Horizontal.TProgressbar",
            troughcolor=self.COLOR_INPUT_BG,
            bordercolor=self.COLOR_BORDER,
            background=self.COLOR_ACCENT,
            lightcolor=self.COLOR_ACCENT,
            darkcolor=self.COLOR_ACCENT
        )

        # Custom Scrollbar styling matching the modern dark UI theme
        self.style.configure(
            "Banana.Vertical.TScrollbar",
            troughcolor=self.COLOR_CARD,
            background=self.COLOR_BORDER,
            bordercolor=self.COLOR_PANEL,
            darkcolor=self.COLOR_BORDER,
            lightcolor=self.COLOR_BORDER,
            arrowcolor=self.COLOR_TEXT_MUTED,
            arrowsize=11,
            gripcount=0,
            width=12
        )
        self.style.map(
            "Banana.Vertical.TScrollbar",
            background=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            darkcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            lightcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            arrowcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)]
        )

        # Apply to standard Vertical.TScrollbar as well
        self.style.configure(
            "Vertical.TScrollbar",
            troughcolor=self.COLOR_CARD,
            background=self.COLOR_BORDER,
            bordercolor=self.COLOR_PANEL,
            darkcolor=self.COLOR_BORDER,
            lightcolor=self.COLOR_BORDER,
            arrowcolor=self.COLOR_TEXT_MUTED,
            arrowsize=11,
            gripcount=0,
            width=12
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            darkcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            lightcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)],
            arrowcolor=[("pressed", self.COLOR_ACCENT_HOVER), ("active", self.COLOR_ACCENT)]
        )

    def _build_layout(self):
        """Creates the two-column main interface."""
        # Main split container
        self.main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Left Column: Inputs & Controls (Scrollable or fixed width)
        self.left_frame = tk.Frame(self.main_container, bg=self.COLOR_PANEL, width=550)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 8))
        self.left_frame.pack_propagate(False)

        # Right Column: Image Preview Area
        self.right_frame = tk.Frame(self.main_container, bg=self.COLOR_PANEL)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Build each column's contents
        self._build_left_controls()
        self._build_right_preview()

    def _build_left_controls(self):
        """Populates the left controls column."""
        # Top banner / Title
        title_frame = tk.Frame(self.left_frame, bg=self.COLOR_PANEL)
        title_frame.pack(fill=tk.X, padx=18, pady=(16, 12))

        title_label = tk.Label(
            title_frame,
            text="🍌 NanoBanana Studio",
            font=(PLATFORM_FONT, 16, "bold"),
            fg=self.COLOR_ACCENT,
            bg=self.COLOR_PANEL
        )
        title_label.pack(side=tk.LEFT)

        version_label = tk.Label(
            title_frame,
            text=self.app_version,
            font=(PLATFORM_FONT, 9, "bold"),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_CARD,
            padx=6,
            pady=2
        )
        version_label.pack(side=tk.LEFT, padx=(8, 0))

        badge_label = tk.Label(
            title_frame,
            text="Powered by Gemini",
            font=(PLATFORM_FONT, 9, "bold"),
            fg=self.COLOR_CYAN,
            bg=self.COLOR_CARD,
            padx=8,
            pady=2
        )
        badge_label.pack(side=tk.RIGHT)

        # Separator line
        sep = tk.Frame(self.left_frame, bg=self.COLOR_BORDER, height=1)
        sep.pack(fill=tk.X, padx=18, pady=(0, 5))

        # Bottom panel for action controls (Generate button & status text)
        # Positioned at bottom left of screen, always visible regardless of scrollbar position
        self.bottom_panel = tk.Frame(self.left_frame, bg=self.COLOR_PANEL)
        self.bottom_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(0, 14))

        bottom_sep = tk.Frame(self.left_frame, bg=self.COLOR_BORDER, height=1)
        bottom_sep.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(0, 12))

        # Scrollable container for middle controls
        scroll_frame = tk.Frame(self.left_frame, bg=self.COLOR_PANEL)
        scroll_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_frame, bg=self.COLOR_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", style="Banana.Vertical.TScrollbar", command=canvas.yview)
        self.scroll_content = tk.Frame(canvas, bg=self.COLOR_PANEL)

        self.scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        
        # Keep width matched to canvas
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(18, 0), pady=(0, 6))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 7), pady=(0, 6))

        # Enable mousewheel scrolling (cross-platform)
        # Windows / macOS: <MouseWheel> with event.delta
        # Linux X11:       <Button-4> (scroll up) and <Button-5> (scroll down)
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                # macOS delta is already in single-line units (no /120 needed)
                canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                # Windows: delta is typically ±120 per notch
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_up_linux(event):
            canvas.yview_scroll(-1, "units")

        def _on_mousewheel_down_linux(event):
            canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        if sys.platform == "linux":
            canvas.bind_all("<Button-4>", _on_mousewheel_up_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_down_linux)

        content = self.scroll_content

        # -------------------------------------------------------------
        # 1. API KEY FIELD (Required)
        # -------------------------------------------------------------
        api_header_frame = tk.Frame(content, bg=self.COLOR_PANEL)
        api_header_frame.pack(fill=tk.X, pady=(4, 4))

        api_label = tk.Label(
            api_header_frame,
            text="Gemini API Key *",
            font=(PLATFORM_FONT, 10, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_PANEL
        )
        api_label.pack(side=tk.LEFT)

        api_req_hint = tk.Label(
            api_header_frame,
            text="(Required)",
            font=(PLATFORM_FONT, 8),
            fg=self.COLOR_ACCENT,
            bg=self.COLOR_PANEL
        )
        api_req_hint.pack(side=tk.LEFT, padx=6)

        # API Key input frame
        api_input_frame = tk.Frame(content, bg=self.COLOR_INPUT_BG, highlightbackground=self.COLOR_BORDER, highlightthickness=1)
        api_input_frame.pack(fill=tk.X, pady=(0, 12))

        self.api_key_var = tk.StringVar()

        self.api_key_entry = tk.Entry(
            api_input_frame,
            textvariable=self.api_key_var,
            show="•",
            font=(PLATFORM_FONT, 10),
            bg=self.COLOR_INPUT_BG,
            fg=self.COLOR_TEXT,
            insertbackground=self.COLOR_ACCENT,
            relief=tk.FLAT,
            bd=0
        )
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=7)

        # Visibility toggle button (Eye)
        self.show_key_var = tk.BooleanVar(value=False)
        self.toggle_eye_btn = tk.Button(
            api_input_frame,
            text="👁",
            font=(PLATFORM_FONT, 9),
            bg=self.COLOR_INPUT_BG,
            fg=self.COLOR_TEXT_MUTED,
            activebackground=self.COLOR_CARD,
            activeforeground=self.COLOR_TEXT,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._toggle_api_key_visibility
        )
        self.toggle_eye_btn.pack(side=tk.RIGHT, padx=6)

        # Real-time listener for API key
        self.api_key_var.trace_add("write", lambda *args: self.update_generate_button_state())
        self.api_key_entry.bind("<KeyRelease>", lambda e: self.update_generate_button_state())

        # -------------------------------------------------------------
        # 2. MODEL SELECTION COMBOBOX (Required)
        # -------------------------------------------------------------
        model_header_frame = tk.Frame(content, bg=self.COLOR_PANEL)
        model_header_frame.pack(fill=tk.X, pady=(2, 4))

        model_label = tk.Label(
            model_header_frame,
            text="NanoBanana Model *",
            font=(PLATFORM_FONT, 10, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_PANEL
        )
        model_label.pack(side=tk.LEFT)

        model_hint = tk.Label(
            model_header_frame,
            text="(Select a model to enable generation)",
            font=(PLATFORM_FONT, 8),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_PANEL
        )
        model_hint.pack(side=tk.LEFT, padx=6)

        self.model_var = tk.StringVar(value=DEFAULT_MODEL_NAME)
        model_names = COMBOBOX_MODEL_OPTIONS

        self.model_combobox = ttk.Combobox(
            content,
            textvariable=self.model_var,
            values=model_names,
            state="readonly",
            style="TCombobox",
            cursor="hand2",
            postcommand=self._on_model_combobox_post,
            font=(PLATFORM_FONT, 9)
        )
        self.model_combobox.pack(fill=tk.X, pady=(0, 12))
        self.model_combobox.bind("<Enter>", lambda e: self.model_combobox.configure(cursor="hand2"))
        self.model_combobox.bind("<Motion>", lambda e: "break")
        self.model_combobox.bind("<<ComboboxSelected>>", self._on_model_selected)
        self.model_var.trace_add("write", lambda *args: self.update_generate_button_state())
        self._on_model_combobox_post()

        # -------------------------------------------------------------
        # 3. PROMPT TEXT BLOCK (Required)
        # -------------------------------------------------------------
        prompt_header_frame = tk.Frame(content, bg=self.COLOR_PANEL)
        prompt_header_frame.pack(fill=tk.X, pady=(2, 4))

        prompt_label = tk.Label(
            prompt_header_frame,
            text="Image Prompt *",
            font=(PLATFORM_FONT, 10, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_PANEL
        )
        prompt_label.pack(side=tk.LEFT)

        prompt_req_hint = tk.Label(
            prompt_header_frame,
            text="(Required - describe your image)",
            font=(PLATFORM_FONT, 8),
            fg=self.COLOR_ACCENT,
            bg=self.COLOR_PANEL
        )
        prompt_req_hint.pack(side=tk.LEFT, padx=6)

        # Large text block
        prompt_container = tk.Frame(content, bg=self.COLOR_INPUT_BG, highlightbackground=self.COLOR_BORDER, highlightthickness=1)
        prompt_container.pack(fill=tk.BOTH, expand=False, pady=(0, 14))

        self.prompt_text = tk.Text(
            prompt_container,
            height=6,
            font=(PLATFORM_FONT, 10),
            bg=self.COLOR_INPUT_BG,
            fg=self.COLOR_TEXT,
            insertbackground=self.COLOR_ACCENT,
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=8
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True)

        # Real-time listener for Prompt text block
        self.prompt_text.bind("<KeyRelease>", lambda e: self.update_generate_button_state())
        self.prompt_text.bind("<<Modified>>", self._on_prompt_modified)

        # -------------------------------------------------------------
        # 4. 8 IMAGE ATTACHMENT FIELDS (Optional)
        # -------------------------------------------------------------
        attach_header_frame = tk.Frame(content, bg=self.COLOR_PANEL)
        attach_header_frame.pack(fill=tk.X, pady=(2, 6))

        attach_label = tk.Label(
            attach_header_frame,
            text="Image Attachments",
            font=(PLATFORM_FONT, 10, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_PANEL
        )
        attach_label.pack(side=tk.LEFT)

        attach_opt_hint = tk.Label(
            attach_header_frame,
            text="(Optional - up to 8 images for editing/reference)",
            font=(PLATFORM_FONT, 8),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_PANEL
        )
        attach_opt_hint.pack(side=tk.LEFT, padx=6)

        # 2x2 Grid for 8 attachment slots
        attach_grid_frame = tk.Frame(content, bg=self.COLOR_PANEL)
        attach_grid_frame.pack(fill=tk.X, pady=(0, 14))

        for col in range(2):
            attach_grid_frame.columnconfigure(col, weight=1, uniform="attach_col")

        for idx in range(MAX_ATTACHMENTS):
            slot_widget = self._create_attachment_slot(attach_grid_frame, idx)
            r = idx // 2
            c = idx % 2
            slot_widget.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            self.attachment_widgets.append(slot_widget)

        # -------------------------------------------------------------
        # 5. GENERATE BUTTON & STATUS (In fixed bottom-left panel)
        # -------------------------------------------------------------
        self.generate_btn = tk.Button(
            self.bottom_panel,
            text="⚡ GENERATE",
            font=(PLATFORM_FONT, 12, "bold"),
            bg=self.COLOR_ACCENT,
            fg="#0F1115",
            activebackground=self.COLOR_ACCENT_HOVER,
            activeforeground="#000000",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            command=self.on_generate_clicked
        )
        self.generate_btn.pack(fill=tk.X)

        # Status and progress bar
        self.progress_bar = ttk.Progressbar(
            self.bottom_panel,
            orient="horizontal",
            mode="indeterminate",
            style="Banana.Horizontal.TProgressbar"
        )
        # Not packed initially, packed when generating

        self.status_label = tk.Label(
            self.bottom_panel,
            text="Fill in API Key, Model, and Prompt to generate",
            font=(PLATFORM_FONT, 9),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_PANEL,
            wraplength=480,
            justify=tk.LEFT
        )
        self.status_label.pack(fill=tk.X, pady=(8, 2))

    def _create_attachment_slot(self, parent, index: int) -> tk.Frame:
        """Creates a single attachment upload card."""
        card = tk.Frame(
            parent,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1,
            padx=6,
            pady=6
        )

        top_bar = tk.Frame(card, bg=self.COLOR_CARD)
        top_bar.pack(fill=tk.X)

        slot_label = tk.Label(
            top_bar,
            text=f"Attachment #{index + 1}",
            font=(PLATFORM_FONT, 8, "bold"),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_CARD
        )
        slot_label.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            top_bar,
            text="✕",
            font=(PLATFORM_FONT, 8, "bold"),
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT_MUTED,
            activebackground=self.COLOR_INPUT_BG,
            activeforeground=self.COLOR_ERROR,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda i=index: self._clear_attachment(i)
        )
        clear_btn.pack(side=tk.RIGHT)

        # Preview / placeholder box
        thumb_label = tk.Label(
            card,
            text="Empty",
            font=(PLATFORM_FONT, 8),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_INPUT_BG,
            width=18,
            height=9
        )
        thumb_label.pack(fill=tk.X, pady=4)

        # Upload button
        upload_btn = tk.Button(
            card,
            text="📁 Select Image",
            font=(PLATFORM_FONT, 10),
            bg=self.COLOR_INPUT_BG,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_BORDER,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda i=index: self._choose_attachment(i)
        )
        upload_btn.pack(fill=tk.X)

        # Store widget references on card
        card.thumb_label = thumb_label
        card.clear_btn = clear_btn
        card.upload_btn = upload_btn
        card.thumb_image = None
        return card

    def _build_right_preview(self):
        """Builds the right-hand preview panel."""
        header_frame = tk.Frame(self.right_frame, bg=self.COLOR_PANEL)
        header_frame.pack(fill=tk.X, padx=18, pady=(16, 8))

        preview_title = tk.Label(
            header_frame,
            text="Image Preview",
            font=(PLATFORM_FONT, 14, "bold"),
            fg=self.COLOR_TEXT,
            bg=self.COLOR_PANEL
        )
        preview_title.pack(side=tk.LEFT)

        self.preview_badge = tk.Label(
            header_frame,
            text="Logo Preview",
            font=(PLATFORM_FONT, 9),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_CARD,
            padx=8,
            pady=2
        )
        self.preview_badge.pack(side=tk.RIGHT)

        # Canvas container for the image preview
        self.preview_container = tk.Frame(
            self.right_frame,
            bg=self.COLOR_CARD,
            highlightbackground=self.COLOR_BORDER,
            highlightthickness=1
        )
        self.preview_container.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            self.preview_container,
            bg="#0E1015",
            highlightthickness=0
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.preview_canvas.bind("<Configure>", self._on_preview_resize)

        # Preview Footer (Timestamp filename, open button, folder button)
        self.footer_frame = tk.Frame(self.right_frame, bg=self.COLOR_PANEL)
        self.footer_frame.pack(fill=tk.X, padx=18, pady=(0, 14))

        self.filename_label = tk.Label(
            self.footer_frame,
            text="No image generated yet. Showing NanoBanana logo.",
            font=(PLATFORM_FONT, 11),
            fg=self.COLOR_TEXT_MUTED,
            bg=self.COLOR_PANEL,
            anchor="w"
        )
        self.filename_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.open_image_btn = tk.Button(
            self.footer_frame,
            text="🔍 View Full Size",
            font=(PLATFORM_FONT, 9),
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_INPUT_BG,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=8,
            state=tk.DISABLED,
            command=self._open_current_image
        )
        self.open_image_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.open_folder_btn = tk.Button(
            self.footer_frame,
            text="📂 Open Output Folder",
            font=(PLATFORM_FONT, 9),
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_INPUT_BG,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=8,
            command=self._open_output_folder
        )
        self.open_folder_btn.pack(side=tk.RIGHT)

    # -----------------------------------------------------------------
    # Attachment Management
    # -----------------------------------------------------------------
    def _choose_attachment(self, index: int):
        """Opens file dialog for user to select an attachment image."""
        file_path = filedialog.askopenfilename(
            title=f"Select Picture for Attachment #{index + 1}",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self._set_attachment(index, file_path)

    def _set_attachment(self, index: int, file_path: str):
        """Updates slot with selected image and creates a thumbnail."""
        try:
            pil_img = Image.open(file_path)
            pil_img.thumbnail((72, 48), Image.Resampling.LANCZOS)
            thumb_photo = ImageTk.PhotoImage(pil_img)

            card = self.attachment_widgets[index]
            card.thumb_image = thumb_photo  # Keep reference
            card.thumb_label.configure(
                image=thumb_photo,
                text="",
                width=72,
                height=48
            )
            filename = Path(file_path).name
            if len(filename) > 16:
                filename = filename[:13] + "..."
            card.upload_btn.configure(text=filename)

            self.attachment_paths[index] = file_path
        except Exception as e:
            messagebox.showerror("Error Loading Image", f"Could not load image:\n{e}")
            raise NanoBananaAPIError(f"Could not load image:\n{e}")

    def _clear_attachment(self, index: int):
        """Clears the specified attachment slot."""
        self.attachment_paths[index] = None
        card = self.attachment_widgets[index]
        card.thumb_image = None
        card.thumb_label.configure(
            image="",
            text="Empty",
            width=18,
            height=3
        )
        card.upload_btn.configure(text="📁 Select Image")

    # -----------------------------------------------------------------
    # Validation & GENERATE Button State
    # -----------------------------------------------------------------
    def _on_model_combobox_post(self):
        """Ensures the popdown options listbox and scrollbar use clickable hand2 cursor."""
        try:
            pop = self.root.tk.eval(f"ttk::combobox::PopdownWindow {self.model_combobox._w}")
            self.root.tk.eval(f"{pop} configure -cursor hand2")
            self.root.tk.eval(f"{pop}.f configure -cursor hand2")
            self.root.tk.eval(f"{pop}.f.l configure -cursor hand2")
            self.root.tk.eval(f"{pop}.f.sb configure -cursor hand2")
        except Exception:
            pass

    def _on_model_selected(self, event=None):
        """Removes the highlight from the combobox text after an option is chosen and updates state."""
        self.model_combobox.selection_clear()
        try:
            self.model_combobox.after_idle(self.model_combobox.selection_clear)
        except Exception:
            pass
        self.update_generate_button_state()

    def _on_prompt_modified(self, event=None):
        """Called when prompt text is modified."""
        flag = self.prompt_text.edit_modified()
        if flag:
            self.update_generate_button_state()
            self.prompt_text.edit_modified(False)

    def update_generate_button_state(self):
        """
        Dynamically enables/disables the GENERATE button.
        Requirements:
        - Enabled ONLY when every required field has been filled in
          (API Key is not blank, Model is selected, Prompt is not blank)
          AND no image is currently being generated.
        - Disabled otherwise.
        """
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        prompt = self.prompt_text.get("1.0", tk.END).strip()

        has_api_key = bool(api_key)
        has_model = is_proper_model(model)
        has_prompt = bool(prompt)

        can_generate = (
            has_api_key
            and has_model
            and has_prompt
            and not self.is_generating
        )

        if can_generate:
            self.generate_btn.configure(
                state=tk.NORMAL,
                bg=self.COLOR_ACCENT,
                fg="#0F1115",
                cursor="hand2"
            )
            if not self.is_generating:
                self.status_label.configure(
                    text="Ready to generate. Click 'GENERATE' when ready.",
                    fg=self.COLOR_TEXT_MUTED
                )
        else:
            self.generate_btn.configure(
                state=tk.DISABLED,
                bg=self.COLOR_BTN_DISABLED,
                fg=self.COLOR_TEXT_DISABLED,
                cursor="arrow"
            )
            if not self.is_generating:
                missing = []
                if not has_api_key:
                    missing.append("API Key")
                if not has_model:
                    missing.append("Model")
                if not has_prompt:
                    missing.append("Prompt")
                if missing:
                    self.status_label.configure(
                        text=f"Required fields missing: {', '.join(missing)}",
                        fg=self.COLOR_TEXT_MUTED
                    )

    def _toggle_api_key_visibility(self):
        """Toggles masking of the API Key field."""
        if self.show_key_var.get():
            self.api_key_entry.configure(show="•")
            self.toggle_eye_btn.configure(text="👁", fg=self.COLOR_TEXT_MUTED)
            self.show_key_var.set(False)
        else:
            self.api_key_entry.configure(show="")
            self.toggle_eye_btn.configure(text="🔒", fg=self.COLOR_ACCENT)
            self.show_key_var.set(True)

    def _initialize_api_key_from_env(self):
        """
        On application startup, checks if the environment variable 'GEMINI_API_KEY'
        is set and non-empty. If true, automatically fills in the API key field.
        This occurs only once when starting the application.
        """
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key is not None and env_key.strip():
            self.api_key_var.set(env_key.strip())

    # -----------------------------------------------------------------
    # Generation Workflow
    # -----------------------------------------------------------------
    def on_generate_clicked(self):
        """
        Triggered when user clicks GENERATE button.
        NOTE: The output file name for generated images MUST be the
        integer timestamp taken the moment the user pressed the GENERATE button.
        """
        # Exactly capture timestamp at the moment user clicks GENERATE
        timestamp = int(time.time())

        api_key = self.api_key_var.get().strip()
        display_model = self.model_var.get().strip()
        model_id = get_model_id_from_display(display_model)
        prompt = self.prompt_text.get("1.0", tk.END).strip()

        # Collect active attachment file paths
        attachments = [p for p in self.attachment_paths if p and os.path.exists(p)]

        # Set generating state
        self.is_generating = True
        self.update_generate_button_state()

        # UI updates: Show progress bar and update status
        self.progress_bar.pack(fill=tk.X, pady=(6, 2), before=self.status_label)
        self.progress_bar.start(10)
        self.status_label.configure(
            text=f"Generating with {model_id}... Please wait.",
            fg=self.COLOR_CYAN
        )

        # Launch background worker thread so UI remains responsive
        worker = threading.Thread(
            target=self._generation_worker,
            args=(api_key, model_id, prompt, attachments, timestamp),
            daemon=True
        )
        worker.start()

    def _poll_task_queue(self):
        """Processes messages sent from background worker threads on the main GUI thread."""
        try:
            while True:
                callback = self.task_queue.get_nowait()
                try:
                    callback()
                except Exception as e:
                    raise NanoBananaAPIError(f"Error executing callback:\n{e}")
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll_task_queue)

    def _generation_worker(
        self,
        api_key: str,
        model_id: str,
        prompt: str,
        attachments: List[str],
        timestamp: int
    ):
        """Background thread worker that queries Gemini API and saves image."""
        try:
            image_bytes, mime_type, text_note = generate_nanobanana_image(
                api_key=api_key,
                model_id=model_id,
                prompt=prompt,
                attachment_paths=attachments
            )

            # Save image using the exact timestamp captured when GENERATE was pressed
            saved_path = save_generated_image(
                image_bytes=image_bytes,
                timestamp=timestamp,
                mime_type=mime_type
            )

            # Schedule UI update on main thread via thread-safe queue
            self.task_queue.put(
                lambda: self._on_generation_success(saved_path, timestamp, text_note)
            )

        except NanoBananaAPIError as e:
            self.task_queue.put(lambda err=str(e): self._on_generation_error(err))
        except Exception as e:
            self.task_queue.put(lambda err=f"Unexpected error: {str(e)}": self._on_generation_error(err))

    def _on_generation_success(self, saved_path: Path, timestamp: int, text_note: Optional[str]):
        """Runs on main thread when image generation succeeds."""
        self.is_generating = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.update_generate_button_state()

        self.last_saved_path = saved_path
        self.open_image_btn.configure(state=tk.NORMAL)
        self.filename_label.configure(
            text=f"Saved: output/{saved_path.name}",
            fg=self.COLOR_SUCCESS
        )
        self.status_label.configure(
            text=f"✓ Successfully generated! File: {saved_path.name}",
            fg=self.COLOR_SUCCESS
        )
        self.preview_badge.configure(text=f"Generated #{timestamp}", fg=self.COLOR_ACCENT)

        # Load and display the generated image in the preview area
        try:
            img = Image.open(saved_path)
            self._display_preview_image(img)
        except Exception as e:
            messagebox.showwarning("Preview Warning", f"Image saved successfully to {saved_path}, but failed to preview: {e}")
            raise NanoBananaAPIError(f"Image saved successfully to {saved_path}, but failed to preview: {e}")

    def _on_generation_error(self, error_message: str):
        """Runs on main thread when image generation fails."""
        self.is_generating = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.update_generate_button_state()

        self.status_label.configure(
            text=f"Error: {error_message}",
            fg=self.COLOR_ERROR
        )
        messagebox.showerror("NanoBanana Generation Error", error_message)

    # -----------------------------------------------------------------
    # Preview Display & Resizing
    # -----------------------------------------------------------------
    def _initialize_preview_on_startup(self):
        """
        On application startup, checks for the most recent image in the output folder.
        If found, displays it. If no image is available, displays the NanoBanana logo.
        """
        recent_image = get_most_recent_output_image()
        if recent_image and recent_image.exists():
            try:
                img = Image.open(recent_image)
                self.last_saved_path = recent_image
                self.open_image_btn.configure(state=tk.NORMAL)
                self.preview_badge.configure(text=f"Recent: {recent_image.name}", fg=self.COLOR_ACCENT)
                self.filename_label.configure(
                    text=f"Loaded from output/{recent_image.name}",
                    fg=self.COLOR_TEXT_MUTED
                )
                self._display_preview_image(img)
                return
            except Exception:
                pass

        # Fallback to logo if no image available or loading failed
        self._show_nanobanana_logo()

    def _show_nanobanana_logo(self):
        """Displays the NanoBanana logo in the preview area when no image is available."""
        self.last_saved_path = None
        self.open_image_btn.configure(state=tk.DISABLED)
        self.preview_badge.configure(text="NanoBanana Logo", fg=self.COLOR_TEXT_MUTED)
        self.filename_label.configure(
            text="No image available. Showing NanoBanana logo.",
            fg=self.COLOR_TEXT_MUTED
        )
        try:
            logo_img = get_nanobanana_logo((480, 480))
            self._display_preview_image(logo_img)
        except Exception:
            pass

    def _display_preview_image(self, pil_image: Image.Image):
        """Stores the current PIL image and renders it fitted to preview canvas."""
        self.current_preview_pil = pil_image
        self._render_current_preview()

    def _on_preview_resize(self, event=None):
        """Re-renders preview when canvas size changes."""
        self._render_current_preview()

    def _render_current_preview(self):
        """Renders current PIL image to canvas maintaining aspect ratio."""
        if self.current_preview_pil is None:
            return

        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            return

        orig_w, orig_h = self.current_preview_pil.size
        if orig_w == 0 or orig_h == 0:
            return

        # Calculate scaled dimensions preserving aspect ratio
        ratio = min(canvas_w / orig_w, canvas_h / orig_h)
        new_w = max(1, int(orig_w * ratio))
        new_h = max(1, int(orig_h * ratio))

        # Resize PIL image
        resized = self.current_preview_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(resized)

        # Clear and draw centered
        self.preview_canvas.delete("all")
        x = (canvas_w - new_w) // 2
        y = (canvas_h - new_h) // 2
        self.preview_canvas.create_image(x, y, anchor="nw", image=self.preview_photo)

    def _open_current_image(self):
        """Opens the last saved image with the system default viewer."""
        if self.last_saved_path and self.last_saved_path.exists():
            try:
                path_str = str(self.last_saved_path)
                if sys.platform == "win32":
                    os.startfile(path_str)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path_str], check=True)
                else:
                    subprocess.run(["xdg-open", path_str], check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
                raise NanoBananaAPIError(f"Could not open file: {e}")

    def _open_output_folder(self):
        """Opens the output folder in the system file manager."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            path_str = str(OUTPUT_DIR)
            if sys.platform == "win32":
                os.startfile(path_str)
            elif sys.platform == "darwin":
                subprocess.run(["open", path_str], check=True)
            else:
                subprocess.run(["xdg-open", path_str], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            raise NanoBananaAPIError(f"Could not open folder: {e}")
