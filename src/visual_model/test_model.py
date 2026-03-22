import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input
from PIL import Image
import numpy as np
import json

# Load model and class names
model = tf.keras.models.load_model('best_model_final.h5')
with open('class_names.json') as f:
    class_names = json.load(f)

print(f"Model loaded. {len(class_names)} classes ready.")

def predict_disease(image_path):
    img = Image.open(image_path).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    confidence = float(np.max(predictions))
    class_index = np.argmax(predictions)
    label = class_names[class_index]

    parts = label.split('___')
    crop = parts[0].replace('_', ' ')
    disease = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown'

    return {
        'crop': crop,
        'disease': disease,
        'confidence': round(confidence * 100, 1),
        'is_healthy': 'healthy' in disease.lower()
    }

# Test
result = predict_disease('/home/guts/Projects/groundbit/photos/images.jpg')
print(result)