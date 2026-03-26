# train.py
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

# ── Config ─────────────────────────────────────────────────────────────────────
TRAIN_DIR      = './dataset/train'
VAL_DIR        = './dataset/test'
IMG_SIZE       = (224, 224)
BATCH_SIZE     = 16
EPOCHS_PHASE1  = 15
EPOCHS_PHASE2  = 30
LEARNING_RATE  = 5e-4

# ── Check Metal GPU ────────────────────────────────────────────────────────────
print("\n── System Check ────────────────────────")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ Metal GPU enabled: {len(gpus)} device(s)")
else:
    print("⚠️  No GPU found — running on CPU (will be slow)")
print(f"   TensorFlow version: {tf.__version__}")
print("────────────────────────────────────────\n")

# ── Data Generators ────────────────────────────────────────────────────────────
train_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.3,
    horizontal_flip=True,
    vertical_flip=True,
    brightness_range=[0.7, 1.3],
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input
)

print("Loading dataset...")
train_gen = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

val_gen = val_datagen.flow_from_directory(
    VAL_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False,
    classes=list(train_gen.class_indices.keys())
)

NUM_CLASSES = len(train_gen.class_indices)
print(f"\n✅ Dataset loaded")
print(f"   Classes           : {NUM_CLASSES}")
print(f"   Training samples  : {train_gen.samples}")
print(f"   Validation samples: {val_gen.samples}")

# ── Save class names ───────────────────────────────────────────────────────────
class_names = {v: k for k, v in train_gen.class_indices.items()}
class_list  = [class_names[i] for i in range(NUM_CLASSES)]
with open('class_names.json', 'w') as f:
    json.dump(class_list, f, indent=2)
print("✅ class_names.json saved")

# ── Class weights (handles imbalanced classes) ─────────────────────────────────
labels = train_gen.classes
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(labels),
    y=labels
)
class_weight_dict = dict(enumerate(class_weights))
print("✅ Class weights computed")

# ── Build Model ────────────────────────────────────────────────────────────────
print("\nBuilding model...")
base_model = EfficientNetB0(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
base_model.trainable = False

inputs  = layers.Input(shape=(224, 224, 3))
x       = base_model(inputs, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.BatchNormalization()(x)
x       = layers.Dense(512, activation='relu')(x)
x       = layers.Dropout(0.4)(x)
x       = layers.Dense(256, activation='relu')(x)
x       = layers.Dropout(0.3)(x)
outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)

model = models.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ── Callbacks ──────────────────────────────────────────────────────────────────
callbacks_phase1 = [
    tf.keras.callbacks.ModelCheckpoint(
        'best_model_phase1.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]

callbacks_phase2 = [
    tf.keras.callbacks.ModelCheckpoint(
        'best_model_final.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=7,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-8,
        verbose=1
    )
]

# ── Phase 1: Train top layers only ────────────────────────────────────────────
print(f"\n── Phase 1: Training top layers ({EPOCHS_PHASE1} epochs) ───────────")
history1 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS_PHASE1,
    class_weight=class_weight_dict,
    callbacks=callbacks_phase1
)

# ── Phase 2: Fine-tune full network ───────────────────────────────────────────
print(f"\n── Phase 2: Fine-tuning full network ({EPOCHS_PHASE2} epochs) ──────")
base_model.trainable = True

model.compile(
    optimizer=tf.keras.optimizers.Adam(LEARNING_RATE / 10),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history2 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS_PHASE2,
    class_weight=class_weight_dict,
    callbacks=callbacks_phase2
)

# ── Plot Training Results ──────────────────────────────────────────────────────
acc      = history1.history['accuracy']     + history2.history['accuracy']
val_acc  = history1.history['val_accuracy'] + history2.history['val_accuracy']
loss     = history1.history['loss']         + history2.history['loss']
val_loss = history1.history['val_loss']     + history2.history['val_loss']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(acc,     label='Train Accuracy')
ax1.plot(val_acc, label='Val Accuracy')
ax1.axvline(x=EPOCHS_PHASE1 - 1, color='gray', linestyle='--', label='Fine-tune start')
ax1.set_title('Accuracy')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Accuracy')
ax1.legend()
ax1.grid(True)

ax2.plot(loss,     label='Train Loss')
ax2.plot(val_loss, label='Val Loss')
ax2.axvline(x=EPOCHS_PHASE1 - 1, color='gray', linestyle='--', label='Fine-tune start')
ax2.set_title('Loss')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Loss')
ax2.legend()
ax2.grid(True)

plt.suptitle('Training Results', fontsize=14)
plt.tight_layout()
plt.savefig('training_results.png', dpi=150)
print("\n✅ Training complete!")
print("   Saved: best_model_final.h5")
print("   Saved: best_model_phase1.h5")
print("   Saved: class_names.json")
print("   Saved: training_results.png")

# ── Final Evaluation ───────────────────────────────────────────────────────────
print("\n── Final Evaluation on Validation Set ──")
loss, accuracy = model.evaluate(val_gen, verbose=1)
print(f"   Val Accuracy: {round(accuracy * 100, 2)}%")
print(f"   Val Loss    : {round(loss, 4)}")
print("────────────────────────────────────────")