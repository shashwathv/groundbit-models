# test_model.py
import tensorflow as tf
import numpy as np
import json
import time
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input
import sys
import os
os.environ['TF_METAL_DEVICE_PLACEMENT'] = '1'

# Load model
model = tf.keras.models.load_model('best_model_final.h5')
with open('class_names.json') as f:
    class_names = json.load(f)

print(f"✅ Model loaded. {len(class_names)} classes ready.")

def predict_disease(image_path):
    img = Image.open(image_path).convert('RGB').resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)

    start = time.time()
    preds = model.predict(img_array, verbose=0)
    elapsed_ms = (time.time() - start) * 1000

    top5 = sorted(enumerate(preds[0]), key=lambda x: x[1], reverse=True)[:5]

    print("\n── Top 5 Predictions ───────────────")
    for idx, score in top5:
        print(f"  {class_names[idx]} — {round(score*100,1)}%")
    print("────────────────────────────────────")

    confidence = float(preds[0][top5[0][0]])
    label = class_names[top5[0][0]]
    parts = label.split('___')
    crop = parts[0].replace('_', ' ') if len(parts) > 1 else label
    disease = parts[1].replace('_', ' ') if len(parts) > 1 else label

    return {
        'crop': crop,
        'disease': disease,
        'confidence': round(confidence * 100, 1),
        'is_healthy': 'healthy' in label.lower(),
        'inference_ms': round(elapsed_ms, 2)
    }

if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else 'test.jpg'
    print(f"\nRunning prediction on: {image_path}")
    result = predict_disease(image_path)

    print(f"\n── Result ──────────────────────────")
    print(f"  Disease    : {result['disease']}")
    print(f"  Confidence : {result['confidence']}%")
    print(f"  Healthy    : {result['is_healthy']}")
    print(f"  Time       : {result['inference_ms']}ms")
    print(f"────────────────────────────────────")