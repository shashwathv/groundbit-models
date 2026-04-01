import torch
from torchvision import transforms
from PIL import Image

TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

def prepare_tensor(image: Image.Image, device: torch.device) -> torch.Tensor:
    return TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)