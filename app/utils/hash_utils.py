from PIL import Image
import imagehash


def load_image(image_path: str) -> Image.Image:
    return Image.open(image_path)


def calculate_phash(image: Image.Image) -> imagehash.ImageHash:
    return imagehash.phash(image)


def calculate_similarity(
    hash1: imagehash.ImageHash,
    hash2: imagehash.ImageHash,
) -> float:
    """
    Value returned:
        1.0 - identical
        0.0 - completely different
    """

    hamming_distance = hash1 - hash2

    max_bits = len(hash1.hash.flatten())

    similarity = 1 - (hamming_distance / max_bits)

    return round(similarity, 2)