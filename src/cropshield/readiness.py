"""Helpers for reporting model, label, dataset, and evaluation readiness."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

from .config import DATA_DIR, LABELS_PATH, METRICS_PATH, MODELS_DIR

LOGGER = logging.getLogger(__name__)
MODEL_CONFIG_PATH = MODELS_DIR / "model_config.json"
DATASET_LABELS_PATH = DATA_DIR / "class_labels.json"


def load_display_labels(
    model_labels_path: str | Path = LABELS_PATH,
    dataset_labels_path: str | Path = DATASET_LABELS_PATH,
) -> list[str]:
    """Prefer model labels, then prepared dataset labels, for honest class counts."""
    for path in (Path(model_labels_path), Path(dataset_labels_path)):
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as labels_file:
                document: Any = json.load(labels_file)
        except (OSError, ValueError):
            LOGGER.warning("Could not read class labels from %s.", path, exc_info=True)
            continue
        if isinstance(document, list):
            labels = document
        elif isinstance(document, dict):
            labels = document.get("class_labels", document.get("class_names", document.get("labels", [])))
        else:
            labels = []
        if isinstance(labels, list) and all(isinstance(label, str) and label for label in labels):
            return labels
        LOGGER.warning("Class labels in %s have an unsupported format.", path)
    return []


def count_supported_classes(labels: list[str]) -> tuple[int, int]:
    """Count unique crop names and model classes from ``Crop___Condition`` labels."""
    crops = {label.partition("___")[0] for label in labels if "___" in label}
    return len(crops), len(labels)


def load_model_details(
    config_path: str | Path = MODEL_CONFIG_PATH,
    metrics_path: str | Path = METRICS_PATH,
) -> dict[str, Any]:
    """Load model identity and metrics from local metadata without raising UI errors."""
    config: dict[str, Any] = {}
    try:
        with Path(config_path).open("r", encoding="utf-8") as config_file:
            loaded_config = json.load(config_file)
        if isinstance(loaded_config, dict):
            config = loaded_config
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        LOGGER.warning("Could not read the local model configuration.", exc_info=True)

    model_type = str(config.get("model_type", "model")).strip().lower()
    model_name = {
        "mobilenet": "MobileNetV2",
        "baseline": "Baseline CNN",
    }.get(model_type, model_type.replace("_", " ").title())
    model_version = str(config.get("model_version", "Version not recorded"))
    metrics: dict[str, float] | None = None

    try:
        with Path(metrics_path).open("r", encoding="utf-8") as metrics_file:
            evaluation = json.load(metrics_file)
    except FileNotFoundError:
        evaluation = {}
    except (OSError, ValueError):
        LOGGER.warning("Could not read the local evaluation metrics.", exc_info=True)
        evaluation = {}

    models = evaluation.get("models") if isinstance(evaluation, dict) else None
    selected_model = None
    if evaluation.get("status") == "evaluated" and isinstance(models, dict):
        selected_model = models.get(model_type)
        if not isinstance(selected_model, dict):
            selected_model = models.get(str(evaluation.get("updated_model", "")))
    if isinstance(selected_model, dict):
        metric_keys = {
            "accuracy": "accuracy",
            "precision": "macro_precision",
            "recall": "macro_recall",
            "f1": "macro_f1",
        }
        valid_metrics = {
            label: float(selected_model[key])
            for label, key in metric_keys.items()
            if isinstance(selected_model.get(key), (int, float))
            and not isinstance(selected_model.get(key), bool)
            and math.isfinite(float(selected_model[key]))
            and 0 <= float(selected_model[key]) <= 1
        }
        metrics = valid_metrics or None

    return {
        "name": model_name,
        "version": model_version,
        "type": model_type,
        "metrics": metrics,
    }
