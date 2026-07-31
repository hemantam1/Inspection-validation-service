# OCR Validator Benchmark Report

_Generated: 2026-07-30T10:51:30.408594+00:00_

**Result: ✅ PASS**

## Summary

| Metric | Value |
|--------|------:|
| Total Samples | 28 |
| Passed | 28 |
| Failed | 0 |
| Accuracy | 100.0% |
| Average OCR Confidence | 78.2 |
| Average Match Score | 76.61 |
| False Positives | 0 |
| False Negatives | 0 |

### Category-wise accuracy

| Group | Passed | Total | Accuracy |
|-------|:------:|:-----:|:--------:|
| difficult | 5 | 5 | 100.0% |
| edge-case | 7 | 7 | 100.0% |
| negative | 5 | 5 | 100.0% |
| perfect-quality | 6 | 6 | 100.0% |
| slightly-noisy | 5 | 5 | 100.0% |

### Difficulty-wise accuracy

| Group | Passed | Total | Accuracy |
|-------|:------:|:-----:|:--------:|
| easy | 6 | 6 | 100.0% |
| hard | 11 | 11 | 100.0% |
| medium | 11 | 11 | 100.0% |

### Worst 5 samples

| Sample | Status | Expected | Actual | Δ |
|--------|:------:|:--------:|:------:|:--:|
| qr_code_01 | TN | 30.7 | 29.21 | 1.49 |
| blank_page_01 | TN | 17.1 | 17.5 | 0.4 |
| inspection_report_rotated90_01 | TN | 23.3 | 23.68 | 0.38 |
| inspection_report_folded_01 | TP | 93.9 | 93.65 | 0.25 |
| symbols_only_01 | TN | 18.0 | 17.88 | 0.12 |

### Best 5 samples

| Sample | Status | Expected | Actual | Δ |
|--------|:------:|:--------:|:------:|:--:|
| form_01 | TP | 100.0 | 100.0 | 0.0 |
| handwritten_note_01 | TP | 100.0 | 100.0 | 0.0 |
| id_card_01 | TP | 100.0 | 100.0 | 0.0 |
| inspection_report_01 | TP | 100.0 | 100.0 | 0.0 |
| inspection_report_02 | TP | 100.0 | 100.0 | 0.0 |

## All samples

| Sample | Category | Diff | Status | Exp | Act | Score | Conf |
|--------|----------|------|:------:|:---:|:---:|------:|-----:|
| blank_page_01 | edge-case | hard | TN | False | False | 17.5 | 6.4 |
| different_language_01 | negative | hard | TN | False | False | 49.69 | 91.93 |
| form_01 | perfect-quality | easy | TP | True | True | 100.0 | 95.0 |
| handwritten_note_01 | edge-case | medium | TP | True | True | 100.0 | 82.91 |
| id_card_01 | perfect-quality | easy | TP | True | True | 100.0 | 94.79 |
| inspection_report_01 | perfect-quality | easy | TP | True | True | 100.0 | 94.09 |
| inspection_report_02 | perfect-quality | easy | TP | True | True | 100.0 | 93.82 |
| inspection_report_blur_01 | slightly-noisy | medium | TP | True | True | 100.0 | 94.77 |
| inspection_report_cropped_01 | difficult | hard | TN | False | False | 74.66 | 94.86 |
| inspection_report_folded_01 | difficult | hard | TP | True | True | 93.65 | 76.92 |
| inspection_report_jpeg_01 | slightly-noisy | medium | TP | True | True | 100.0 | 94.95 |
| inspection_report_lowcontrast_01 | slightly-noisy | medium | TP | True | True | 100.0 | 94.41 |
| inspection_report_perspective_01 | difficult | hard | TP | True | True | 98.12 | 84.12 |
| inspection_report_rotated90_01 | difficult | hard | TN | False | False | 23.68 | 54.18 |
| inspection_report_shadow_01 | slightly-noisy | medium | TP | True | True | 100.0 | 95.0 |
| inspection_report_skew_01 | difficult | hard | TN | False | False | 84.62 | 75.48 |
| invoice_01 | perfect-quality | easy | TP | True | True | 93.83 | 89.77 |
| mixed_font_sizes_01 | edge-case | medium | TP | True | True | 100.0 | 95.05 |
| multiline_table_01 | edge-case | medium | TN | False | False | 34.09 | 57.6 |
| qr_code_01 | negative | hard | TN | False | False | 29.21 | 53.0 |
| random_no_text_01 | edge-case | hard | TN | False | False | 0.0 | 0.0 |
| receipt_01 | perfect-quality | easy | TP | True | True | 90.77 | 91.33 |
| receipt_noisy_01 | slightly-noisy | medium | TP | True | True | 90.77 | 93.67 |
| symbols_only_01 | negative | hard | TN | False | False | 17.88 | 23.13 |
| tiny_font_01 | edge-case | hard | TP | True | True | 93.44 | 84.77 |
| watermark_over_text_01 | edge-case | medium | TP | True | True | 100.0 | 93.95 |
| wrong_document_01 | negative | medium | TN | False | False | 72.68 | 93.82 |
| wrong_reference_code_01 | negative | medium | TN | False | False | 80.43 | 89.74 |
