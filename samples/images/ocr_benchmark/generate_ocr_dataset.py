"""
generate_ocr_dataset.py
=======================
Reproducible generator for the OCR benchmark dataset used to test the
Inspection Validation Service's OCR validator (Tesseract + RapidFuzz).

It draws every image locally with PIL / OpenCV (no AI-generated images),
writes a matching <name>.json for each <name>.png, and — when Tesseract is
available — runs the SAME pipeline the validator uses (pytesseract
image_to_data + rapidfuzz.token_sort_ratio on lowercased text) so that
`expectedMatchScore` and `expectedTextMatched` are MEASURED, not invented.

Run:
    python generate_ocr_dataset.py

Notes:
  * Output goes next to this script (samples/images/ocr_benchmark/).
  * Deterministic: fixed random seed.
  * On Windows, set TESSERACT_CMD to tesseract.exe if it is not on PATH,
    e.g.  set TESSERACT_CMD=C:\\Tesseract-OCR\\tesseract.exe
  * Fonts are resolved portably (DejaVu on Linux, Arial/Consolas on Windows,
    Arial on macOS); falls back to PIL's bitmap font if none are found.
"""

import json
import os
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
SEED = 42
# RapidFuzz token_sort_ratio (0-100) threshold used to LABEL expectedTextMatched.
THRESHOLD = 85

random.seed(SEED)
np.random.seed(SEED)

# --------------------------------------------------------------------------- #
# Fonts (portable resolution across OSes)
# --------------------------------------------------------------------------- #
_FONT_CANDIDATES = {
    "sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ],
    "oblique": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "C:/Windows/Fonts/ariali.ttf",
    ],
}


def rfont(style: str, size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES[style]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# --------------------------------------------------------------------------- #
# PIL <-> OpenCV helpers
# --------------------------------------------------------------------------- #
def pil_to_cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def cv_to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


# --------------------------------------------------------------------------- #
# Document renderers  (each returns (PIL image, canonical_text))
# --------------------------------------------------------------------------- #
def render_doc(title, rows, W=1200, H=820, title_sz=54, label_sz=34,
               value_sz=34, bg=(255, 255, 255), fg=(0, 0, 0),
               value_mono=True, underline=True):
    """Generic key/value document (report, invoice, receipt, id, form)."""
    img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)
    tf = rfont("bold", title_sz)
    lf = rfont("sans", label_sz)
    vf = rfont("mono" if value_mono else "sans", value_sz)

    tw = dr.textlength(title, font=tf)
    dr.text(((W - tw) / 2, 40), title, font=tf, fill=fg)
    y0 = 40 + title_sz + 20
    if underline:
        dr.line((80, y0, W - 80, y0), fill=fg, width=3)

    y = y0 + 35
    gap = (H - y - 45) / max(len(rows), 1)
    for label, value in rows:
        dr.text((100, y), f"{label}:", font=lf, fill=fg)
        dr.text((int(W * 0.42), y), str(value), font=vf, fill=fg)
        y += gap

    text = title + " " + " ".join(f"{l}: {v}" for l, v in rows)
    return img, text


def render_table(title, headers, data_rows, W=1200, H=820):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    tf = rfont("bold", 48)
    hf = rfont("bold", 30)
    cf = rfont("mono", 28)
    tw = dr.textlength(title, font=tf)
    dr.text(((W - tw) / 2, 35), title, font=tf, fill=(0, 0, 0))

    ncol = len(headers)
    x0, y0 = 70, 150
    cw = (W - 2 * x0) / ncol
    rh = 70
    nrow = len(data_rows) + 1
    # grid
    for c in range(ncol + 1):
        dr.line((x0 + c * cw, y0, x0 + c * cw, y0 + nrow * rh), fill=(0, 0, 0), width=2)
    for r in range(nrow + 1):
        dr.line((x0, y0 + r * rh, x0 + ncol * cw, y0 + r * rh), fill=(0, 0, 0), width=2)
    # header
    for c, h in enumerate(headers):
        dr.text((x0 + c * cw + 15, y0 + 18), h, font=hf, fill=(0, 0, 0))
    # rows
    for r, row in enumerate(data_rows):
        for c, cell in enumerate(row):
            dr.text((x0 + c * cw + 15, y0 + (r + 1) * rh + 20), str(cell),
                    font=cf, fill=(0, 0, 0))

    text = (title + " " + " ".join(headers) + " " +
            " ".join(" ".join(str(x) for x in row) for row in data_rows))
    return img, text


