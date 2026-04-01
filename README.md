# 🌾 GroundBit

Agricultural pest detection system combining **audio-based pest detection** and **visual plant disease classification** using deep learning.

## Features

- **Audio Pest Detection** — Detects pest activity (crickets, fruit flies, stem borers) from field audio recordings using CNN14 embeddings + ML classifiers
- **Visual Disease Classification** — Identifies 38 crop diseases across 14 crops from leaf photos using EfficientNet

## Project Structure

```
groundbit/
├── src/
│   ├── audio_model/
│   │   ├── core/
│   │   │   ├── audio_cnn.py            # Inference entry point — detect()
│   │   │   └── classifier.py           # Train & evaluate classifiers
│   │   ├── preprocessing/
│   │   │   ├── convert_audio.py        # Raw audio → 16kHz mono WAV
│   │   │   └── extract_embeddings.py   # CNN14 → 1024-dim embeddings
│   │   ├── samples/                    # Sample audio files
│   │   └── api/                        # FastAPI prediction server
│   └── visual_model/
│       ├── api/                        # FastAPI prediction server
│       │   ├── middleware/cors.py      # CORS config
│       │   ├── models/schemas.py       # Pydantic response models
│       │   ├── routes/                 # /predict, /health, /crops
│       │   └── services/              # Inference pipeline & preprocessing
│       ├── classes/                    # Per-crop disease label JSONs
│       ├── weights/                   # EfficientNet .pth weights (LFS)
│       └── test/test_model.py         # Smoke-test script
├── data/
│   └── datasets/
│       ├── pest/                       # cricket, fruit_fly, stem_borer
│       └── no_pest/                    # ambient, quiet_outdoor, rain, wind
├── models/                             # Trained model artifacts (.pkl)
├── outputs/                            # Spectrograms, confusion matrices
└── requirements.txt
```

## Tech Stack

| Component | Libraries |
|-----------|-----------|
| Audio features | PyTorch, torchaudio, librosa, panns-inference |
| Audio classifier | scikit-learn (RF, LR, Gradient Boosting) |
| Visual model | PyTorch, torchvision, EfficientNet |
| Visualization | matplotlib, seaborn |
