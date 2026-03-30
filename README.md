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
│       ├── test_model.py               # EfficientNet inference
│       └── class_names.json            # 38 crop/disease labels
├── data/
│   └── datasets/
│       ├── pest/                       # cricket, fruit_fly, stem_borer
│       └── no_pest/                    # ambient, quiet_outdoor, rain, wind
├── models/                             # Trained model artifacts (.pkl)
├── outputs/                            # Spectrograms, confusion matrices
└── requirements.txt
```

## Setup

```bash
# Clone
git clone https://github.com/<your-username>/groundbit.git
cd groundbit

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** Requires Python 3.11.9. CUDA 12 recommended for GPU acceleration.

## Usage

### Audio Model

```bash
# 1. Convert raw audio to 16kHz WAV
python src/audio_model/preprocessing/convert_audio.py data/raw/

# 2. Extract CNN14 embeddings from dataset
python src/audio_model/preprocessing/extract_embeddings.py

# 3. Train the classifier
python src/audio_model/core/classifier.py

# 4. Run inference on a file
python src/audio_model/core/audio_cnn.py path/to/audio.wav
```

### Visual Model

```bash
# Run disease prediction on a leaf photo
python src/visual_model/test_model.py
```

## Tech Stack

| Component | Libraries |
|-----------|-----------|
| Audio features | PyTorch, torchaudio, librosa, panns-inference |
| Audio classifier | scikit-learn (RF, LR, Gradient Boosting) |
| Visual model | TensorFlow/Keras, EfficientNet |
| Visualization | matplotlib, seaborn |

## Model Files (Not in Git)

Large files are excluded from the repository. Download or regenerate them:

- `models/embeddings.pkl` — CNN14 embeddings (run `extract_embeddings.py`)
- `models/pest_classifier.pkl` — Trained classifier (run `classifier.py`)
- `models/scaler.pkl` — Feature scaler (run `classifier.py`)
- `src/visual_model/best_model_final.h5` — EfficientNet weights
- `src/visual_model/best_model_phase1.h5` — Phase 1 weights
