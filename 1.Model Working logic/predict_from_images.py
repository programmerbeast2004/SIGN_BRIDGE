import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load model and label map
model = load_model('model/sign_model.h5')
label_map = np.load('model/label_map.npy', allow_pickle=True).item()
idx_to_label = {v: k for k, v in label_map.items()}
IMG_SIZE = 64

# Folder containing test images
test_folder = "test_sequence"

# Get sorted image files (e.g., 01_A.jpg, 02_B.jpg for proper order)
image_files = sorted([
    f for f in os.listdir(test_folder)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
])

sentence = ""

print("\n--- Predictions ---")
for filename in image_files:
    path = os.path.join(test_folder, filename)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"❌ Could not load: {filename}")
        continue

    # Preprocess image
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img / 255.0
    img = img.reshape(1, IMG_SIZE, IMG_SIZE, 1)

    prediction = model.predict(img, verbose=0)
    pred_index = np.argmax(prediction)
    pred_class = idx_to_label[pred_index]
    confidence = prediction[0][pred_index]

    # Build sentence without any repeat delay
    sentence += {
        "space": " ",
        "nothing": ".",
        "del": ","
    }.get(pred_class, pred_class)

    print(f"{filename} → {pred_class} ({confidence*100:.2f}%)")

print("\n✅ Final Sentence Prediction:")
print("→", sentence)
