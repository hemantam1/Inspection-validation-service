from pathlib import Path

import cv2
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    

    image = cv2.imread(str(Path(image_path)))

    if image is None:
        raise FileNotFoundError(f"Unable to load image: {image_path}")

    return image


def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculate blur score using Variance of Laplacian.
    Higher score indicates a sharper image.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(blur_score: float, threshold: float) -> bool:
    

    return blur_score < threshold