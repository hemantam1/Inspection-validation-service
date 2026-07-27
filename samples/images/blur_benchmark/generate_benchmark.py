import cv2, numpy as np, os, random
from PIL import Image, ImageDraw, ImageFont

random.seed(42); np.random.seed(42)
OUT = "samples/images/blur_benchmark"
CANON = 1024
FSANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FBOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FMONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

def resize_long_edge(bgr, target=CANON):
    h, w = bgr.shape[:2]
    scale = target / max(h, w)
    if scale >= 1.0:
        return bgr.copy()  # downscale-only: never upscale
    return cv2.resize(bgr, (int(round(w*scale)), int(round(h*scale))),
                      interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)

def vol(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())

def blur(bgr, sigma):
    if sigma <= 0: return bgr.copy()
    return cv2.GaussianBlur(bgr, (0, 0), sigmaX=sigma, sigmaY=sigma)

def save(bgr, name):
    cv2.imwrite(os.path.join(OUT, name), bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])

# ---------- synthetic DOCUMENT (dense text, e.g. loan agreement / KYC) ----------
def make_document():
    W, H = 760, 1024
    img = Image.new("RGB", (W, H), (250, 249, 246))
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(FBOLD, 30); body = ImageFont.truetype(FSANS, 17)
    d.text((60, 45), "LOAN AGREEMENT - GOLD LOAN", font=title, fill=(15,15,15))
    d.line((60, 90, W-60, 90), fill=(15,15,15), width=2)
    para = ("This Agreement is made between the Lender and the Borrower for the sanction "
            "of a gold loan against pledged ornaments. The Borrower confirms lawful ownership "
            "of the pledged gold and agrees to the loan-to-value ratio, interest rate and "
            "repayment schedule set out below. All valuation, purity testing and custody "
            "evidence shall be retained in the digital evidence locker for audit.").split()
    y = 115; line = ""
    for w in para*4:
        if d.textlength(line + " " + w, font=body) > W-120:
            d.text((60, y), line, font=body, fill=(25,25,25)); y += 26; line = w
        else: line = (line + " " + w).strip()
        if y > H-70: break
    d.text((60, y+10), line, font=body, fill=(25,25,25))
    return resize_long_edge(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

# ---------- synthetic FORM (fields/table, KYC form) ----------
def make_form():
    W, H = 760, 1024
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    hd = ImageFont.truetype(FBOLD, 26); lab = ImageFont.truetype(FSANS, 18); mono = ImageFont.truetype(FMONO, 18)
    d.text((60, 40), "KYC VERIFICATION FORM", font=hd, fill=(0,0,0))
    d.rectangle((55, 35, W-55, H-40), outline=(0,0,0), width=2)
    fields = [("Full Name","RAMESH KUMAR SHARMA"),("PAN","ABCDE1234F"),
              ("Aadhaar (masked)","XXXX XXXX 7788"),("Loan Account","GL-2026-004521"),
              ("Branch","BARODA - SECTOR 21"),("Sanction Amount","INR 4,50,000"),
              ("LTV Ratio","72%"),("Appraiser ID","EMP-1183")]
    y = 100
    for lbl, val in fields:
        d.text((70, y), lbl+":", font=lab, fill=(0,0,0))
        d.text((320, y), val, font=mono, fill=(0,0,0))
        d.line((70, y+30, W-70, y+30), fill=(180,180,180), width=1)
        y += 52
    # signature box + grid
    d.rectangle((70, y+20, 360, y+130), outline=(0,0,0), width=2)
    d.text((80, y+25), "Signature", font=lab, fill=(120,120,120))
    for gx in range(400, W-70, 45):
        d.line((gx, y+20, gx, y+130), fill=(210,210,210), width=1)
    return resize_long_edge(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))

