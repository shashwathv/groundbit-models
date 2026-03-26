# convert_model.py
import tensorflow as tf
import coremltools as ct

print("Loading model...")
model = tf.keras.models.load_model('best_model_final.h5')

# Auto-detect input layer name
input_name = model.input_names[0] if hasattr(model, 'input_names') else model.layers[0].name
print(f"Input layer name: {input_name}")

print("Converting to Core ML...")
coreml_model = ct.convert(
    model,
    inputs=[ct.TensorType(
        name=input_name,
        shape=(1, 224, 224, 3),
    )],
    compute_units=ct.ComputeUnit.ALL
)

coreml_model.save('disease_model.mlpackage')
print("✅ Saved as disease_model.mlpackage")