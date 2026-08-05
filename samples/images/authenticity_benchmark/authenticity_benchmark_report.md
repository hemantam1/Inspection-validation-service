# Document Authenticity Benchmark Report

_ELA_THRESHOLD = 15.0_

| Image | Type | Localized Error | Hotspot Contrast | Score | Tampering Detected |
|-------|------|----------------:|-----------------:|------:|:------------------:|
| bank_statement_original | AUTHENTIC | 1.88 | 1.88 | 91 | False |
| inspection_report_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| invoice_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| kyc_form_original | AUTHENTIC | 1.83 | 1.83 | 91 | False |
| property_inspection_original | AUTHENTIC | 6.07 | 6.07 | 70 | False |
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
| property_tampered_addstamp | TAMPERED | 6.07 | 6.07 | 70 | False |
| property_tampered_removestamp | TAMPERED | 2.11 | 2.11 | 89 | False |

## Calibration

- Authentic localized-error range: [1.83, 6.07]
- Max authentic localized error: **6.07**
- Tampered docs above that max (ELA-separable): []
- Tampered docs at/below it (NOT ELA-separable): ['bank_statement_tampered_recompress', 'bank_statement_tampered_refid', 'inspection_report_tampered_date', 'inspection_report_tampered_inspector', 'inspection_report_tampered_status', 'inspection_report_tampered_vehicle', 'invoice_tampered_amount', 'invoice_tampered_copymove', 'kyc_tampered_signature', 'kyc_tampered_splice', 'property_tampered_addstamp', 'property_tampered_removestamp']
- Suggested ELA_THRESHOLD (catches separable tampers only): **None**