# ---------- synthetic SERIAL PLATE (asset inspection - engine/chassis no.) ----------
def make_plate():
    W, H = 1024, 620
    base = np.full((H, W, 3), 150, np.uint8)
    base += np.random.randint(-14, 14, (H, W, 3), dtype=np.int16).astype(np.uint8)  # metal grain
    img = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FBOLD, 92); sub = ImageFont.truetype(FMONO, 44)
    d.rounded_rectangle((40,40,W-40,H-40), radius=25, outline=(40,40,40), width=6)
    d.text((90, 120), "ENGINE No.", font=sub, fill=(30,30,30))
    d.text((90, 200), "MH12 AB 1234", font=big, fill=(10,10,10))
    d.text((90, 360), "CHASSIS  MA3ERLF1S00X4471", font=sub, fill=(20,20,20))
    # a few rivets/scratches
    for _ in range(6):
        cx, cy = random.randint(80,W-80), random.randint(80,H-80)
        d.ellipse((cx-6,cy-6,cx+6,cy+6), fill=(90,90,90))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

# ---------- base loader for real photos ----------
def load_real(path):
    return resize_long_edge(cv2.imread(path))

# ===== assemble dataset: (base_img, prefix, scene, [(sigma,label,filename), ...]) =====
SHARP, SLIGHT, MOD, HEAVY = 0.0, 1.2, 2.6, 5.5
docs = {"document": make_document(), "form": make_form(), "plate": make_plate()}
baroda = load_real("samples/images/current.jpg")
boa    = load_real("samples/images/reference_different.jpg")
tree   = load_real("samples/images/test.jpg")

jobs = [
 (baroda,"bank_baroda","Outdoor - bank branch storefront (real photo)",
    [(SHARP,"SHARP","01_bank_baroda_sharp.jpg"),(SLIGHT,"SLIGHT","02_bank_baroda_slight.jpg"),
     (MOD,"MODERATE","03_bank_baroda_moderate.jpg"),(HEAVY,"HEAVY","04_bank_baroda_heavy.jpg")]),
 (boa,"bank_boa","Outdoor - bank branch + ATM signage (real photo)",
    [(SHARP,"SHARP","05_bank_boa_sharp.jpg"),(SLIGHT,"SLIGHT","06_bank_boa_slight.jpg"),
     (MOD,"MODERATE","07_bank_boa_moderate.jpg")]),
 (tree,"tree","Outdoor - high-detail tree silhouette at dusk (real photo)",
    [(SHARP,"SHARP","08_tree_sharp.jpg"),(HEAVY,"HEAVY","09_tree_heavy.jpg")]),
 (docs["document"],"document","Document - dense printed text (synthetic)",
    [(SHARP,"SHARP","10_document_text_sharp.jpg"),(SLIGHT,"SLIGHT","11_document_text_slight.jpg"),
     (MOD,"MODERATE","12_document_text_moderate.jpg"),(HEAVY,"HEAVY","13_document_text_heavy.jpg")]),
 (docs["form"],"form","Document - KYC form with fields/table (synthetic)",
    [(SHARP,"SHARP","14_document_form_sharp.jpg"),(MOD,"MODERATE","15_document_form_moderate.jpg")]),
 (docs["plate"],"plate","Indoor - asset serial/engine number plate (synthetic)",
    [(SHARP,"SHARP","16_serial_plate_sharp.jpg"),(SLIGHT,"SLIGHT","17_serial_plate_slight.jpg"),
     (HEAVY,"HEAVY","18_serial_plate_heavy.jpg")]),
]

rows = []
for base, prefix, scene, variants in jobs:
    for sigma, label, fn in variants:
        im = blur(base, sigma)
        save(im, fn)
        # score the SAVED file (post-JPEG), so this matches exactly what the
        # Blur Validator computes on disk. Saved images are already at canonical
        # resolution, so grayscale VoL here == preprocess_for_blur + VoL.
        s = vol(cv2.imread(os.path.join(OUT, fn)))
        rows.append((fn, label, scene, sigma, s))

print(f"{'file':<34}{'category':<10}{'sigma':>6}{'VoL':>10}")
print("-"*72)
for fn,label,scene,sigma,s in rows:
    print(f"{fn:<34}{label:<10}{sigma:>6.1f}{s:>10.1f}")

print("\n=== VoL by category (VERIFIED) ===")
from collections import defaultdict
byc = defaultdict(list)
for *_, in rows: pass
for fn,label,scene,sigma,s in rows: byc[label].append(s)
for label in ["SHARP","SLIGHT","MODERATE","HEAVY"]:
    v = byc[label]
    print(f"{label:<10} n={len(v)}  min={min(v):8.1f}  max={max(v):8.1f}  mean={sum(v)/len(v):8.1f}")
