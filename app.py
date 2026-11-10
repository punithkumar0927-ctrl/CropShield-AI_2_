from __future__ import annotations

import base64
import logging
from pathlib import Path

import streamlit as st

from src.cropshield.config import (
    DATA_DIR,
    LABELS_PATH,
    METRICS_PATH,
    MODEL_PATH,
    MODELS_DIR,
    TFLITE_MODEL_PATH,
    ensure_directories,
)
from src.cropshield.dataset import summarize_dataset
from src.cropshield.footer import render_about_footer
from src.cropshield.model import load_model, load_tflite_model
from src.cropshield.readiness import (
    count_supported_classes,
    load_display_labels,
    load_model_details,
)
from src.cropshield.translations import translate
from src.cropshield.ui import (
    get_selected_language,
    inject_theme,
    render_home_hero,
)

LOGGER = logging.getLogger(__name__)
ensure_directories()

st.set_page_config(page_title="CropShield AI 2.0", page_icon="🌿", layout="wide")
inject_theme(home=True)
language = get_selected_language()


@st.cache_resource
def get_model_status() -> tuple[bool, str | None]:
    """Check that at least one configured inference model can be loaded."""
    for model_path in (
        MODEL_PATH,
        MODELS_DIR / "cropshield_model.keras",
        MODELS_DIR / "cropshield_model.h5",
    ):
        if not model_path.is_file():
            continue
        try:
            if load_model(model_path) is not None:
                return True, model_path.name
        except (OSError, ValueError, RuntimeError):
            LOGGER.warning("A local model artifact could not be loaded.", exc_info=True)
    if TFLITE_MODEL_PATH.is_file():
        try:
            if load_tflite_model(TFLITE_MODEL_PATH) is not None:
                return True, TFLITE_MODEL_PATH.name
        except (OSError, ValueError, RuntimeError):
            LOGGER.warning("A local TensorFlow Lite artifact could not be loaded.", exc_info=True)
    return False, None


@st.cache_data(ttl=300)
def get_dataset_summary() -> dict:
    """Cache the local dataset scan for a responsive readiness dashboard."""
    return summarize_dataset()


def _render_setup_panel(*, model_ready: bool, dataset_ready: bool) -> None:
    """Show concrete, non-technical steps for any missing local assets."""
    if model_ready and dataset_ready:
        return

    with st.container(border=True):
        st.subheader(translate("setup_title", language))
        if not dataset_ready:
            st.warning(translate("dataset_missing_detail", language))
        if not model_ready:
            st.warning(translate("model_missing_detail", language))
        with st.expander("Expected folder structure and setup commands"):
            st.code(
                """CropShield_AI_2.0/
├── data/
│   └── PlantVillage-Dataset/
│       └── color/
│           ├── Tomato___Early_blight/
│           │   └── leaf-image.jpg
│           └── Tomato___healthy/
│               └── leaf-image.jpg
└── models/
    ├── crop_model.keras
    ├── class_labels.json
    ├── model_config.json
    └── preprocessing_config.json""",
                language="text",
            )
            st.markdown(
                "Install dependencies with `pip install -r requirements.txt`. "
                "Prepare an authorized PlantVillage archive using "
                "`python scripts/prepare_dataset.py --dataset-archive PATH_TO_ARCHIVE.zip`."
            )
            st.markdown(
                "Then train the supported Tomato classes with the following command:"
            )
            st.code(
                "python scripts/train_model.py --dataset-root "
                '"data/PlantVillage-Dataset/color" --model-type mobilenet '
                "--crop Tomato --batch-size 16 --image-size 224 --epochs 8",
                language="powershell",
            )
            st.caption(
                "Training creates a model and matching class/preprocessing metadata. "
                "Run `python scripts/evaluate_model.py` to generate test metrics."
            )


