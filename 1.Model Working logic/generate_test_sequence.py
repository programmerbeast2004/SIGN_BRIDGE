import os
import shutil

# === CONFIGURATION ===
sentence = "HEY THERE, ARJIT HERE"  # Test sentence
dataset_path = "dataset"  # Root dataset folder
output_folder = "test_sequence"  # Output folder to simulate sequence
# =======================

# Map special characters
char_map = {
    " ": "space",
    ".": "nothing",
    ",": "del"
}

# Clean and recreate output folder
if os.path.exists(output_folder):
    shutil.rmtree(output_folder)
os.makedirs(output_folder)

index = 1

for char in sentence.upper():
    label = char_map.get(char, char)  # map space, del, etc.

    label_folder = os.path.join(dataset_path, label)
    if not os.path.isdir(label_folder):
        print(f"❌ Folder missing for: {label}")
        continue

    # Get image files sorted alphabetically
    images = sorted([f for f in os.listdir(label_folder)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if not images:
        print(f"⚠️ No images found in: {label_folder}")
        continue

    # Take the first image
    first_img = images[0]
    src = os.path.join(label_folder, first_img)
    dst = os.path.join(output_folder, f"{index:02d}_{label}.jpg")

    shutil.copy(src, dst)
    print(f"✅ {index:02d}_{label}.jpg ← {first_img}")
    index += 1

print(f"\n✅ Sentence sequence generated at: {output_folder}/")
