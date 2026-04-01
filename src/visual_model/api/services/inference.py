import json
import torch
import torch.nn as nn
import zipfile
import io
from torchvision import models
from functools import lru_cache
from pathlib import Path

from api.services.preprocessing import prepare_tensor

BASE_DIR   = Path(__file__).resolve().parents[2]
WEIGHTS_DIR = BASE_DIR / "weights"
CLASSES_DIR = BASE_DIR / "classes"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DISEASE_MODEL_MAP = {
    "cotton":    "cotton_model_clean.pth",
    "maize":     "maize_model_clean.pth",
    "rice":      "rice_model_clean.pth",
    "sugarcane": "sugarcane_model_clean.pth",
    "tomato":    "tomato_model_clean.pth",
    "groundnut": "groundnut_model_clean.pth",
    "ragi":      "ragi_model_clean.pth",
    "soybean":   "soybean_model_clean.pth",
}

DISEASE_CLASSES_MAP = {
    "cotton":    "cotton_classes.json",
    "maize":     "maize_classes.json",
    "rice":      "rice_classes.json",
    "sugarcane": "sugarcane_classes.json",
    "tomato":    "tomato_classes.json",
    "groundnut": "groundnut_classes.json",
    "ragi":      "ragi_classes.json",
    "soybean":   "soybean_classes.json",
}

def _load_classes(path) -> dict:
    with open(path) as f:
        return json.load(f)

def _build_model(num_classes: int, weights_path: Path) -> nn.Module:
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features, num_classes
    )
    state_dict = torch.load(weights_path, map_location=DEVICE, weights_only=False)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model

# Crop model — loaded once at import
_crop_classes = _load_classes(CLASSES_DIR / "crop_classes.json")
_crop_model   = _build_model(len(_crop_classes), WEIGHTS_DIR / "crop_model_clean.pth")

@lru_cache(maxsize=5)
def _get_disease_model(crop_name: str):
    classes = _load_classes(CLASSES_DIR / DISEASE_CLASSES_MAP[crop_name])
    model   = _build_model(len(classes), WEIGHTS_DIR / DISEASE_MODEL_MAP[crop_name])
    return model, classes

def _predict(model: nn.Module, tensor: torch.Tensor, classes):
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)
        conf, idx = torch.max(probs, dim=1)
    
    key = idx.item()
    
    # Handle both list and dict formats
    if isinstance(classes, list):
        label = classes[key]
    else:
        label = classes.get(key) or classes.get(str(key))
    
    return label, round(conf.item() * 100, 2)

def run_pipeline(image) -> dict:
    tensor = prepare_tensor(image, DEVICE)

    crop_name, crop_conf = _predict(_crop_model, tensor, _crop_classes)

    if crop_name not in DISEASE_MODEL_MAP:
        return {
            "crop": crop_name,
            "crop_confidence_pct": crop_conf,
            "disease": None,
            "disease_confidence_pct": None,
            "note": f"No disease model available for '{crop_name}'"
        }

    disease_model, disease_classes = _get_disease_model(crop_name)
    disease_name, disease_conf = _predict(disease_model, tensor, disease_classes)

    return {
        "crop": crop_name,
        "crop_confidence_pct": crop_conf,
        "disease": disease_name,
        "disease_confidence_pct": disease_conf,
        "note": None
    }