def render_handwritten(lines, W=1200, H=820):
    """Simulated handwriting: oblique font, per-word rotation + jitter."""
    img = Image.new("RGB", (W, H), (252, 250, 244))
    base = img
    y = 90
    for line in lines:
        x = 90
        for word in line.split():
            f = rfont("oblique", random.randint(34, 42))
            tmp = Image.new("RGBA", (len(word) * 34 + 40, 90), (0, 0, 0, 0))
            td = ImageDraw.Draw(tmp)
            td.text((6, 12), word, font=f, fill=(20, 20, 60, 255))
            tmp = tmp.rotate(random.uniform(-6, 6), expand=True, resample=Image.BICUBIC)
            base.paste(tmp, (x, y + random.randint(-8, 8)), tmp)
            x += int(td.textlength(word, font=f)) + random.randint(22, 40)
        y += 95
    text = " ".join(lines)
    return base, text


def render_symbols(W=1000, H=700):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    f = rfont("mono", 40)
    syms = "!@#$%^&*()_+-=[]{};:'\",.<>/?\\|~`"
    y = 60
    for _ in range(8):
        line = "".join(random.choice(syms) for _ in range(28))
        dr.text((60, y), line, font=f, fill=(0, 0, 0))
        y += 75
    return img, "!@#$%^&*() symbols only no words"


def render_qr(W=900, H=900, caption="SCAN TO VERIFY"):
    """Synthetic QR-like image (finder patterns + random modules) + caption."""
    img = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    n = 29
    m = 22            # module size
    ox = (W - n * m) // 2
    oy = 60
    # random data modules
    for r in range(n):
        for c in range(n):
            if random.random() < 0.5:
                dr.rectangle((ox + c * m, oy + r * m, ox + (c + 1) * m, oy + (r + 1) * m),
                             fill=(0, 0, 0))

    def finder(cx, cy):
        dr.rectangle((cx, cy, cx + 7 * m, cy + 7 * m), fill=(255, 255, 255))
        dr.rectangle((cx, cy, cx + 7 * m, cy + 7 * m), outline=(0, 0, 0), width=m)
        dr.rectangle((cx + 2 * m, cy + 2 * m, cx + 5 * m, cy + 5 * m), fill=(0, 0, 0))

    finder(ox, oy)
    finder(ox + (n - 7) * m, oy)
    finder(ox, oy + (n - 7) * m)
    cf = rfont("sans", 40)
    cw = dr.textlength(caption, font=cf)
    dr.text(((W - cw) / 2, oy + n * m + 25), caption, font=cf, fill=(0, 0, 0))
    return img, caption


def render_blank(W=1200, H=820):
    img = Image.new("RGB", (W, H), (253, 253, 253))
    arr = pil_to_cv(img).astype(np.int16)
    arr += np.random.randint(-2, 3, arr.shape, dtype=np.int16)  # faint paper texture
    return cv_to_pil(np.clip(arr, 0, 255).astype(np.uint8)), "blank page no text"


def render_random_no_text(W=1000, H=700):
    arr = np.random.randint(0, 255, (H, W, 3), dtype=np.uint8)
    arr = cv2.GaussianBlur(arr, (0, 0), 9)
    for _ in range(12):
        p1 = (random.randint(0, W), random.randint(0, H))
        p2 = (random.randint(0, W), random.randint(0, H))
        col = tuple(int(x) for x in np.random.randint(0, 255, 3))
        cv2.rectangle(arr, p1, p2, col, -1)
    return cv_to_pil(arr), "random image no text"


# --------------------------------------------------------------------------- #
# Degradation transforms (operate on a PIL image, return PIL image)
# --------------------------------------------------------------------------- #
def t_blur(img, sigma=1.2):
    return cv_to_pil(cv2.GaussianBlur(pil_to_cv(img), (0, 0), sigma))


