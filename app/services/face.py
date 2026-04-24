"""
Face recognition service — wired up when ML dependencies are installed.

Install when ready:
    pip install deepface tensorflow opencv-python numpy pillow

Then uncomment the imports and implementations below.
"""

# from deepface import DeepFace
# import numpy as np


async def extract_embedding(image_bytes: bytes) -> list[float]:
    """Extract face embedding vector from raw image bytes."""
    # TODO: decode image_bytes to numpy array (cv2.imdecode)
    # TODO: call DeepFace.represent(img, model_name="Facenet") or preferred model
    # TODO: return embedding as list[float]
    raise NotImplementedError


async def compare_embeddings(stored: list[float], live: list[float]) -> tuple[bool, float]:
    """
    Compare stored enrollment embedding against a live scan.
    Returns (match: bool, confidence: float).
    """
    # TODO: compute cosine similarity between stored and live vectors
    # TODO: apply a threshold (e.g. 0.6 for Facenet) to determine match
    # TODO: return (similarity >= threshold, similarity)
    raise NotImplementedError


async def verify_student_face(
    student_id: str,
    image_bytes: bytes,
    db,
) -> tuple[bool, float]:
    """
    Full pipeline: fetch stored embedding, extract live embedding, compare.
    Called from attendance router before recording attendance.
    """
    # TODO: fetch user.face_embedding from DB for student_id
    # TODO: if no embedding stored, decide policy — reject or allow (configure via env)
    # TODO: call extract_embedding(image_bytes)
    # TODO: call compare_embeddings(stored, live)
    # TODO: return result
    raise NotImplementedError
