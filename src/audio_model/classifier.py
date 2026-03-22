"""
train_classifier.py
Trains a binary classifier (pest vs no_pest) on CNN14 embeddings.
Saves pest_classifier.pkl and scaler.pkl to models/
Saves confusion_matrix.png to outputs/

Usage:
    python src/train_classifier.py
"""

import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, roc_auc_score)
import joblib

# ── Paths ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
OUT_DIR    = os.path.join(BASE_DIR, 'outputs')
os.makedirs(OUT_DIR, exist_ok=True)
# ───────────────────────────────────────────────────────

def load_embeddings():
    path = os.path.join(MODELS_DIR, 'embeddings.pkl')
    if not os.path.exists(path):
        raise FileNotFoundError("Run extract_embeddings.py first!")
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data['X'], data['y'], data['classes']

def train():
    X, y, classes = load_embeddings()
    print(f"Loaded {len(X)} samples — classes: {classes}")
    print(f"  pest: {np.sum(y==1)}  |  no_pest: {np.sum(y==0)}\n")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # Try 3 models, pick best
    candidates = {
        'LogisticRegression' : LogisticRegression(max_iter=1000, C=1.0),
        'RandomForest'       : RandomForestClassifier(n_estimators=100, random_state=42),
        'GradientBoosting'   : GradientBoostingClassifier(n_estimators=100, random_state=42),
    }

    print("Comparing models (5-fold cross validation):")
    best_name, best_score, best_model = None, 0, None

    for name, clf in candidates.items():
        cv_scores = cross_val_score(clf, X_scaled, y, cv=5, scoring='f1')
        mean_f1 = cv_scores.mean()
        print(f"  {name:<22} F1 = {mean_f1:.3f}  ±{cv_scores.std():.3f}")
        if mean_f1 > best_score:
            best_score, best_name, best_model = mean_f1, name, clf

    print(f"\n🏆 Best: {best_name} (F1={best_score:.3f})")

    # Train best model on full training set
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    y_prob = best_model.predict_proba(X_test)[:, 1]

    acc     = accuracy_score(y_test, y_pred)
    auc     = roc_auc_score(y_test, y_prob)
    print(f"\nTest Accuracy : {acc:.2%}")
    print(f"Test AUC      : {auc:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=classes))

    # Save confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title(f'Confusion Matrix — {best_name}')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    cm_path = os.path.join(OUT_DIR, 'confusion_matrix.png')
    plt.tight_layout()
    plt.savefig(cm_path)
    plt.close()
    print(f"\n📊 Confusion matrix saved → outputs/confusion_matrix.png")

    # Save model + scaler
    joblib.dump(best_model, os.path.join(MODELS_DIR, 'pest_classifier.pkl'))
    joblib.dump(scaler,     os.path.join(MODELS_DIR, 'scaler.pkl'))
    print(f"✅ Saved pest_classifier.pkl + scaler.pkl → models/")

    # Threshold tuning hint
    print(f"\n💡 Tip: Current threshold = 0.5")
    print(f"   To reduce false alarms → raise threshold to 0.6–0.7 in audio_cnn.py")
    print(f"   To catch more pests    → lower threshold to 0.35–0.4 in audio_cnn.py")

if __name__ == '__main__':
    train()