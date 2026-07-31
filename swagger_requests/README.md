# OCR Benchmark Dataset

A controlled test set for the Inspection Validation Service's **OCR validator**
(Tesseract via `pytesseract` + RapidFuzz `token_sort_ratio`). 28 locally-generated
document images spanning clean → degraded → edge → negative, each paired with a JSON
label file.

---

## ⚠️ Provenance / honesty notes — read first

- **Everything is generated locally with PIL/OpenCV** by `generate_ocr_dataset.py` — no
  AI-generated images, no downloaded photos. Deterministic (seed = 42).
- **`expectedMatchScore` and `expectedTextMatched` are MEASURED, not invented.** The
  generator runs the *same* pipeline the validator uses — `pytesseract.image_to_data`
  (`--oem 3 --psm 6`) then `rapidfuzz.token_sort_ratio(expected.lower(), extracted.lower())`
  — on each generated image and records the real numbers.
- **These baseline numbers were measured on Tesseract 4.1.1 (Linux).** Your Windows
  Tesseract build may differ by a few points. Re-running `generate_ocr_dataset.py` on your
  machine re-measures and **localizes** the JSON scores. Assert against `expectedTextMatched`
  (a boolean) and treat `expectedMatchScore` with a tolerance (±5), or regenerate locally.
- **`handwritten_note_01` is a synthetic proxy** (slanted, jittered *print*), not true
  cursive — Tesseract reads it cleanly, so it's a slant/jitter case, **not** a real
  handwriting test. Its JSON note says so.
- **`expectedText` is exact ground truth** for all content-bearing images. For **negative
  cases** it is deliberately a *different* string than what the image contains, so a correct
  validator must NOT match.

---

## Dataset summary

| Category | Count | Difficulty | Intent |
|----------|:-----:|-----------|--------|
| 1. Perfect quality | 6 | easy | Clean docs — OCR should read verbatim (positive) |
| 2. Slightly noisy | 5 | medium | Blur / JPEG / shadow / low-contrast / noise — should still match |
| 3. Difficult | 5 | hard | Perspective / skew / rotation / crop / fold — stress OCR |
| 4. Edge cases | 7 | mixed | Blank, pseudo-handwriting, no-text, watermark, tiny/mixed fonts, table |
| 5. Negative | 5 | mixed | Wrong doc / other language / symbols / QR / near-miss — must NOT match |
| **Total** | **28** | | |

Each `<name>.png` has a `<name>.json`:

```json
{
  "expectedText": "...",          // ground truth (positive) or intentional mismatch (negative)
  "expectedMatchScore": 100.0,    // measured RapidFuzz token_sort_ratio (0-100)
  "expectedTextMatched": true,    // measured score >= 85 (see threshold below)
  "notes": "... [measured: OCR conf N, token_sort_ratio S]",
  "category": "perfect-quality|slightly-noisy|difficult|edge-case|negative",
  "difficulty": "easy|medium|hard"
}
```

---

## Measured baseline (VERIFIED)

Scores are RapidFuzz `token_sort_ratio` of OCR output vs `expectedText`. `matched` = score ≥ 85.