st.title(translate("app_title", language))
render_home_hero()
st.sidebar.title("Navigation")
navigation = (
    ("app.py", "home", "🏠"),
    ("pages/1_Disease_Detection.py", "disease_detection", "📷"),
    ("pages/2_Dataset_Explorer.py", "dataset_explorer", "🗂️"),
    ("pages/3_Model_Performance.py", "model_performance", "📊"),
    ("pages/4_Explainable_AI.py", "explainable_ai", "🔎"),
    ("pages/5_Prediction_History.py", "prediction_history", "🕘"),
    ("pages/8_Plant_Timeline.py", "plant_timeline", "🌱"),
    ("pages/6_About.py", "about", "ℹ️"),
    ("pages/7_Treatment_Guide.py", "treatment_guide", "🩺"),
)
for page_path, label_key, icon in navigation:
    st.sidebar.page_link(page_path, label=translate(label_key, language), icon=icon)
if st.sidebar.button("↻ " + translate("check_setup", language), key="refresh_setup"):
    get_model_status.clear()
    get_dataset_summary.clear()
    st.rerun()

dataset = get_dataset_summary()
model_ready, model_file_name = get_model_status()
model_details = load_model_details()
model_labels = load_display_labels()
if model_labels:
    crop_count, class_count = count_supported_classes(model_labels)
elif dataset.get("status") == "available":
    crop_count = len(
        {name.partition("___")[0] for name in dataset.get("class_counts", {}) if "___" in name}
    )
    class_count = int(dataset.get("class_count", 0))
else:
    crop_count, class_count = 0, 0
dataset_ready = dataset.get("status") == "available"
metrics = model_details["metrics"]

status_col, version_col = st.columns([1, 2])
with status_col:
    if model_ready:
        st.success(f"{translate('model_ready', language)} · {model_file_name}")
    else:
        st.warning(translate("model_missing", language))
with version_col:
    st.caption(
        f"{translate('model', language)}: {model_details['name']} · "
        f"{model_details['version']}"
    )
if dataset_ready:
    st.success(translate("dataset_ready", language))
else:
    st.info(translate("dataset_not_prepared", language))

card1, card2, card3 = st.columns(3)
card1.metric(translate("supported_crops", language), crop_count or "—")
card2.metric(translate("disease_classes", language), class_count or "—")
accuracy = metrics.get("accuracy") if metrics else None
card3.metric(
    translate("model_accuracy", language),
    f"{accuracy:.1%}" if accuracy is not None else translate("not_evaluated", language),
)

st.caption(translate("test_metrics", language))
if metrics:
    metric_parts = [
        f"{label}: {metrics[key]:.1%}"
        for key, label in (
            ("accuracy", "Accuracy"),
            ("precision", "Macro precision"),
            ("recall", "Macro recall"),
            ("f1", "Macro F1"),
        )
        if key in metrics
    ]
    st.write(" · ".join(metric_parts))
else:
    st.write(translate("not_evaluated", language))

_render_setup_panel(model_ready=model_ready, dataset_ready=dataset_ready)

st.subheader(translate("how_it_works", language))
st.markdown(
    f"<div class='cs-hero'><p class='cs-lead'>{translate('steps', language)}</p></div>",
    unsafe_allow_html=True,
)
st.page_link(
    "pages/1_Disease_Detection.py",
    label=translate("upload_image", language),
    icon="📷",
)

demo_dir = Path(__file__).resolve().parent / "assets" / "demo_samples"
demo_images = sorted(demo_dir.glob("*.svg"))[:5] if demo_dir.is_dir() else []
if demo_images:
    st.subheader(translate("demo_samples", language))
    st.caption(translate("demo_warning", language))
    demo_columns = st.columns(len(demo_images))
    for column, sample_path in zip(demo_columns, demo_images, strict=False):
        with column:
            try:
                encoded = base64.b64encode(sample_path.read_bytes()).decode("ascii")
                st.markdown(
                    (
                        "<div style='display:flex;justify-content:center;'><img src='data:image/svg+xml;base64,"
                        f"{encoded}' width='220' alt='{sample_path.stem.replace('_', ' ').title()}' /></div>"
                    ),
                    unsafe_allow_html=True,
                )
            except OSError:
                st.write(sample_path.stem.replace("_", " ").title())

st.caption(translate("disclaimer", language))
render_about_footer()