def t_jpeg(img, quality=16):
    ok, buf = cv2.imencode(".jpg", pil_to_cv(img), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv_to_pil(cv2.imdecode(buf, cv2.IMREAD_COLOR))


def t_shadow(img):
    cv = pil_to_cv(img).astype(np.float32)
    h, w = cv.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    grad = 0.45 + 0.55 * (1 - (xx / w) * (yy / h))     # darker toward a corner
    cv *= grad[..., None]
    return cv_to_pil(np.clip(cv, 0, 255).astype(np.uint8))


def t_low_contrast(img):
    cv = pil_to_cv(img).astype(np.float32)
    cv = 128 + (cv - 128) * 0.32                        # squeeze toward mid-gray
    return cv_to_pil(np.clip(cv, 0, 255).astype(np.uint8))


def t_noise(img, sigma=22):
    cv = pil_to_cv(img).astype(np.float32)
    cv += np.random.normal(0, sigma, cv.shape)
    return cv_to_pil(np.clip(cv, 0, 255).astype(np.uint8))


def t_perspective(img):
    cv = pil_to_cv(img)
    h, w = cv.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[w * 0.10, h * 0.05], [w * 0.93, h * 0.02],
                      [w * 0.98, h * 0.97], [w * 0.05, h * 0.92]])
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(cv, M, (w, h), borderValue=(255, 255, 255))
    return cv_to_pil(out)


def t_skew(img, angle=8):
    cv = pil_to_cv(img)
    h, w = cv.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    out = cv2.warpAffine(cv, M, (w, h), borderValue=(255, 255, 255))
    return cv_to_pil(out)


def t_rotate90(img):
    return cv_to_pil(cv2.rotate(pil_to_cv(img), cv2.ROTATE_90_CLOCKWISE))


def t_crop(img, keep=0.62):
    cv = pil_to_cv(img)
    h = cv.shape[0]
    return cv_to_pil(cv[: int(h * keep), :])            # bottom rows lost


def t_fold(img):
    cv = pil_to_cv(img).astype(np.float32)
    h, w = cv.shape[:2]
    for frac in (0.5,):
        y = int(h * frac)
        band = 26
        cv[max(0, y - band):y, :] *= 0.72               # crease shadow
        cv[y:min(h, y + band), :] *= 1.12               # highlight
        cv[y:y + 2, :] = 60
    return cv_to_pil(np.clip(cv, 0, 255).astype(np.uint8))


