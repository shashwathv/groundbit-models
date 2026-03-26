# debug.py
import tensorflow as tf
import numpy as np
from PIL import Image
from tensorflow.keras.applications.efficientnet import preprocess_input

model = tf.keras.models.load_model('best_model_final.h5')

import json
with open('class_names.json') as f:
    class_names = json.load(f)

def predict_direct(image_path):
    img = Image.open(image_path).convert('RGB').resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    
    preds = model.predict(img_array, verbose=0)
    top5 = sorted(enumerate(preds[0]), key=lambda x: x[1], reverse=True)[:5]
    
    print("\nTop 5 (direct TF, no Core ML):")
    for idx, score in top5:
        print(f"  {class_names[idx]} — {round(score*100,1)}%")

predict_direct('/Users/nate/Projects/groundbit-models/photos/tomato.jpg')
predict_direct('/Users/nate/Projects/groundbit-models/photos/Untitled.jpg')