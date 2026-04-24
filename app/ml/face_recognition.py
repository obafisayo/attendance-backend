"""
ML model wrapper for face recognition.

This module is intentionally separate from services/face.py so you can
swap models (DeepFace, FaceNet, ArcFace, your own trained model) without
touching the service layer.

Steps to wire up:
  1. Install ML deps (uncomment in requirements.txt, pip install)
  2. Implement extract_embedding() and compare()
  3. Import and call from services/face.py
"""


class FaceRecognitionModel:
    # TODO: load your model weights here in __init__ (once, at startup)
    # TODO: store as class-level singleton so it's not reloaded per request

    def extract_embedding(self, image_bytes: bytes) -> list[float]:
        # TODO: preprocess image (resize, normalize)
        # TODO: run inference
        # TODO: return embedding vector
        raise NotImplementedError

    def compare(self, emb1: list[float], emb2: list[float], threshold: float = 0.6) -> tuple[bool, float]:
        # TODO: cosine similarity between emb1 and emb2
        # TODO: return (similarity >= threshold, similarity)
        raise NotImplementedError


# Singleton — import this instance in services/face.py
# face_model = FaceRecognitionModel()
