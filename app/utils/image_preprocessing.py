from PIL import Image, ImageOps
import cv2
import numpy as np


def fix_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Correct image orientation using EXIF metadata.
    """
    return ImageOps.exif_transpose(image)


def normalize_brightness(image: np.ndarray) -> np.ndarray:
    """
    Normalize image brightness using CLAHE.
    """

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

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
    Crop image boundaries to remove unwanted edges.
    Default: removes 5% from each side.
    """

    h, w = image.shape[:2]

    x = int(w * crop_percent)
    y = int(h * crop_percent)

    return image[
        y : h - y,
        x : w - x,
    ]


def preprocess_image(
    image_path: str,
) -> np.ndarray:
    """
    Complete preprocessing pipeline.

    1. Fix EXIF orientation
    2. Convert to OpenCV format
    3. Normalize brightness
    4. Crop image boundaries
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