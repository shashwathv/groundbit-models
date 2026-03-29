"""
audio_cnn.py
Binary pest detector — answers: IS THERE A BUG IN THIS AUDIO?
Uses CNN14 embeddings + trained classifier.

Usage:
    python src/audio_cnn.py path/to/audio.wav
    python src/audio_cnn.py                    # uses data/converted/ latest file
"""

import os
import sys
import numpy as np
import librosa
import matplotlib.pyplot as plt
import joblib
from panns_inference import AudioTagging

# ── Paths ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
OUT_DIR    = os.path.join(BASE_DIR, 'outputs', 'spectrograms')
os.makedirs(OUT_DIR, exist_ok=True)

# ── Config ─────────────────────────────────────────────
SAMPLE_RATE = 16000
DURATION    = 3       # seconds
THRESHOLD   = 0.50    # raise to 0.65 to reduce false alarms
# ───────────────────────────────────────────────────────

def load_audio(path):
    y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=DURATION)
    if len(y) < SAMPLE_RATE * DURATION:
        y = np.pad(y, (0, SAMPLE_RATE * DURATION - len(y)))
    return y

def save_spectrogram(y, wav_path):
    mel = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, n_mels=128,
                                          n_fft=1024, hop_length=512)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    plt.figure(figsize=(8, 3))
    librosa.display.specshow(mel_db, sr=SAMPLE_RATE, hop_length=512,
                              x_axis='time', y_axis='mel', cmap='magma')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Mel Spectrogram — {os.path.basename(wav_path)}')
    plt.tight_layout()

    fname   = os.path.splitext(os.path.basename(wav_path))[0] + '_spectrogram.png'
    out_path = os.path.join(OUT_DIR, fname)
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"📊 Spectrogram saved → outputs/spectrograms/{fname}")

def load_models():
    clf_path    = os.path.join(MODELS_DIR, 'pest_classifier.pkl')
    scaler_path = os.path.join(MODELS_DIR, 'scaler.pkl')

    if not os.path.exists(clf_path) or not os.path.exists(scaler_path):
        print("❌ No trained model found.")
        print("   Run these first:")
        print("     python src/extract_embeddings.py")
        print("     python src/train_classifier.py")
        sys.exit(1)

    clf    = joblib.load(clf_path)
    scaler = joblib.load(scaler_path)
    return clf, scaler

def detect(wav_path):
    print(f"\n🎤 Analysing: {os.path.basename(wav_path)}")
    print("─" * 45)

    # Load audio
    audio = load_audio(wav_path)
    print(f"Audio loaded : {len(audio)/SAMPLE_RATE:.1f} seconds @ {SAMPLE_RATE}Hz")

    # Save spectrogram
    save_spectrogram(audio, wav_path)

    # Extract CNN14 embedding
    print("Extracting CNN14 features...")
    panns_model = AudioTagging(checkpoint_path=None, device='cpu')
    _, embedding = panns_model.inference(audio[None, :])

    # Load classifier
    clf, scaler = load_models()
    X = scaler.transform(embedding)          # shape: (1, 1024)
    prob_pest = clf.predict_proba(X)[0][1]   # probability of pest

    # Decision
    pest_detected = prob_pest >= THRESHOLD

    print(f"\n── Detection Result ──────────────────────")
    print(f"Pest probability : {prob_pest:.2%}")
    print(f"Threshold        : {THRESHOLD:.2%}")

    if pest_detected:
        print(f"\n🚨 PEST DETECTED! (confidence: {prob_pest:.2%})")
        print(f"   → Trigger WhatsApp alert to farmer")
    else:
        print(f"\n✅ No pest detected ({prob_pest:.2%} < {THRESHOLD:.0%} threshold)")

    return pest_detected, prob_pest

def main():
    # Get wav path from argument or find latest converted file
    if len(sys.argv) > 1:
        wav_path = sys.argv[1]
        if not os.path.exists(wav_path):
            print(f"❌ File not found: {wav_path}")
            sys.exit(1)
    else:
        # Default: pick latest file in data/converted/
        converted_dir = os.path.join(BASE_DIR, 'data', 'converted')
        wavs = [f for f in os.listdir(converted_dir) if f.endswith('.wav')]
        if not wavs:
            print("❌ No WAV files found in data/converted/")
            print("   Either pass a path: python src/audio_cnn.py path/to/file.wav")
            print("   Or run: python src/convert_audio.py data/raw/")
            sys.exit(1)
        wavs.sort(key=lambda f: os.path.getmtime(os.path.join(converted_dir, f)))
        wav_path = os.path.join(converted_dir, wavs[-1])
        print(f"No file specified — using latest: {wavs[-1]}")

    detect(wav_path)

if __name__ == '__main__':
    main()