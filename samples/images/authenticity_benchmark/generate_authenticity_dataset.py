"""
generate_authenticity_dataset.py
================================
Reproducible benchmark for the DOCUMENT_AUTHENTICITY_CHECK validator (localized ELA).

Generates authentic documents and realistic tampered variants, entirely with
Pillow (no downloaded images, no AI), and writes a JSON label next to each image.

Design notes that make this a *valid* ELA benchmark (see README):
  * All images are saved as JPEG. ELA is a JPEG technique; storing lossless PNG
    would erase the effect it relies on.
  * Authentic docs are saved once at BASE_QUALITY. Tampered docs edit the
    authentic JPEG and re-save at the SAME quality, so untouched areas stay
    "settled" (low error) while a freshly-pasted region reads as higher error —
    the classic ELA signal.
  * Tamper strength deliberately spans a spectrum (thin-text edits ... textured
    stamps ... different-compression splices) so the measured table shows which
    tamper types the current ELA can and cannot separate. That is the point:
    calibrate ELA_THRESHOLD on real measurements, and see the limits.

Run:
    python generate_authenticity_dataset.py
Deterministic (fixed seed).
"""

import io
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
SEED = 7
BASE_QUALITY = 85          # authentic + tampered final JPEG quality
PATCH_QUALITY = 30         # low quality used for "different compression history" edits

random.seed(SEED)

# --------------------------------------------------------------------------- #
# Portable fonts
# --------------------------------------------------------------------------- #
_FONTS = {
    "bold": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf"],
    "sans": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "C:/Windows/Fonts/arial.ttf", "/Library/Fonts/Arial.ttf"],
    "mono": ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
             "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf"],
}


def font(style, size):
    for p in _FONTS[style]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
W, H = 1000, 720
ROW_Y0, ROW_DY, VAL_X = 175, 95, 470


def render_doc(title, rows, stamp=False):
    """Returns (PIL image, field_boxes). field_boxes[label] = (x, y, w, h) of the
    value cell, so tampers can target a specific field."""
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((60, 45), title, font=font("bold", 44), fill=(0, 0, 0))
    d.line((60, 120, W - 60, 120), fill=(0, 0, 0), width=3)

    boxes = {}
    y = ROW_Y0
    for label, value in rows:
        d.text((80, y), f"{label}:", font=font("bold", 30), fill=(0, 0, 0))
        d.text((VAL_X, y), str(value), font=font("mono", 30), fill=(0, 0, 0))
        boxes[label] = (VAL_X - 5, y - 6, W - VAL_X - 40, 48)
        y += ROW_DY

    if stamp:
        _draw_stamp(d, (W - 240, 150))
        boxes["__stamp__"] = (W - 320, 150, 180, 180)

    return img, boxes


def _draw_stamp(draw, center):
    cx, cy = center
    draw.ellipse((cx - 80, cy - 20, cx + 80, cy + 140), outline=(190, 30, 30), width=7)
    draw.text((cx - 55, cy + 30), "VERIFIED", font=font("bold", 26), fill=(190, 30, 30))
    draw.text((cx - 30, cy + 65), "2026", font=font("bold", 26), fill=(190, 30, 30))


# --------------------------------------------------------------------------- #
# JPEG helpers
# --------------------------------------------------------------------------- #
def save_jpeg(img, name, quality=BASE_QUALITY):
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "JPEG", quality=quality)
    return path


def load_jpeg(name):
    with Image.open(os.path.join(OUT, name)) as im:
        return im.convert("RGB")


