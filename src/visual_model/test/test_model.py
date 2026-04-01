"""
Quick smoke-test for the visual model inference pipeline.

Usage:
    python test_model.py <image_path>
    python test_model.py              # uses a default test image
"""

import sys
import json
from pathlib import Path

import torch
from torchvision import models, transforms
from PIL import Image

# ── Paths ────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[1]       # src/visual_model/
WEIGHTS_DIR = BASE_DIR / "weights"
CLASSES_DIR = BASE_DIR / "classes"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


def load_model(weights_path: Path, num_classes: int):
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(
        model.classifier[1].in_features, num_classes
    )
    state_dict = torch.load(weights_path, map_location=DEVICE, weights_only=False)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model


def predict(model, image_path: str, classes):
    img = Image.open(image_path).convert("RGB")
    tensor = TRANSFORM(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)
        conf, idx = torch.max(probs, dim=1)

    key = idx.item()
    label = classes[key] if isinstance(classes, list) else classes.get(str(key), classes.get(key))
    return label, round(conf.item() * 100, 2)


def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    if image_path is None:
        print("Usage: python test_model.py <image_path>")
        sys.exit(1)

    # ── Step 1: Identify the crop ──────────────────────
    crop_classes_path = CLASSES_DIR / "crop_classes.json"
    with open(crop_classes_path) as f:
        crop_classes = json.load(f)

    crop_model = load_model(WEIGHTS_DIR / "crop_model_clean.pth", len(crop_classes))
    crop_name, crop_conf = predict(crop_model, image_path, crop_classes)
    print(f"Crop:    {crop_name}  ({crop_conf}%)")

    # ── Step 2: Identify the disease ───────────────────
    disease_file = CLASSES_DIR / f"{crop_name}_classes.json"
    disease_weight = WEIGHTS_DIR / f"{crop_name}_model_clean.pth"

    if not disease_file.exists() or not disease_weight.exists():
        print(f"  → No disease model available for '{crop_name}'")
        return

    with open(disease_file) as f:
        disease_classes = json.load(f)

    disease_model = load_model(disease_weight, len(disease_classes))
    disease_name, disease_conf = predict(disease_model, image_path, disease_classes)
    print(f"Disease: {disease_name}  ({disease_conf}%)")


if __name__ == "__main__":
    main()