# --- Blur detection ---
# VoL < BLUR_THRESHOLD => image is considered blurry.
BLUR_THRESHOLD = 250.0
# Long edge (px) that blur preprocessing normalizes to. Downscale-only: images
# smaller than this are left as-is (upscaling smooths detail and deflates VoL).
BLUR_CANONICAL_LONG_EDGE = 1024
EARTH_RADIUS_METERS = 6371000
DUPLICATE_SIMILARITY_THRESHOLD = 0.90
MIN_CAPTURE_INTERVAL_SECONDS = 10
GPS_ACCURACY_THRESHOLD = 50  # meters
GPS_POOR_ACCURACY_PENALTY = 10
OCR_MATCH_THRESHOLD = 85
OCR_MIN_CONFIDENCE = 80
OCR_CONFIDENCE_PENALTY = 10
ELA_JPEG_QUALITY = 90
ELA_THRESHOLD = 15.0
# Localized ELA: residual is aggregated into ELA_BLOCK_SIZE x ELA_BLOCK_SIZE
# blocks; the hotspot is the ELA_HOTSPOT_PERCENTILE of block-mean errors.
ELA_BLOCK_SIZE = 16
ELA_HOTSPOT_PERCENTILE = 99
# Authenticity score weights: the hotspot's contrast against the image's own
# baseline is the tampering-relevant term, so it is weighted above the level.
ELA_SCORE_CONTRAST_WEIGHT = 4.0
ELA_SCORE_LEVEL_WEIGHT = 1.0
DOCUMENT_AUTHENTICITY_RISK_SCORE = 40