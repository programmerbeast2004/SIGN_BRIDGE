import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

MODEL_PATH = 'model/sign_model.h5'
LABEL_MAP_PATH = 'model/label_map.npy'
TEST_DIR = 'dataset_test'
IMG_SIZE = 64

# Load model and label map
model = load_model(MODEL_PATH)
label_map = np.load(LABEL_MAP_PATH, allow_pickle=True).item()
idx_to_label = {v: k for k, v in label_map.items()}

correct = 0
total = 0

for label in os.listdir(TEST_DIR):
    label_folder = os.path.join(TEST_DIR, label)
    if not os.path.isdir(label_folder): continue
    for file in os.listdir(label_folder):
        img_path = os.path.join(label_folder, file)
        try:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img = img / 255.0
            img = img.reshape(1, IMG_SIZE, IMG_SIZE, 1)

            prediction = model.predict(img)
            predicted_label = idx_to_label[np.argmax(prediction)]

            if predicted_label == label:
                correct += 1
            total += 1
        except:
            print(f"Skipping: {img_path}")

accuracy = (correct / total) * 100 if total > 0 else 0
print(f"Test Accuracy: {accuracy:.2f}% on {total} images.")