| File | Category | Diff | Score | Matched |
|------|----------|------|------:|:-------:|
| inspection_report_01 | perfect-quality | easy | 100.0 | ✅ |
| inspection_report_02 | perfect-quality | easy | 100.0 | ✅ |
| invoice_01 | perfect-quality | easy | 93.8 | ✅ |
| receipt_01 | perfect-quality | easy | 90.8 | ✅ |
| id_card_01 | perfect-quality | easy | 100.0 | ✅ |
| form_01 | perfect-quality | easy | 100.0 | ✅ |
| inspection_report_blur_01 | slightly-noisy | medium | 100.0 | ✅ |
| inspection_report_jpeg_01 | slightly-noisy | medium | 100.0 | ✅ |
| inspection_report_shadow_01 | slightly-noisy | medium | 100.0 | ✅ |
| inspection_report_lowcontrast_01 | slightly-noisy | medium | 100.0 | ✅ |
| receipt_noisy_01 | slightly-noisy | medium | 90.8 | ✅ |
| inspection_report_perspective_01 | difficult | hard | 98.1 | ✅ |
| inspection_report_skew_01 | difficult | hard | 84.6 | ❌ |
| inspection_report_rotated90_01 | difficult | hard | 23.3 | ❌ |
| inspection_report_cropped_01 | difficult | hard | 74.7 | ❌ |
| inspection_report_folded_01 | difficult | hard | 93.9 | ✅ |
| blank_page_01 | edge-case | hard | 17.1 | ❌ |
| handwritten_note_01 | edge-case | medium | 100.0 | ✅ |
| random_no_text_01 | edge-case | hard | 0.0 | ❌ |
| watermark_over_text_01 | edge-case | medium | 100.0 | ✅ |
| tiny_font_01 | edge-case | hard | 93.4 | ✅ |
| mixed_font_sizes_01 | edge-case | medium | 100.0 | ✅ |
| multiline_table_01 | edge-case | medium | 34.1 | ❌ |
| wrong_document_01 | negative | medium | 72.7 | ❌ |
| different_language_01 | negative | hard | 49.7 | ❌ |
| symbols_only_01 | negative | hard | 18.0 | ❌ |
| qr_code_01 | negative | hard | 30.7 | ❌ |
| wrong_reference_code_01 | negative | medium | 80.4 | ❌ |

---

## Expected behavior

- **Positives (clean + slightly-noisy + watermark/tiny/mixed fonts):** score 90–100, `matched = true`.
  Tesseract is robust to blur, JPEG, shadow, low contrast, watermark, tiny font and mixed sizes here.
- **Negatives:** all score below the threshold (max negative = 80.4), `matched = false`. A correct
  validator raises the `DOCUMENT_FRAUD` risk flag on these.
- **Realistic OCR failure modes (documented, not bugs):** 90° rotation (23), blank/no-text (0–17),
  a partial crop that loses fields (75), and a **table under `--psm 6`** (34 — column bleed fragments
  the read). These *should* fail the match; they exist to prove the validator degrades gracefully and
  hits its no-text / mismatch paths.
- **Two deliberate threshold probes** sit just under the line: `inspection_report_skew_01` (84.6, a
  positive that a stricter threshold rejects) and `wrong_reference_code_01` (80.4, a near-miss negative).

---

## Recommended threshold

**Use `token_sort_ratio ≥ 85` as the `textMatched` cutoff.**

Evidence from the measured distribution:

- Every document that *should* pass (clean, noisy, watermark, tiny/mixed font, folded, perspective)
  scored **≥ 90.8**.
- The highest **negative** scored **80.4** (`wrong_reference_code_01`).
- So the band **(80.4 → 90.8)** is empty of "should-pass vs must-fail" conflicts, and **85 sits inside
  it** — separating true positives from all negatives.
- Caveat: an **8° skew** scored 84.6 and is rejected at 85. Don't lower the threshold to catch it (that
  would also admit the 80.4 near-miss negative) — instead add a deskew step to preprocessing if skewed
  captures are common.

Pair the match threshold with the OCR **confidence** floor already in the project
(`OCR_MIN_CONFIDENCE = 80`) so low-confidence reads are flagged even if the fuzzy match is high.

> **Action item (separate from this dataset):** `app/core/constants.py` has
> `OCR_MATCH_THRESHOLD = 0.95`, but RapidFuzz `token_sort_ratio` is on a **0–100** scale, so
> `score >= 0.95` is true for almost everything. Set it to **`85`** (this dataset is the evidence).
> Without that fix, every negative above will incorrectly pass.

---

## Testing instructions

**Regenerate the dataset (recreates every image + JSON from scratch, re-measured locally):**

```bash
cd samples/images/ocr_benchmark
# Windows: set TESSERACT_CMD if tesseract.exe is not on PATH
#   set TESSERACT_CMD=C:\Tesseract-OCR\tesseract.exe
python generate_ocr_dataset.py
```