def compress_patch(patch, quality=PATCH_QUALITY):
    """Return a patch carrying a *different* JPEG compression history."""
    buf = io.BytesIO()
    patch.convert("RGB").save(buf, "JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# --------------------------------------------------------------------------- #
# Tamper operations (operate on an authentic PIL image, return tampered PIL)
# --------------------------------------------------------------------------- #
def edit_field(img, box, new_text):
    """Thin-text edit: white out a value cell and type a new value (fresh ink)."""
    t = img.copy()
    d = ImageDraw.Draw(t)
    x, y, w, h = box
    d.rectangle((x, y, x + w, y + h), fill=(255, 255, 255))
    d.text((x + 5, y + 6), new_text, font=font("mono", 30), fill=(0, 0, 0))
    return t


def add_stamp(img, center):
    t = img.copy()
    _draw_stamp(ImageDraw.Draw(t), center)
    return t


def remove_stamp(img, box):
    t = img.copy()
    x, y, w, h = box
    ImageDraw.Draw(t).rectangle((x, y, x + w, y + h), fill=(255, 255, 255))
    return t


def replace_signature(img, box):
    t = img.copy()
    d = ImageDraw.Draw(t)
    x, y, w, h = box
    d.rectangle((x, y, x + w, y + h), fill=(255, 255, 255))
    cx, cy = x + 10, y + h // 2
    pts = [(cx + i * 9, cy + int(22 * (0.5 - random.random()))) for i in range(28)]
    d.line(pts, fill=(0, 0, 120), width=4)
    return t


def copy_move(img, src_box, dst_xy):
    """Copy a region and paste it elsewhere (same compression history)."""
    t = img.copy()
    x, y, w, h = src_box
    region = t.crop((x, y, x + w, y + h))
    t.paste(region, dst_xy)
    return t


def splice_from_other(img, dst_xy, patch):
    """Paste a low-quality patch cropped from a *different* document."""
    t = img.copy()
    t.paste(compress_patch(patch), dst_xy)
    return t


def different_compression_edit(img, box, new_text):
    """Edit whose region carries a different JPEG compression history:
    render new text, pre-compress it hard, then paste."""
    x, y, w, h = box
    patch = Image.new("RGB", (w, h), (255, 255, 255))
    ImageDraw.Draw(patch).text((5, 6), new_text, font=font("mono", 30), fill=(0, 0, 0))
    t = img.copy()
    t.paste(compress_patch(patch), (x, y))
    return t


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #
def build():
    specs = []   # (name, image, json_dict)

    def authentic(name, doc_type, img):
        save_jpeg(img, name + ".jpg")
        specs.append((name, {
            "category": "authentic",
            "documentType": doc_type,
            "modification": None,
            "expectedTamperingSuspected": False,
            "expectedRiskFlag": None,
        }))

    def tampered(name, original, tamper_type, modification, img):
        save_jpeg(img, name + ".jpg")
        specs.append((name, {
            "category": "tampered",
            "tamperType": tamper_type,
            "originalImage": original + ".jpg",
            "modification": modification,
            "expectedTamperingSuspected": True,     # ground-truth design intent
            "expectedRiskFlag": "DOCUMENT_FRAUD",
        }))

    # ---- Authentic originals (5 document types) ----
    rep_img, rep_b = render_doc("INSPECTION REPORT", [
        ("Vehicle ID", "MH12AB1234"), ("Inspection Date", "29-Jul-2026"),
        ("Inspector", "John Smith"), ("Status", "APPROVED"),
        ("Reference Code", "OCRTEST2026")])
    inv_img, inv_b = render_doc("TAX INVOICE", [
        ("Invoice No", "INV-2026-0442"), ("Date", "29-Jul-2026"),
        ("Vendor", "Sharma Auto Works"), ("Amount", "INR 2500.00"),
        ("Reference Code", "OCRTEST2026")])
    bank_img, bank_b = render_doc("BANK STATEMENT", [
        ("Account No", "0123456789"), ("Statement Date", "31-Jul-2026"),
        ("Holder", "Rakesh Kumar"), ("Closing Balance", "INR 84,300.00"),
        ("Reference ID", "TXN20260731")])
    kyc_img, kyc_b = render_doc("KYC VERIFICATION FORM", [
        ("Full Name", "Rakesh Kumar"), ("PAN", "ABCDE4587L"),
        ("Date", "29-Jul-2026"), ("Officer", "John Smith"),
        ("Signature", "R Kumar")])
    prop_img, prop_b = render_doc("PROPERTY INSPECTION", [
        ("Property ID", "PL-77-2026"), ("Inspection Date", "29-Jul-2026"),
        ("Inspector", "John Smith"), ("Condition", "GOOD"),
        ("Reference Code", "PROP2026")], stamp=True)   # authentic stamp baked in

    authentic("inspection_report_original", "inspection_report", rep_img)
    authentic("invoice_original", "invoice", inv_img)
    authentic("bank_statement_original", "bank_statement", bank_img)
    authentic("kyc_form_original", "kyc_form", kyc_img)
    authentic("property_inspection_original", "property_inspection", prop_img)

    # reload the saved authentic JPEGs so tampers edit the *compressed* originals
    rep = load_jpeg("inspection_report_original.jpg")
    inv = load_jpeg("invoice_original.jpg")
    bank = load_jpeg("bank_statement_original.jpg")
    kyc = load_jpeg("kyc_form_original.jpg")
    prop = load_jpeg("property_inspection_original.jpg")

    # ---- Tampered variants (12, spanning tamper types) ----
    tampered("inspection_report_tampered_date", "inspection_report_original",
             "edited_date", "Changed inspection date from 29-Jul-2026 to 05-Aug-2026",
             edit_field(rep, rep_b["Inspection Date"], "05-Aug-2026"))
    tampered("invoice_tampered_amount", "invoice_original",
             "changed_amount", "Changed amount from INR 2500.00 to INR 9500.00",
             edit_field(inv, inv_b["Amount"], "INR 9500.00"))
    tampered("inspection_report_tampered_vehicle", "inspection_report_original",
             "modified_vehicle_number", "Changed Vehicle ID from MH12AB1234 to MH12ZX9999",
             edit_field(rep, rep_b["Vehicle ID"], "MH12ZX9999"))
    tampered("kyc_tampered_signature", "kyc_form_original",
             "replaced_signature", "Replaced the signature with a different scribble",
             replace_signature(kyc, kyc_b["Signature"]))
    tampered("property_tampered_addstamp", "inspection_report_original",
             "added_stamp", "Added a fake 'VERIFIED' stamp to an unstamped report",
             add_stamp(rep, (W - 240, 150)))
    tampered("property_tampered_removestamp", "property_inspection_original",
             "removed_stamp", "Removed the genuine verification stamp",
             remove_stamp(prop, prop_b["__stamp__"]))
    tampered("inspection_report_tampered_status", "inspection_report_original",
             "changed_status", "Changed Status from APPROVED to REJECTED",
             edit_field(rep, rep_b["Status"], "REJECTED"))
    tampered("inspection_report_tampered_inspector", "inspection_report_original",
             "changed_inspector", "Changed Inspector from John Smith to A Sharma",
             edit_field(rep, rep_b["Inspector"], "A Sharma"))
    tampered("bank_statement_tampered_refid", "bank_statement_original",
             "edited_reference_id", "Changed Reference ID from TXN20260731 to TXN20260899",
             edit_field(bank, bank_b["Reference ID"], "TXN20260899"))
    tampered("invoice_tampered_copymove", "invoice_original",
             "copy_move", "Copy-pasted the 'Reference Code' cell over the 'Date' cell",
             copy_move(inv, inv_b["Reference Code"], (inv_b["Date"][0], inv_b["Date"][1])))
    tampered("kyc_tampered_splice", "kyc_form_original",
             "spliced_region", "Spliced a PAN value region from another document",
             splice_from_other(kyc, (kyc_b["PAN"][0], kyc_b["PAN"][1]),
                               bank.crop((VAL_X, ROW_Y0, VAL_X + 380, ROW_Y0 + 48))))
    tampered("bank_statement_tampered_recompress", "bank_statement_original",
             "different_compression_history",
             "Edited Closing Balance region pasted with different JPEG compression",
             different_compression_edit(bank, bank_b["Closing Balance"], "INR 999,999.00"))

    return specs


def main():
    os.makedirs(OUT, exist_ok=True)
    specs = build()
    for name, meta in specs:
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
    n_auth = sum(1 for _, m in specs if m["category"] == "authentic")
    n_tamp = len(specs) - n_auth
    print(f"Generated {len(specs)} documents "
          f"({n_auth} authentic, {n_tamp} tampered) in {OUT}")


if __name__ == "__main__":
    main()
