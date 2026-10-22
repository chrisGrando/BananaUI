"""NanoBanana logo generation and image management utilities."""
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import LOGO_PATH, ASSETS_DIR

def create_nanobanana_logo(size: int = 512, save_path: Path = LOGO_PATH) -> Image.Image:
    """
    Programmatically creates a high-quality, professional NanoBanana logo
    with a cybernetic/AI banana, glowing circuit paths, and Gemini sparkles.
    """
    # Create high-res canvas (supersampled x2 for antialiasing)
    canvas_size = size * 2
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = canvas_size // 2
    cy = canvas_size // 2

    # Draw stylish rounded background card / disc with subtle gradient
    radius = int(canvas_size * 0.46)
    
    # Background radial glow
    glow_img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    for r in range(radius + 40, radius - 60, -8):
        alpha = int(45 * (1.0 - (r - (radius - 60)) / 100))
        glow_draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            fill=(255, 200, 30, max(0, min(100, alpha)))
        )
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(glow_img)

    # Base dark container
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=(18, 22, 34, 250),
        outline=(255, 215, 0, 180),
        width=int(6 * 2)
    )

    # Inner decorative tech ring
    inner_ring_r = int(radius * 0.94)
    draw.ellipse(
        (cx - inner_ring_r, cy - inner_ring_r, cx + inner_ring_r, cy + inner_ring_r),
        outline=(0, 229, 255, 90),
        width=int(2 * 2)
    )

    # Draw stylized cyber banana using smooth polygons / arcs
    # Banana body points: crescent shape
    banana_pts = []
    # Outer curve (from stem top to bottom tip)
    outer_steps = 60
    for i in range(outer_steps + 1):
        t = i / outer_steps
        # Angle from ~ 205 deg to 345 deg
        angle = math.radians(195 + t * 145)
        # Variable radius creates banana crescent
        r_outer = radius * 0.65 * (0.92 + 0.16 * math.sin(t * math.pi))
        x = cx + r_outer * math.cos(angle) - 20
        y = cy + r_outer * math.sin(angle) * 0.85 + 20
        banana_pts.append((x, y))

    # Inner curve (from bottom tip back to stem top)
    inner_steps = 60
    for i in range(inner_steps + 1):
        t = 1.0 - (i / inner_steps)
        angle = math.radians(195 + t * 145)
        r_inner = radius * 0.44 * (0.85 + 0.22 * math.sin(t * math.pi))
        x = cx + r_inner * math.cos(angle) - 10
        y = cy + r_inner * math.sin(angle) * 0.78 + 35
        banana_pts.append((x, y))

    # Draw golden banana body
    draw.polygon(banana_pts, fill=(255, 210, 20, 255), outline=(255, 175, 0, 255))

    # Banana highlights (inner shine)
    highlight_pts = []
    for i in range(20, 48):
        t = i / outer_steps
        angle = math.radians(195 + t * 145)
        r_h = radius * 0.58 * (0.92 + 0.16 * math.sin(t * math.pi))
        x = cx + r_h * math.cos(angle) - 18
        y = cy + r_h * math.sin(angle) * 0.83 + 24
        highlight_pts.append((x, y))
    if len(highlight_pts) > 1:
        draw.line(highlight_pts, fill=(255, 250, 160, 220), width=int(5 * 2))

    # Stem and tip accents
    stem_p = banana_pts[0]
    draw.rectangle(
        (stem_p[0] - 12, stem_p[1] - 22, stem_p[0] + 10, stem_p[1] + 6),
        fill=(68, 170, 75, 255),
        outline=(40, 120, 50, 255)
    )
    tip_p = banana_pts[outer_steps]
    draw.ellipse(
        (tip_p[0] - 8, tip_p[1] - 8, tip_p[0] + 8, tip_p[1] + 8),
        fill=(160, 80, 20, 255)
    )

    # Circuit traces across the banana body (Nano theme)
    circuit_pts = [
        (cx - 160, cy - 80),
        (cx - 110, cy - 110),
        (cx - 40, cy - 130),
        (cx + 40, cy - 120),
        (cx + 120, cy - 70),
        (cx + 160, cy + 10)
    ]
    for i in range(len(circuit_pts) - 1):
        p1 = circuit_pts[i]
        p2 = circuit_pts[i + 1]
        draw.line([p1, p2], fill=(0, 229, 255, 230), width=int(2.5 * 2))

    for pt in circuit_pts:
        draw.ellipse((pt[0] - 9, pt[1] - 9, pt[0] + 9, pt[1] + 9), fill=(0, 229, 255, 255))
        draw.ellipse((pt[0] - 4, pt[1] - 4, pt[0] + 4, pt[1] + 4), fill=(255, 255, 255, 255))

    # Gemini-style 4-point AI sparkles
    def draw_sparkle(center_x, center_y, arm_len, color=(255, 255, 255, 255)):
        sp_pts = [
            (center_x, center_y - arm_len),
            (center_x + arm_len * 0.22, center_y - arm_len * 0.22),
            (center_x + arm_len, center_y),
            (center_x + arm_len * 0.22, center_y + arm_len * 0.22),
            (center_x, center_y + arm_len),
            (center_x - arm_len * 0.22, center_y + arm_len * 0.22),
            (center_x - arm_len, center_y),
            (center_x - arm_len * 0.22, center_y - arm_len * 0.22)
        ]
        draw.polygon(sp_pts, fill=color)

    # Several sparkles
    draw_sparkle(cx + 110, cy - 180, int(35 * 2), (255, 255, 255, 255))
    draw_sparkle(cx - 170, cy + 40, int(24 * 2), (0, 229, 255, 230))
    draw_sparkle(cx + 170, cy + 80, int(18 * 2), (255, 220, 50, 240))
    draw_sparkle(cx - 60, cy - 190, int(14 * 2), (255, 255, 255, 200))

    # Typography: "NanoBanana"
    # Fallback to default bitmap or generic truetype font if available
    font_large = None
    font_small = None
    # Cross-platform font candidates:
    #  - Windows: arialbd.ttf, segoeuib.ttf, calibrib.ttf
    #  - macOS:   "Helvetica Bold.ttf", system Helvetica TTC
    #  - Linux:   DejaVuSans-Bold.ttf, LiberationSans-Bold.ttf, FreeSansBold.ttf
    font_candidates_bold = [
        "arialbd.ttf",
        "segoeuib.ttf",
        "calibrib.ttf",
        "Arial Bold.ttf",
        # macOS
        "Helvetica Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        # Linux
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "FreeSansBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    # Corresponding regular (non-bold) variants for subtitle text
    font_candidates_regular = [
        "arial.ttf",
        "segoeui.ttf",
        "calibri.ttf",
        "Arial.ttf",
        # macOS
        "Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        # Linux
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "FreeSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for font_candidate in font_candidates_bold:
        try:
            font_large = ImageFont.truetype(font_candidate, int(32 * 2))
            break
        except Exception:
            continue

    if font_large:
        for font_candidate in font_candidates_regular:
            try:
                font_small = ImageFont.truetype(font_candidate, int(14 * 2))
                break
            except Exception:
                continue

    text_main = "NanoBanana"
    text_sub = "IMAGE GENERATION ENGINE"

    if font_large:
        # Measure and draw centered
        bbox = draw.textbbox((0, 0), text_main, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy + radius * 0.44), text_main, fill=(255, 255, 255, 255), font=font_large)
        if font_small:
            s_bbox = draw.textbbox((0, 0), text_sub, font=font_small)
            sw = s_bbox[2] - s_bbox[0]
            draw.text((cx - sw // 2, cy + radius * 0.59), text_sub, fill=(0, 229, 255, 220), font=font_small)
    else:
        # Simple default rendering
        draw.text((cx - 80, cy + radius * 0.48), text_main, fill=(255, 255, 255, 255))

    # Resize down with high-quality resampling for anti-aliasing
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Save to disk
    save_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(save_path, format="PNG")
    return final_img

def get_nanobanana_logo(target_size: tuple[int, int] = (400, 400)) -> Image.Image:
    """Returns the NanoBanana logo as a PIL Image, creating it if it doesn't exist."""
    if not LOGO_PATH.exists():
        create_nanobanana_logo(size=512)
    try:
        img = Image.open(LOGO_PATH).convert("RGBA")
        return img.resize(target_size, Image.Resampling.LANCZOS)
    except Exception:
        # If open failed, regenerate
        img = create_nanobanana_logo(size=512)
        return img.resize(target_size, Image.Resampling.LANCZOS)

if __name__ == "__main__":
    print(f"Creating logo at {LOGO_PATH}...")
    create_nanobanana_logo(512)
    print("Logo created successfully!")
