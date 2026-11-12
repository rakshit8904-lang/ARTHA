"""Run from the project root with python -m ml.compare_validation."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
from scipy.sparse import load_npz
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .shared.evaluate import measure_call, score_predictions
from .shared.prepare import prepare
from .shared.protocol import load_contract, majority_category


def compare(output):
    splits, labels = load_contract()
    train, validation = splits["train"], splits["validation"]
    models = {"Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
              "Linear SVM": LinearSVC(random_state=42), "Complement Naive Bayes": ComplementNB(),
              "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42)}
    prep = prepare(output / "shared")
    vectorizer = joblib.load(output / "shared/tfidf.joblib")
    x_train, x_val = [load_npz(output / f"shared/{s}.npz") for s in ("train", "validation")]
    descriptions = [r["description"] for r in validation]
    report = {"preparation": prep, "models": {}}
    predictions = {"Majority baseline": [majority_category(train, labels)] * len(validation)}
    for name, model in models.items():
        _, fit = measure_call(model.fit, x_train, [r["category"] for r in train])
        predictions[name], inference = measure_call(model.predict, x_val)
        path = output / (name.replace(" ", "_") + ".joblib")
        joblib.dump(Pipeline([("tfidf", vectorizer), ("classifier", model)]), path)
        if list(joblib.load(path).predict(descriptions)) != list(predictions[name]):
            raise ValueError(f"Reload check failed for {name}")
        report["models"][name] = dict(settings=model.get_params(), fit=fit, inference=inference, bytes=path.stat().st_size)
    for name, guesses in predictions.items():
        rows = [dict(transaction_id=r["transaction_id"], category=g) for r, g in zip(validation, guesses, strict=True)]
        result = report["models"].setdefault(name, {})
        result["validation"] = score_predictions(validation, rows, labels)
        result["mistakes"] = [dict(**r, predicted=g) for r, g in zip(validation, guesses) if r["category"] != g]
        result["predictions"] = rows
    (output / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent / "artifacts"
    root.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=root) as temp:
        run = Path(temp) / "comparison"
        compare(run)
        run.rename(root / "validation_v2")
