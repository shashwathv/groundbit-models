"""
Converts raw audio files to 16kHz mono WAV format.
Input:  data/raw/
Output: data/converted/

Usage:
  Single file : python src/convert_audio.py data/raw/audio.mp3
  Whole folder: python src/convert_audio.py data/raw/
"""

import os
import sys
from pydub import AudioSegment

# ─── PATHS ────────────────────────────────────────────
RAW_DIR       = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')
CONVERTED_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'converted')
# ──────────────────────────────────────────────────────

SUPPORTED = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac")


def convert_to_wav(input_path, output_dir=CONVERTED_DIR):
    os.makedirs(output_dir, exist_ok=True)

    base     = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(output_dir, f"{base}_converted.wav")

    print(f"Converting: {input_path}")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(out_path, format="wav")
    print(f"  ✅ Saved → {out_path}")
    return out_path


def batch_convert(folder_path, output_dir=CONVERTED_DIR):
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED)]

    if not files:
        print("❌ No audio files found.")
        return

    for f in files:
        convert_to_wav(os.path.join(folder_path, f), output_dir)

    print(f"\n✅ Done! Converted {len(files)} files → {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file : python src/convert_audio.py data/raw/audio.mp3")
        print("  Whole folder: python src/convert_audio.py data/raw/")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        batch_convert(path)
    else:
        convert_to_wav(path)