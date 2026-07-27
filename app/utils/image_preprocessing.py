from PIL import Image, ImageOps
import cv2
import numpy as np

from app.core.constants import BLUR_CANONICAL_LONG_EDGE


def downscale_long_edge(
    image: np.ndarray,
    target: int = BLUR_CANONICAL_LONG_EDGE,
) -> np.ndarray:
    h, w = image.shape[:2]
    longest = max(h, w)

    if longest <= target:
        return image

    scale = target / longest
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def preprocess_for_blur(image_path: str) -> np.ndarray:
    """
    Preprocessing pipeline specific to blur detection.

    Deliberately minimal so that nothing fabricates high-frequency content:
      1. Fix EXIF orientation (geometric only; leaves frequency content intact)
      2. Downscale-only resolution normalization (see downscale_long_edge)
    """
    image = Image.open(image_path)
    image = fix_exif_orientation(image)

    image = cv2.cvtColor(
        np.array(image.convert("RGB")),
        cv2.COLOR_RGB2BGR,
    )

    image = downscale_long_edge(image)

    return image


def fix_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Correct image orientation using EXIF metadata.
    """
    return ImageOps.exif_transpose(image)


def normalize_brightness(image: np.ndarray) -> np.ndarray:
    """
    Normalize image brightness using CLAHE (Contrast Limited
    Adaptive Histogram Equalization).
    """

    lab = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2LAB,
    )

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    l = clahe.apply(l)

    lab = cv2.merge((l, a, b))

    return cv2.cvtColor(
        lab,
        cv2.COLOR_LAB2BGR,
    )


def crop_boundaries(
    image: np.ndarray,
    crop_percent: float = 0.05,
) -> np.ndarray:
    """
    Removes unwanted image boundaries before validation.

    By default, crops 5% from each side.
    Very small images are returned unchanged.
    """
    h, w = image.shape[:2]

    if h < 100 or w < 100:
        return image

    x = int(w * crop_percent)
    y = int(h * crop_percent)

    return image[
        y:h - y,
        x:w - x,
    ]


def preprocess_image(
    image_path: str,
) -> np.ndarray:
    """
    Standard image preprocessing pipeline.

    Steps:
    1. Correct EXIF orientation.
    2. Convert PIL image to OpenCV format.
    3. Normalize brightness using CLAHE.
    4. Crop image boundaries.
    """

    image = Image.open(image_path)

    image = fix_exif_orientation(image)

    image = cv2.cvtColor(
        np.array(image),
        cv2.COLOR_RGB2BGR,
    )

    image = normalize_brightness(image)

    image = crop_boundaries(image)

    return image