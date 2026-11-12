"""Local inference with the exact pipeline selected before final testing."""
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import logging
from pathlib import Path

import joblib

MODEL_FILE = Path(__file__).with_name("Linear_SVM.joblib")
FROZEN_HASH = "9820d9a24a5e3b6a969a8ba17ef0f205256bb00d81301af9290e55be73f73176"


@lru_cache(maxsize=1)
def load_model():
    data = MODEL_FILE.read_bytes()
    if sha256(data).hexdigest() != FROZEN_HASH:
        raise ValueError("Frozen model checksum mismatch")
    return joblib.load(BytesIO(data))


def suggest_categories(rows):
    eligible = [r for r in rows if not r["errors"] and not r["category"]
                and r["direction"] == "debit" and r["transaction_type"] in (None, "purchase", "fee")]
    if not eligible:
        return
    try:
        model = load_model()
        features = model.named_steps["tfidf"].transform([r["description"] for r in eligible])
        predictions = model.named_steps["classifier"].predict(features)
        for row, guess, known_words in zip(eligible, predictions, features.getnnz(axis=1), strict=True):
            if known_words:
                row["suggested_category"] = str(guess)
    except (OSError, ValueError, ImportError):
        logging.getLogger(__name__).warning("Category suggestions unavailable; manual review is available.")
