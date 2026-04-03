import torch
from torchvision import transforms
from PIL import Image, ImageEnhance, ImageFilter

def _enhance_image(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.1)

    image = image.filter(ImageFilter.SHARPEN)

    return image

TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

def prepare_tensor(image: Image.Image, device: torch.device) -> torch.Tensor:
    image = _enhance_image(image)
    return TRANSFORM(image).unsqueeze(0).to(device)