def t_watermark(img, text="CONFIDENTIAL"):
    base = img.convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    f = rfont("bold", 150)
    tw = dr.textlength(text, font=f)
    tmp = Image.new("RGBA", (int(tw) + 40, 220), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((10, 10), text, font=f, fill=(120, 120, 120, 110))
    tmp = tmp.rotate(30, expand=True, resample=Image.BICUBIC)
    layer.paste(tmp, ((base.size[0] - tmp.size[0]) // 2,
                      (base.size[1] - tmp.size[1]) // 2), tmp)
    return Image.alpha_composite(base, layer).convert("RGB")


# --------------------------------------------------------------------------- #
# Canonical content
# --------------------------------------------------------------------------- #
REPORT_V1 = [
    ("Vehicle ID", "MH12AB1234"),
    ("Engine No", "EN987654321"),
    ("Chassis No", "CH123456789"),
    ("Inspector", "John Smith"),
    ("Inspection Date", "29-Jul-2026"),
    ("Status", "APPROVED"),
    ("Reference Code", "OCRTEST2026"),
]
REPORT_V2 = [
    ("Vehicle ID", "KA05CJ7890"),
    ("Engine No", "EN112233445"),
    ("Chassis No", "CH556677889"),
    ("Inspector", "Priya Nair"),
    ("Inspection Date", "12-Aug-2026"),
    ("Status", "REJECTED"),
    ("Reference Code", "REF99887766"),
]


def report_text(rows):
    return "INSPECTION REPORT " + " ".join(f"{l}: {v}" for l, v in rows)


# --------------------------------------------------------------------------- #
# Build the spec list  -> each: dict(name, group, difficulty, notes,
#                                    expected_text, image)
# --------------------------------------------------------------------------- #
def build_specs():
    specs = []

    def add(name, group, difficulty, notes, expected_text, image):
        specs.append(dict(name=name, group=group, difficulty=difficulty,
                          notes=notes, expected_text=expected_text, image=image))

    # base report images reused by transforms
    rep1_img, rep1_txt = render_doc("INSPECTION REPORT", REPORT_V1)
    rep2_img, rep2_txt = render_doc("INSPECTION REPORT", REPORT_V2)

    # ---- 1. Perfect quality ------------------------------------------------
    add("inspection_report_01", "perfect-quality", "easy",
        "Clean inspection report. OCR should read it verbatim.", rep1_txt, rep1_img)
    add("inspection_report_02", "perfect-quality", "easy",
        "Second clean inspection report (different vehicle).", rep2_txt, rep2_img)
    inv_img, inv_txt = render_doc("TAX INVOICE", [
        ("Invoice No", "INV-2026-0442"), ("Date", "29-Jul-2026"),
        ("Vendor", "Sharma Auto Works"), ("GSTIN", "24ABCDE1234F1Z5"),
        ("Item", "Vehicle Inspection Service"), ("Amount", "INR 2500.00"),
        ("Reference Code", "OCRTEST2026")])
    add("invoice_01", "perfect-quality", "easy",
        "Clean tax invoice.", inv_txt, inv_img)
    rec_img, rec_txt = render_doc("PAYMENT RECEIPT", [
        ("Receipt No", "RC-88231"), ("Date", "29-Jul-2026"),
        ("Paid By", "John Smith"), ("Amount", "INR 2500.00"),
        ("Mode", "UPI"), ("Reference Code", "OCRTEST2026")],
        W=760, H=900, title_sz=44)
    add("receipt_01", "perfect-quality", "easy",
        "Clean narrow payment receipt.", rec_txt, rec_img)
    id_img, id_txt = render_doc("FIELD INSPECTOR ID CARD", [
        ("Name", "John Smith"), ("Inspector ID", "EMP-1183"),
        ("Department", "Asset Verification"), ("Valid Till", "31-Dec-2026"),
        ("Reference Code", "OCRTEST2026")], H=640)
    add("id_card_01", "perfect-quality", "easy",
        "Clean ID card.", id_txt, id_img)
    form_img, form_txt = render_doc("KYC VERIFICATION FORM", [
        ("Full Name", "Rakesh Kumar"), ("PAN", "ABCDE4587L"),
        ("Vehicle ID", "MH12AB1234"), ("Inspector", "John Smith"),
        ("Status", "APPROVED"), ("Reference Code", "OCRTEST2026")])
    add("form_01", "perfect-quality", "easy",
        "Clean KYC form.", form_txt, form_img)

    # ---- 2. Slightly noisy -------------------------------------------------
    add("inspection_report_blur_01", "slightly-noisy", "medium",
        "Small Gaussian blur; text still legible.", rep1_txt, t_blur(rep1_img))
    add("inspection_report_jpeg_01", "slightly-noisy", "medium",
        "Heavy JPEG compression artifacts.", rep1_txt, t_jpeg(rep1_img))
    add("inspection_report_shadow_01", "slightly-noisy", "medium",
        "Uneven lighting / corner shadow.", rep1_txt, t_shadow(rep1_img))
    add("inspection_report_lowcontrast_01", "slightly-noisy", "medium",
        "Low contrast (gray text on gray).", rep1_txt, t_low_contrast(rep1_img))
    add("receipt_noisy_01", "slightly-noisy", "medium",
        "Gaussian sensor noise over a receipt.", rec_txt, t_noise(rec_img))

    # ---- 3. Difficult ------------------------------------------------------
    add("inspection_report_perspective_01", "difficult", "hard",
        "Perspective distortion (photographed at an angle).", rep1_txt, t_perspective(rep1_img))
    add("inspection_report_skew_01", "difficult", "hard",
        "Skewed ~8 degrees.", rep1_txt, t_skew(rep1_img, 8))
    add("inspection_report_rotated90_01", "difficult", "hard",
        "Rotated 90 degrees; OCR (psm 6) expected to fail without orientation detection.",
        rep1_txt, t_rotate90(rep1_img))
    add("inspection_report_cropped_01", "difficult", "hard",
        "Partially cropped; lower fields missing.", rep1_txt, t_crop(rep1_img))
    add("inspection_report_folded_01", "difficult", "hard",
        "Folded paper with a crease shadow.", rep1_txt, t_fold(rep1_img))

    # ---- 4. Edge cases -----------------------------------------------------
    add("blank_page_01", "edge-case", "hard",
        "Blank page: no text present. Validator should hit the no-text path.",
        report_text(REPORT_V1), render_blank()[0])
    hw_img, hw_txt = render_handwritten([
        "Vehicle ID MH12AB1234", "Engine No EN987654321",
        "Inspector John Smith", "Status APPROVED"])
    add("handwritten_note_01", "edge-case", "medium",
        "Synthetic pseudo-handwriting proxy: slanted (oblique) print with per-word "
        "rotation/jitter. NOTE: this is still rendered glyphs, so Tesseract reads it "
        "cleanly; it does NOT represent true cursive handwriting (which would score far "
        "lower). Treat as a slant/jitter robustness case, not a real handwriting test.",
        hw_txt, hw_img)
    add("random_no_text_01", "edge-case", "hard",
        "Random shapes/noise, no text. Validator should hit the no-text path.",
        report_text(REPORT_V1), render_random_no_text()[0])
    add("watermark_over_text_01", "edge-case", "medium",
        "Large diagonal watermark over a readable report.", rep1_txt, t_watermark(rep1_img))
    tiny_img, tiny_txt = render_doc("INSPECTION REPORT", REPORT_V1,
                                    title_sz=20, label_sz=13, value_sz=13)
    add("tiny_font_01", "edge-case", "hard",
        "Very small font.", tiny_txt, tiny_img)
    # mixed font sizes
    mix = Image.new("RGB", (1200, 820), (255, 255, 255))
    mdr = ImageDraw.Draw(mix)
    mdr.text((60, 40), "INSPECTION REPORT", font=rfont("bold", 64), fill=(0, 0, 0))
    mrows = REPORT_V1
    sizes = [22, 48, 30, 40, 26, 52, 34]
    yy = 200
    for (l, v), s in zip(mrows, sizes):
        mdr.text((80, yy), f"{l}:", font=rfont("sans", s), fill=(0, 0, 0))
        mdr.text((560, yy), v, font=rfont("mono", s), fill=(0, 0, 0))
        yy += 85
    add("mixed_font_sizes_01", "edge-case", "medium",
        "Mixed font sizes within one document.", report_text(REPORT_V1), mix)
    tbl_img, tbl_txt = render_table(
        "INSPECTION CHECKLIST",
        ["Item", "Result", "Ref"],
        [["Engine", "OK", "EN987654321"],
         ["Chassis", "OK", "CH123456789"],
         ["Brakes", "PASS", "BR-01"],
         ["Lights", "PASS", "LT-02"],
         ["Status", "APPROVED", "OCRTEST2026"]])
    add("multiline_table_01", "edge-case", "medium",
        "Multiline table with rows and columns.", tbl_txt, tbl_img)

    # ---- 5. Negative cases (intentional mismatches) ------------------------
    add("wrong_document_01", "negative", "medium",
        "Image is a DIFFERENT report (V2); expectedText is V1 -> must NOT match.",
        rep1_txt, rep2_img)
    fr_img, _ = render_doc("RAPPORT D'INSPECTION", [
        ("Vehicule", "FR07XY4321"), ("Moteur", "MT445566778"),
        ("Inspecteur", "Pierre Dubois"), ("Date", "05-Sep-2026"),
        ("Statut", "APPROUVE"), ("Code", "FRTEST2026")])
    add("different_language_01", "negative", "hard",
        "French document; expectedText is the English V1 report -> must NOT match.",
        rep1_txt, fr_img)
    sym_img, _ = render_symbols()
    add("symbols_only_01", "negative", "hard",
        "Only symbols/punctuation; expectedText is V1 report -> must NOT match.",
        rep1_txt, sym_img)
    qr_img, _ = render_qr(caption="SCAN TO VERIFY REF OCRTEST2026")
    add("qr_code_01", "negative", "hard",
        "QR code with a tiny caption; expectedText is V1 report -> must NOT match.",
        rep1_txt, qr_img)
    wr_img, _ = render_doc("INSPECTION REPORT", [
        ("Vehicle ID", "TN09ZX5555"), ("Engine No", "EN987654321"),
        ("Chassis No", "CH000000000"), ("Inspector", "John Smith"),
        ("Inspection Date", "29-Jul-2026"), ("Status", "APPROVED"),
        ("Reference Code", "WRONGREF0000")])
    add("wrong_reference_code_01", "negative", "medium",
        "Near-miss: same layout but Vehicle ID / Chassis / Reference Code differ "
        "from expectedText. Threshold-sensitivity probe.", rep1_txt, wr_img)

    return specs


# --------------------------------------------------------------------------- #
# Measurement (same logic as the app's ocr_utils)
# --------------------------------------------------------------------------- #
def get_measurer():
    if os.getenv("OCR_SKIP_MEASURE"):
        return None
    try:
        import pytesseract
        from pytesseract import Output
        from rapidfuzz import fuzz
    except Exception:
        return None
    tcmd = os.getenv("TESSERACT_CMD")
    if tcmd:
        pytesseract.pytesseract.tesseract_cmd = tcmd

    def measure(pil_img, expected_text):
        try:
            data = pytesseract.image_to_data(
                pil_img, lang="eng", config="--oem 3 --psm 6",
                output_type=Output.DICT)
        except Exception:
            return None
        words, confs = [], []
        for t, c in zip(data.get("text", []), data.get("conf", [])):
            tok = (t or "").strip()
            if not tok:
                continue
            try:
                cv = float(c)
            except (TypeError, ValueError):
                continue
            if cv < 0:
                continue
            words.append(tok)
            confs.append(cv)
        extracted = " ".join(words)
        avg = sum(confs) / len(confs) if confs else 0.0
        score = fuzz.token_sort_ratio(expected_text.lower(), extracted.lower())
        return extracted, avg, score

    return measure


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    os.makedirs(OUT, exist_ok=True)
    specs = build_specs()
    measure = get_measurer()
    if measure is None:
        print("WARNING: pytesseract/rapidfuzz unavailable -> writing DESIGN "
              "fallback scores (unmeasured).")

    summary = []
    for spec in specs:
        img_path = os.path.join(OUT, spec["name"] + ".png")
        json_path = os.path.join(OUT, spec["name"] + ".json")
        spec["image"].save(img_path, "PNG")

        measured = measure(spec["image"], spec["expected_text"]) if measure else None
        if measured is not None:
            extracted, avg_conf, score = measured
            match_score = round(float(score), 1)
            matched = bool(score >= THRESHOLD)
            note = (f"{spec['notes']} "
                    f"[measured: OCR conf {avg_conf:.0f}, "
                    f"token_sort_ratio {match_score}]")
        else:
            match_score = None
            matched = spec["group"] not in ("negative",) and spec["difficulty"] != "hard"
            note = spec["notes"] + " [scores unmeasured - Tesseract unavailable]"

        record = {
            "expectedText": spec["expected_text"],
            "expectedMatchScore": match_score,
            "expectedTextMatched": matched,
            "notes": note,
            "category": spec["group"],
            "difficulty": spec["difficulty"],
        }
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, ensure_ascii=False)

        summary.append((spec["name"], spec["group"], spec["difficulty"],
                        match_score, matched))

    # console summary
    print(f"\nGenerated {len(specs)} image+JSON pairs in {OUT}")
    print(f"{'file':<34}{'group':<18}{'diff':<8}{'score':>7}{'matched':>9}")
    print("-" * 78)
    for name, group, diff, score, matched in summary:
        s = "-" if score is None else f"{score:>7.1f}"
        print(f"{name:<34}{group:<18}{diff:<8}{s}{str(matched):>9}")


if __name__ == "__main__":
    main()
