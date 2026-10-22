"""Gemini API client for NanoBanana image generation."""
import os
import json
import base64
import mimetypes
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional, Tuple
from config import GEMINI_API_BASE_URL, OUTPUT_DIR
from exceptions import NanoBananaAPIError

def encode_image_file(file_path: str | Path) -> dict:
    """Reads an image file and returns an inlineData part for Gemini API."""
    path = Path(file_path)
    if not path.exists():
        raise NanoBananaAPIError(f"Attachment file not found: {path}")

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        suffix = path.suffix.lower()
        if suffix in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif suffix == ".png":
            mime_type = "image/png"
        elif suffix == ".webp":
            mime_type = "image/webp"
        elif suffix == ".gif":
            mime_type = "image/gif"
        else:
            mime_type = "image/png"

    with open(path, "rb") as f:
        encoded_data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "inlineData": {
            "mimeType": mime_type,
            "data": encoded_data
        }
    }

def generate_nanobanana_image(
    api_key: str,
    model_id: str,
    prompt: str,
    attachment_paths: Optional[List[str]] = None,
    timeout: int = 120
) -> Tuple[bytes, str, Optional[str]]:
    """
    Sends request to Gemini API to generate an image using the specified NanoBanana model.

    Returns:
        Tuple of (image_bytes, mime_type, text_response)
    """
    if not api_key or not api_key.strip():
        raise NanoBananaAPIError("Gemini API key is required.")
    if not prompt or not prompt.strip():
        raise NanoBananaAPIError("Prompt is required.")
    if not model_id or not model_id.strip():
        raise NanoBananaAPIError("NanoBanana model is required.")

    # Prepare contents parts
    parts = []

    # Add text prompt
    parts.append({"text": prompt.strip()})

    # Add optional image attachments
    if attachment_paths:
        for p in attachment_paths:
            if p and os.path.exists(p):
                try:
                    parts.append(encode_image_file(p))
                except Exception as e:
                    raise NanoBananaAPIError(f"Failed to process attachment '{p}': {e}")

    # Construct payload
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }

    url = f"{GEMINI_API_BASE_URL}/{model_id.strip()}:generateContent?key={api_key.strip()}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "BananaUI/1.0"
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}: {e.reason}"
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            if "error" in err_json and "message" in err_json["error"]:
                err_msg = err_json["error"]["message"]
            elif "error" in err_json:
                err_msg = str(err_json["error"])
        except Exception:
            pass
        raise NanoBananaAPIError(f"Gemini API Error: {err_msg}")
    except urllib.error.URLError as e:
        raise NanoBananaAPIError(f"Network Connection Error: {e.reason}")
    except TimeoutError:
        raise NanoBananaAPIError("Request timed out. Please try again.")
    except Exception as e:
        raise NanoBananaAPIError(f"Unexpected error: {str(e)}")

    try:
        res_data = json.loads(response_body)
    except json.JSONDecodeError as e:
        raise NanoBananaAPIError(f"Invalid JSON response from server: {e}")

    # Parse response to extract image bytes
    candidates = res_data.get("candidates", [])
    if not candidates:
        # Check for promptFeedback or safety ratings
        feedback = res_data.get("promptFeedback", {})
        block_reason = feedback.get("blockReason")
        if block_reason:
            raise NanoBananaAPIError(f"Generation blocked by safety filters: {block_reason}")
        raise NanoBananaAPIError("No candidates returned by Gemini API.")

    first_candidate = candidates[0]
    content = first_candidate.get("content", {})
    response_parts = content.get("parts", [])

    image_bytes = None
    mime_type = "image/png"
    text_content = []

    for part in response_parts:
        # Check inlineData
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and "data" in inline:
            b64_data = inline["data"]
            mime_type = inline.get("mimeType", "image/png")
            try:
                image_bytes = base64.b64decode(b64_data)
                break
            except Exception as e:
                raise NanoBananaAPIError(f"Failed to decode returned image: {e}")
        elif "text" in part:
            text_content.append(part["text"])

    if not image_bytes:
        # Check if model returned an explanation or finish reason
        finish_reason = first_candidate.get("finishReason", "UNKNOWN")
        text_str = " ".join(text_content).strip()
        if text_str:
            raise NanoBananaAPIError(f"Model returned text instead of image: '{text_str}' (Reason: {finish_reason})")
        raise NanoBananaAPIError(f"No image was generated. Finish reason: {finish_reason}")

    return image_bytes, mime_type, ("\n".join(text_content) if text_content else None)

def save_generated_image(image_bytes: bytes, timestamp: int, mime_type: str = "image/png") -> Path:
    """
    Saves generated image bytes to the output folder.
    The filename is the exact integer timestamp taken when GENERATE was pressed.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine appropriate extension based on mime_type
    ext = ".png"
    if "jpeg" in mime_type or "jpg" in mime_type:
        ext = ".jpg"
    elif "webp" in mime_type:
        ext = ".webp"

    file_name = f"{timestamp}{ext}"
    output_path = OUTPUT_DIR / file_name

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path

def get_most_recent_output_image() -> Optional[Path]:
    """
    Returns the Path to the most recent image in the output folder,
    or None if the folder is empty or contains no supported images.
    """
    if not OUTPUT_DIR.exists():
        return None

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    image_files = [
        p for p in OUTPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in valid_extensions
    ]
    if not image_files:
        return None

    def sort_key(p: Path):
        try:
            return (int(p.stem), p.stat().st_mtime)
        except ValueError:
            return (0, p.stat().st_mtime)

    image_files.sort(key=sort_key, reverse=True)
    return image_files[0]
