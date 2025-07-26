import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load model and label map
model = load_model('model/sign_model.h5')
label_map = np.load('model/label_map.npy', allow_pickle=True).item()
idx_to_label = {v: k for k, v in label_map.items()}
IMG_SIZE = 64

# Function to calculate dynamic words per batch based on window size
def get_max_words_per_batch(display_img, font, font_scale, thickness, margin=20):
    height, width = display_img.shape[:2]
    display_width = width - (2 * margin)

    # Test with sample text to estimate character width
    sample_text = "AVERAGE"
    (text_width, text_height), _ = cv2.getTextSize(sample_text, font, font_scale, thickness)
    avg_char_width = text_width / len(sample_text)
    avg_word_length = 6  # Assuming average word length
    space_width = avg_char_width

    # Calculate how many words can fit
    words_per_line = int(display_width / ((avg_word_length * avg_char_width) + space_width))
    return max(1, words_per_line)  # At least 1 word

# Folder with test images
test_folder = "test_sequence"
image_files = sorted([
    f for f in os.listdir(test_folder)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
])

# Sentence logic
current_word = ""
all_words = []
final_sentence = ""
current_batch_index = 0

# Display settings (INCREASED SCALE)
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.0    # 🔼 increased from 0.8
thickness = 2       # ✅ keep or increase to 3 if needed

print("\n--- Simulated Live Test ---")

for filename in image_files:
    path = os.path.join(test_folder, filename)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"❌ Could not load: {filename}")
        continue

    # Preprocess image
    img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    input_img = img_resized / 255.0
    input_img = input_img.reshape(1, IMG_SIZE, IMG_SIZE, 1)

    # Predict
    prediction = model.predict(input_img, verbose=0)
    pred_index = np.argmax(prediction)
    pred_class = idx_to_label[pred_index]
    confidence = prediction[0][pred_index]

    # Handle character logic (WITH PUNCTUATION IN DISPLAY)
    if pred_class == "space":
        if current_word:
            all_words.append(current_word)
            final_sentence += current_word + " "
            current_word = ""
    elif pred_class == "del":
        if current_word:
            all_words.append(current_word + ",")
            final_sentence += current_word + ","
            current_word = ""
    elif pred_class == "nothing":
        if current_word:
            all_words.append(current_word + ".")
            final_sentence += current_word + "."
            current_word = ""
    else:
        current_word += pred_class

    print(f"{filename} → {pred_class} ({confidence*100:.2f}%)")

    # Show image and caption
    display_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    display_img = cv2.resize(display_img, (400, 400))

    # DYNAMIC BATCHING FEATURE - MOVIE CAPTION STYLE
    WORDS_PER_BATCH = get_max_words_per_batch(display_img, font, font_scale, thickness)

    # Calculate current batch
    if len(all_words) % WORDS_PER_BATCH == 0 and len(all_words) > 0:
        current_batch_number = len(all_words) // WORDS_PER_BATCH
        display_batch = []
    else:
        current_batch_number = len(all_words) // WORDS_PER_BATCH
        batch_start = current_batch_number * WORDS_PER_BATCH
        display_batch = all_words[batch_start:]

    # Build caption: batch + current typing word
    caption = " ".join(display_batch)
    if current_word:
        caption += " " + current_word if caption else current_word

    # Display prediction
    cv2.putText(display_img, f"Prediction: {pred_class}", (10, 30),
                font, 1, (0, 255, 0), 2)

    # Batch info
    cv2.putText(display_img, f"Batch {current_batch_number + 1} (Max: {WORDS_PER_BATCH} words)", (10, 60),
                font, 0.6, (255, 255, 0), 1)

    # Show caption with increased font scale
    cv2.putText(display_img, caption, (10, 380),
                font, font_scale, (255, 255, 255), thickness)

    cv2.imshow("Sign Captioning", display_img)
    key = cv2.waitKey(1000)

    if key == ord('q'):
        break
cv2.destroyAllWindows()

print("\n✅ Final Sentence Formed:")
print("→", final_sentence.strip())
