import io

import numpy as np
from PIL import Image, ImageChops, ImageStat

from app.core.constants import (
    ELA_BLOCK_SIZE,
    ELA_HOTSPOT_PERCENTILE,
    ELA_JPEG_QUALITY,
    ELA_SCORE_CONTRAST_WEIGHT,
    ELA_SCORE_LEVEL_WEIGHT,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


def load_image(
    image_path: str,
) -> Image.Image:
    """
    Loads an image from disk.

    Returns:
        PIL Image in RGB mode.
    """

    logger.info(
        "Loading image: %s",
        image_path,
    )

    with Image.open(image_path) as image:
        return image.convert("RGB")


def perform_ela(
    image_path: str,
) -> tuple[float, float]:
    """
    Performs localized Error Level Analysis (ELA).

    The recompression residual is aggregated into fixed-size blocks so a locally
    edited region can stand out against the rest of the document, instead of
    being averaged into a single whole-image number.

    Returns:
        (
            localized_error,   # error level of the hottest regions
            hotspot_contrast,  # how far the hottest region sits above the
                               # image's own baseline (the tampering signal)
        )
    """

    logger.info(
        "Running localized Error Level Analysis."
    )

    original = load_image(image_path)

    buffer = io.BytesIO()

    original.save(
        buffer,
        format="JPEG",
        quality=ELA_JPEG_QUALITY,
    )

    buffer.seek(0)

    with Image.open(buffer) as recompressed:
        difference = ImageChops.difference(
            original,
            recompressed.convert("RGB"),
        )

    # Per-pixel error = strongest response across channels, kept on the native
    # 0-255 scale (no per-image normalization, which previously saturated max).
    residual = np.asarray(
        difference,
        dtype=np.float32,
    ).max(axis=2)

    # Average the residual over non-overlapping ELA_BLOCK_SIZE blocks.
    height, width = residual.shape
    rows = (height // ELA_BLOCK_SIZE) * ELA_BLOCK_SIZE
    cols = (width // ELA_BLOCK_SIZE) * ELA_BLOCK_SIZE

    if rows and cols:
        block_means = (
            residual[:rows, :cols]
            .reshape(
                rows // ELA_BLOCK_SIZE,
                ELA_BLOCK_SIZE,
                cols // ELA_BLOCK_SIZE,
                ELA_BLOCK_SIZE,
            )
            .mean(axis=(1, 3))
        )
    else:
        # Image smaller than one block: treat the whole image as a single block.
        block_means = residual.reshape(1, -1).mean(axis=1)

    hotspot = float(
        np.percentile(block_means, ELA_HOTSPOT_PERCENTILE)
    )
    baseline = float(np.median(block_means))

    localized_error = round(hotspot, 2)
    hotspot_contrast = round(hotspot - baseline, 2)

    logger.info(
        (
            "ELA completed | "
            "localized=%.2f | "
            "contrast=%.2f"
        ),
        localized_error,
        hotspot_contrast,
    )

    return (
        localized_error,
        hotspot_contrast,
    )


def calculate_authenticity_score(
    localized_error: float,
    hotspot_contrast: float,
) -> int:
    """
    Converts localized ELA statistics into
    an authenticity score.

    Higher score => More authentic. A hotspot that stands well above the
    image's own baseline is the tampering signal, so it is weighted the most.
    """

    penalty = (
        (hotspot_contrast * ELA_SCORE_CONTRAST_WEIGHT)
        + (localized_error * ELA_SCORE_LEVEL_WEIGHT)
    )

    score = max(
        0,
        min(
            100,
            round(
                100 - penalty
            ),
        ),
    )

    logger.info(
        "Authenticity score: %d",
        score,
    )

    return score