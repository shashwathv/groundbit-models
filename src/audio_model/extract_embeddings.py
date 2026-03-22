"""
extract_embeddings.py
Extracts CNN14 embeddings from pest/ and no_pest/ folders.
Saves embeddings.pkl to models/

Usage:
    python src/extract_embeddings.py
"""

import os
import pickle
import numpy as np
import librosa
from panns_inference import AudioTagging

# ── Paths ──────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'data', 'datasets')
MODELS_DIR  = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

CLASSES     = ['no_pest', 'pest']   # binary: 0 = no_pest, 1 = pest
SAMPLE_RATE = 16000
DURATION    = 3  # seconds
# ───────────────────────────────────────────────────────

def load_audio(path):
    y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=DURATION)
    if len(y) < SAMPLE_RATE * DURATION:
        y = np.pad(y, (0, SAMPLE_RATE * DURATION - len(y)))
    return y

def extract_all():
    print("Loading CNN14 model...")
    model = AudioTagging(checkpoint_path=None, device='cpu')
    print("Model ready.\n")

    X, y_labels = [], []

    for label, class_name in enumerate(CLASSES):
        folder = os.path.join(DATASET_DIR, class_name)
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found: {folder}")
            continue

        # Walk recursively through all subfolders
        files = []
        for root, _, fnames in os.walk(folder):
            for f in fnames:
                if f.endswith('.wav'):
                    files.append(os.path.join(root, f))
        print(f"[{class_name}] — {len(files)} files found (including subfolders)")

        for fpath in files:
            fname = os.path.relpath(fpath, folder)
            try:
                audio = load_audio(fpath)
                _, embedding = model.inference(audio[None, :])
                X.append(embedding[0])      # 1024-dim feature vector
                y_labels.append(label)
                print(f"  ✅ {fname}")
            except Exception as e:
                print(f"  ❌ {fname}: {e}")

    X = np.array(X)
    y_labels = np.array(y_labels)

    out_path = os.path.join(MODELS_DIR, 'embeddings.pkl')
    with open(out_path, 'wb') as f:
        pickle.dump({'X': X, 'y': y_labels, 'classes': CLASSES}, f)

    print(f"\n✅ Done! Saved {len(X)} embeddings → models/embeddings.pkl")
    print(f"   pest samples   : {np.sum(y_labels == 1)}")
    print(f"   no_pest samples: {np.sum(y_labels == 0)}")

if __name__ == '__main__':
    extract_all()