

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

CATEGORIES: List[str] = [
    "Authentication",
    "Database Operations",
    "API/Communication",
    "Business Logic",
    "Configuration/Utilities",
    "Testing",
]


@dataclass
class ClassificationResult:
    """Prediction outcome for a code entity."""
    category: str
    confidence: float
    probabilities: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "confidence": round(self.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
        }


class CodeClassifier:
    """TF-IDF + Logistic Regression model for code snippet classification."""

    def __init__(self, training_data_path: Optional[str | Path] = None):
        if training_data_path is None:
            training_data_path = Path(__file__).parent / "training_data.json"
        self.training_data_path = Path(training_data_path)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=3000,
            token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b",
        )
        self.model = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            solver="lbfgs",
        )
        self.is_trained: bool = False
        self.training_counts: Dict[str, int] = {}
        self._load_and_train()

    def _load_and_train(self) -> None:
        """Load labeled data from JSON and fit the model."""
        if not self.training_data_path.exists():
            raise FileNotFoundError(
                f"Training dataset not found at {self.training_data_path}"
            )

        with open(self.training_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        texts: List[str] = []
        labels: List[str] = []
        self.training_counts = {cat: 0 for cat in CATEGORIES}

        for item in raw_data:
            cat = item.get("category")
            txt = item.get("text", "")
            if cat in self.training_counts and txt.strip():
                texts.append(txt)
                labels.append(cat)
                self.training_counts[cat] += 1

        if not texts:
            raise ValueError("Training dataset has no valid samples.")

        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_trained = True

    def predict(self, code_text: str) -> ClassificationResult:
        """Classify a single code snippet, returning predicted category and confidence."""
        if not self.is_trained:
            raise RuntimeError("Classifier has not been trained.")

        cleaned = code_text.strip()
        if not cleaned:
            uniform_prob = 1.0 / len(CATEGORIES)
            return ClassificationResult(
                category="Configuration/Utilities",
                confidence=uniform_prob,
                probabilities={cat: uniform_prob for cat in CATEGORIES},
            )

        X = self.vectorizer.transform([cleaned])
        pred_label = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]
        class_labels = self.model.classes_

        prob_dict = {str(label): float(prob) for label, prob in zip(class_labels, probs)}
        confidence = float(prob_dict.get(pred_label, 0.0))

        return ClassificationResult(
            category=pred_label,
            confidence=confidence,
            probabilities=prob_dict,
        )

    def get_dataset_info(self) -> Dict[str, Any]:
        """Metadata about the transparent baseline training set."""
        total = sum(self.training_counts.values())
        return {
            "total_samples": total,
            "category_distribution": dict(self.training_counts),
            "disclaimer": (
                "NOTE: This classifier uses a transparent, compact baseline dataset "
                "intended for initial categorization. For production environments, "
                "fine-tuning on domain-specific enterprise codebases is recommended."
            ),
        }
