from PIL import Image
import imagehash
import cv2
import numpy as np


def calculate_phash(
    image: np.ndarray,
) -> imagehash.ImageHash:
    """
    Calculates perceptual hash (pHash) for a preprocessed
    OpenCV (BGR) image.
    """

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB,
    )

    pil_image = Image.fromarray(image)

    return imagehash.phash(pil_image)


def calculate_similarity(
    hash1: imagehash.ImageHash,
    hash2: imagehash.ImageHash,
) -> float:
    """
    Returns similarity score between two perceptual hashes.

    1.0 -> Identical
    0.0 -> Completely different
    """

    hamming_distance = hash1 - hash2

    max_bits = len(hash1.hash.flatten())

    similarity = 1 - (hamming_distance / max_bits)

    return round(similarity, 2)