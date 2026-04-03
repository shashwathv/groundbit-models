import json
import torch
import torch.nn as nn
import numpy as np
import cv2
from torchvision import models
from functools import lru_cache
from pathlib import Path
from PIL import Image
import torchvision.transforms.functional as TF

from api.services.preprocessing import prepare_tensor

BASE_DIR = Path(__file__).resolve().parents[2]
WEIGHTS_DIR = BASE_DIR / "weights"
CLASSES_DIR = BASE_DIR / "classes"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DISEASE_MODEL_MAP = {
    "cotton": "cotton_model_clean.pth",
    "maize": "maize_model_clean.pth",
    "rice": "rice_model_clean.pth",
    "sugarcane": "sugarcane_model_clean.pth",
    "tomato": "tomato_model_clean.pth",
    "groundnut": "groundnut_model_clean.pth",
    "ragi": "ragi_model_clean.pth",
    "soybean": "soybean_model_clean.pth",
}

DISEASE_CLASSES_MAP = {
    "cotton": "cotton_classes.json",
    "maize": "maize_classes.json",
    "rice": "rice_classes.json",
    "sugarcane": "sugarcane_classes.json",
    "tomato": "tomato_classes.json",
    "groundnut": "groundnut_classes.json",
    "ragi": "ragi_classes.json",
    "soybean": "soybean_classes.json",
}

def _load_classes(path):
    with open(path) as f:
        return json.load(f)

def _build_model(num_classes, weights_path):
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    state_dict = torch.load(weights_path, map_location=DEVICE, weights_only=False)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model

_crop_classes = _load_classes(CLASSES_DIR / "crop_classes.json")
_crop_model = _build_model(len(_crop_classes), WEIGHTS_DIR / "crop_model_clean.pth")

@lru_cache(maxsize=10)
def _get_disease_model(crop_name):
    classes = _load_classes(CLASSES_DIR / DISEASE_CLASSES_MAP[crop_name])
    model = _build_model(len(classes), WEIGHTS_DIR / DISEASE_MODEL_MAP[crop_name])
    return model, classes

def _segment_leaf(image):
    img = np.array(image.convert("RGB"))
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    lower = np.array([25, 40, 40])
    upper = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        cropped = img[y:y+h, x:x+w]
        return Image.fromarray(cropped)
    return image

def _multi_crop_tensors(image):
    image = _segment_leaf(image)
    image = image.convert("RGB")
    w, h = image.size

    crops = []
    crops.append(TF.center_crop(image, min(w, h)))
    crops.append(image.crop((0, 0, w//2, h//2)))
    crops.append(image.crop((w//2, 0, w, h//2)))
    crops.append(image.crop((0, h//2, w//2, h)))
    crops.append(image.crop((w//2, h//2, w, h)))

    return [prepare_tensor(c, DEVICE) for c in crops]

def _predict_avg(model, tensors, classes):
    preds = []
    with torch.no_grad():
        for t in tensors:
            preds.append(torch.softmax(model(t), dim=1))

    avg_pred = torch.mean(torch.stack(preds), dim=0)
    conf, idx = torch.max(avg_pred, dim=1)

    key = idx.item()
    if isinstance(classes, list):
        label = classes[key]
    else:
        label = classes.get(key) or classes.get(str(key))

    return label, conf.item()

def run_pipeline(image, debug=False):
    tensors = _multi_crop_tensors(image)

    crop_preds = []
    with torch.no_grad():
        for t in tensors:
            crop_preds.append(torch.softmax(_crop_model(t), dim=1))

    avg_crop = torch.mean(torch.stack(crop_preds), dim=0)
    confs, indices = torch.topk(avg_crop, k=3)

    crop_candidates = []
    for conf, idx in zip(confs[0], indices[0]):
        key = idx.item()
        if isinstance(_crop_classes, list):
            crop_name = _crop_classes[key]
        else:
            crop_name = _crop_classes.get(key) or _crop_classes.get(str(key))
        crop_candidates.append((crop_name, conf.item()))

    model_outputs = []

    for crop_name in DISEASE_MODEL_MAP.keys():
        model, classes = _get_disease_model(crop_name)
        disease_name, disease_conf = _predict_avg(model, tensors, classes)

        crop_boost = 0
        for c_name, c_conf in crop_candidates:
            if c_name == crop_name:
                crop_boost = c_conf * 0.3

        score = disease_conf + crop_boost

        if crop_name in disease_name.lower():
            score += 0.05

        model_outputs.append({
            "crop": crop_name,
            "disease": disease_name,
            "confidence": disease_conf,
            "score": score
        })

    model_outputs.sort(key=lambda x: x["score"], reverse=True)

    best = model_outputs[0]
    second = model_outputs[1]

    margin = best["score"] - second["score"]

    if best["confidence"] < 0.35:
        return {
            "crop": None,
            "crop_confidence_pct": None,
            "disease": None,
            "disease_confidence_pct": None,
            "note": "Very low confidence prediction",
            "debug": model_outputs if debug else None
        }

    note = None
    if margin < 0.03:
        note = "Low confidence (model confusion)"

    result = {
        "crop": best["crop"],
        "crop_confidence_pct": round(best["score"] * 100, 2),
        "disease": best["disease"],
        "disease_confidence_pct": round(best["confidence"] * 100, 2),
        "note": note
    }

    if debug:
        result["debug"] = model_outputs

    return result