**Drive the OCR validator with the dataset (pytest sketch):**

```python
import json, glob, os
from app.utils.ocr_utils import extract_text, calculate_match_score, is_text_match

THRESHOLD = 85  # RapidFuzz 0-100 scale

for jp in glob.glob("samples/images/ocr_benchmark/*.json"):
    label = json.load(open(jp, encoding="utf-8"))
    img = jp[:-5] + ".png"

    text, conf = extract_text(img)
    score = calculate_match_score(label["expectedText"], text)
    matched = is_text_match(score, THRESHOLD)

    # boolean is stable across machines; score compared with tolerance
    assert matched == label["expectedTextMatched"], f"{img}: matched mismatch"
    if label["expectedMatchScore"] is not None:
        assert abs(score - label["expectedMatchScore"]) <= 5, f"{img}: score drift"
```

Notes:
- Assert on `expectedTextMatched` (stable); allow ±5 on `expectedMatchScore` (Tesseract-version drift),
  or regenerate to localize.
- For short alphanumeric fields (engine/chassis/serial numbers) use `--psm 7`; for tables, `--psm 6`
  fragments columns (see `multiline_table_01`) — `--psm 4`/`11` read tables better if you add that mode.

---

---

## Regression benchmark (`run_ocr_benchmark.py`)

`run_ocr_benchmark.py` (at the **project root**) is the official regression suite for the OCR
validator. It does **not** re-implement any OCR logic — it drives the real validator exactly as the
application does (`ValidatorFactory.get_validator(JobType.OCR_CHECK).validate(request)`), discovers
every `<name>.json` that has a sibling image in this folder, compares the validator's decision against
the label, and reports.

**Run it (from the project root):**

```bash
python run_ocr_benchmark.py
```

It writes three reports into this folder and prints a colored terminal summary:

| File | Contents |
|------|----------|
| `benchmark_report.json` | Full structured result (summary + every sample) |
| `benchmark_report.md` | Human-readable report (summary, category/difficulty tables, FP/FN, worst/best 5) |
| `benchmark_results.csv` | One row per sample, for spreadsheets / dashboards |

**What it measures:** Total / Passed / Failed / Accuracy, Average OCR Confidence, Average Match Score,
category-wise and difficulty-wise accuracy, False Positives, False Negatives, and the worst/best 5 samples.

**Pass criterion:** a sample passes when the validator's `textMatched` equals the label's
`expectedTextMatched`. A sample is a **False Positive** if the validator matched something it should
not have, and a **False Negative** if it missed a match it should have made.

**Exit codes (for CI / GitHub Actions):**

- `0` — every sample passed
- `1` — one or more samples failed, or no samples were found

```yaml
# .github/workflows example step
- name: OCR regression benchmark
  run: python run_ocr_benchmark.py     # fails the job on any regression
```

> **Keep it deterministic on your machine:** the labels are calibrated to the Tesseract build that
> generated them. On a new environment, run `python samples/images/ocr_benchmark/generate_ocr_dataset.py`
> once to re-label against your local Tesseract, then `run_ocr_benchmark.py` will be stable there.
> This suite depends on `constants.OCR_MATCH_THRESHOLD` being on the 0–100 scale (currently `85`) — the
> validator's decision and these labels must use the same threshold.

---

## Files

```
inspection-validation-service/
├── run_ocr_benchmark.py            # regression runner (project root)
└── samples/images/ocr_benchmark/
    ├── generate_ocr_dataset.py     # reproducible generator (source of truth for the data)
    ├── README.md                   # this file
    ├── <name>.png   × 28           # generated images
    ├── <name>.json  × 28           # matching labels
    ├── benchmark_report.json       # written by run_ocr_benchmark.py
    ├── benchmark_report.md         # written by run_ocr_benchmark.py
    └── benchmark_results.csv       # written by run_ocr_benchmark.py
```
