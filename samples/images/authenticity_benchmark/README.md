# Document Authenticity Benchmark Dataset

A reproducible benchmark for the `DOCUMENT_AUTHENTICITY_CHECK` validator (localized ELA).
17 documents — 5 authentic originals and 12 realistic tampered variants — each with a JSON
label, generated entirely with Pillow (no downloaded or AI images).

Purpose: **calibrate `ELA_THRESHOLD` and the score weights on real measurements** rather than
guesses — and, just as importantly, find out where ELA's operating envelope actually is.

---

## How it's built (methodology that makes it a valid ELA test)

- **All images are JPEG.** ELA is a JPEG technique; storing lossless PNG would erase the very
  effect it measures.
- **Authentic docs are saved once at quality 85.** Tampered docs edit the authentic JPEG and
  re-save at the *same* quality, so untouched areas stay "settled" (low error) while a fresh
  edit can read as higher error — the classic ELA signal.
- **Tamper strength spans a deliberate spectrum**, from thin single-line text edits to textured
  stamps to different-compression splices, so the table reveals which tamper types ELA can and
  cannot separate.
- Deterministic (fixed seed). Regenerate with `python generate_authenticity_dataset.py`.

Each `<name>.json` holds: `category` (authentic/tampered), `tamperType`, `originalImage`,
`modification` (what was changed), and the ground-truth `expectedTamperingSuspected` /
`expectedRiskFlag`.

---

## VERIFIED measured results (through the real validator)

`ELA_THRESHOLD = 15.0` (current). Localized Error = `elaMeanScore`, Hotspot Contrast = `elaMaxScore`.

| Image | Type | Localized Error | Hotspot Contrast | Score | Tampering Detected |
|-------|------|----------------:|-----------------:|------:|:------------------:|
| bank_statement_original | AUTHENTIC | 1.88 | 1.88 | 91 | False |
| inspection_report_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| invoice_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| kyc_form_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| property_inspection_original | AUTHENTIC | **6.07** | 6.07 | 70 | False |
| bank_statement_tampered_recompress | TAMPERED | 2.08 | 2.08 | 90 | False |
| bank_statement_tampered_refid | TAMPERED | 2.08 | 2.08 | 90 | False |
| inspection_report_tampered_date | TAMPERED | 1.99 | 1.99 | 90 | False |
| inspection_report_tampered_inspector | TAMPERED | 1.99 | 1.99 | 90 | False |
| inspection_report_tampered_status | TAMPERED | 1.97 | 1.97 | 90 | False |
| inspection_report_tampered_vehicle | TAMPERED | 2.01 | 2.01 | 90 | False |
| invoice_tampered_amount | TAMPERED | 2.02 | 2.02 | 90 | False |
| invoice_tampered_copymove | TAMPERED | 2.04 | 2.04 | 90 | False |
| kyc_tampered_signature | TAMPERED | 2.52 | 2.52 | 87 | False |
| kyc_tampered_splice | TAMPERED | 1.95 | 1.95 | 90 | False |
| property_tampered_addstamp | TAMPERED | **6.07** | 6.07 | 70 | False |
| property_tampered_removestamp | TAMPERED | 2.11 | 2.11 | 89 | False |

*(`property_tampered_addstamp` is an inspection report with a fake stamp added — the `property_`
prefix is cosmetic; its `originalImage` is `inspection_report_original.jpg`.)*

---

## What the measurements tell us (the calibration finding)

**There is no `ELA_THRESHOLD` that reliably separates tampered from authentic on this realistic
set.** Concretely:

1. **Thin-text edits are invisible to ELA.** Changed date, amount, vehicle number, status,
   inspector, reference ID, the copy-move, the splice, and the different-compression edit all land
   at **~2.0**, indistinguishable from the authentic originals (~1.83–1.88). Flat document
   backgrounds give ELA almost no signal, and a uniform re-save settles the edit. These are the
   forgeries that matter most, and single-quality ELA cannot see them.

2. **ELA responds to *texture*, not tampering.** The only images that rise (to **6.07**) are the
   ones with a **stamp** — and that includes the *authentic* stamped property document. So the
   forged-stamp document and the genuine-stamp document score identically. ELA cannot tell a
   real stamp from a fake one; it just reacts to the ink/edges.

3. **Because the busiest authentic doc (6.07, genuinely stamped) sits above every tampered doc,
   no threshold separates them.** The runner's calibration step therefore reports
   `suggestedThreshold = None` and zero ELA-separable tampers — the honest, data-backed result.

This is the same conclusion the earlier design review reached in theory, now confirmed with
measurements: **localized ELA is necessary but not sufficient for document authenticity.** It is a
weak signal on flat documents and confounds legitimate texture with edits.

**Recommendation:** do not spend time hand-tuning `ELA_THRESHOLD` — the data shows it can't be made
to work alone here. Keep this dataset as the fixed regression set and re-run the benchmark as V2
signals are added (EXIF/metadata consistency, double-JPEG/quantization analysis, copy-move via
keypoint matching, and cross-checking the OCR text against expected values). Those are what will
actually move the tampered rows away from the authentic ones — and this benchmark will measure it.

---

## Running the benchmark

```bash
# from the project root
python run_authenticity_benchmark.py
```

Prints the table above and writes three reports into this folder:
`authenticity_benchmark_report.json`, `authenticity_benchmark_report.md`,
`authenticity_benchmark_results.csv`. It drives the real validator via `ValidatorFactory`
(no OCR logic or persistence duplicated), so the numbers match production behavior.

## Files

```
samples/images/authenticity_benchmark/
├── generate_authenticity_dataset.py   # reproducible generator (source of truth)
├── README.md                          # this file
├── <name>.jpg   × 17                  # 5 authentic + 12 tampered
├── <name>.json  × 17                  # labels (ground truth + modification)
└── authenticity_benchmark_report.*    # written by run_authenticity_benchmark.py
run_authenticity_benchmark.py          # runner (project root)
```
