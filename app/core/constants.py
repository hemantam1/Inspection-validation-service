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
OCR_MATCH_THRESHOLD = 0.95
OCR_MIN_CONFIDENCE = 80