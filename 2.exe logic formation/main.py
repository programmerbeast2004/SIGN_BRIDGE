import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import cv2
import numpy as np
import time
from tensorflow.keras.models import load_model
import mediapipe as mp
import os
import sys
from datetime import datetime
import json
import queue
import pyvirtualcam

# === PATH MANAGEMENT FOR PROJECT STRUCTURE ===
# Get the directory where the main.py script is located
if getattr(sys, 'frozen', False):
    # If running as compiled executable
    base_path = sys._MEIPASS
else:
    # If running as script, get the script's directory
    base_path = os.path.dirname(os.path.abspath(__file__))

# Define paths based on your folder structure
model_path = os.path.join(base_path, "model", "sign_model.h5")
label_map_path = os.path.join(base_path, "model", "label_map.npy")
caption_output_path = os.path.join(base_path, "dist", "caption_output.txt")
settings_path = os.path.join(base_path, "settings.json")
assets_path = os.path.join(base_path, "assets")
icon_path = os.path.join(assets_path, "signbridge_icon.ico")

# Ensure required directories exist
os.makedirs(os.path.dirname(caption_output_path), exist_ok=True)
os.makedirs(assets_path, exist_ok=True)

# === LOAD MODEL WITH BETTER ERROR HANDLING ===
model_loaded = False
model = None
label_map = None
idx_to_label = None
IMG_SIZE = 64

def load_ai_model():
    global model, label_map, idx_to_label, model_loaded
    try:
        print(f"Loading model from: {model_path}")
        print(f"Loading label map from: {label_map_path}")
        
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}")
            return False
            
        if not os.path.exists(label_map_path):
            print(f"Error: Label map file not found at {label_map_path}")
            return False
        
        model = load_model(model_path)
        label_map = np.load(label_map_path, allow_pickle=True).item()
        idx_to_label = {v: k for k, v in label_map.items()}
        model_loaded = True
        print("✅ AI Model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        model_loaded = False
        return False

# Try to load the model
load_ai_model()

# === SETTINGS ===
default_settings = {
    "confidence_threshold": 0.8,
    "display_interval": 2.5,
    "max_caption_length": 35,
    "auto_save": True,
    "dark_mode": True,
    "show_confidence": True,
    "camera_index": 0
}

def load_settings():
    try:
        with open(settings_path, 'r') as f:
            return {**default_settings, **json.load(f)}
    except:
        return default_settings.copy()

def save_settings(settings):
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

settings = load_settings()

# === STATE VARIABLES ===
is_running = False
cap = None
hands = None
current_word = ""
caption_words = []
next_caption_words = []
display_caption = ""
last_display_time = 0
prediction_buffer = []
prev_prediction = ""
frame_threshold = 15
repeat_delay = 2
last_update_time = time.time()
session_stats = {"translations": 0, "words": 0, "session_start": None}
translation_history = []

# === UI ELEMENTS ===
root = None
status_label = None
prediction_label = None
translation_text = None
confidence_label = None
stats_frame = None
progress_var = None

# === THREAD-SAFE GUI UPDATE QUEUE ===
gui_queue = queue.Queue()

# === THEME COLORS ===
COLORS = {
    "bg_primary": "#0F172A",
    "bg_secondary": "#1E293B",
    "bg_tertiary": "#334155",
    "accent_primary": "#3B82F6",
    "accent_secondary": "#10B981",
    "accent_danger": "#EF4444",
    "accent_warning": "#F59E0B",
    "text_primary": "#F8FAFC",
    "text_secondary": "#CBD5E1",
    "text_muted": "#64748B",
    "border": "#475569"
}

# === THREAD-SAFE GUI UPDATE FUNCTIONS ===
def process_gui_queue():
    """Process GUI update queue to handle thread-safe updates"""
    try:
        while True:
            try:
                func, args = gui_queue.get_nowait()
                func(*args)
            except queue.Empty:
                break
    except Exception as e:
        print(f"GUI queue processing error: {e}")
    
    # Schedule next check
    if root:
        root.after(100, process_gui_queue)

def queue_gui_update(func, *args):
    """Queue a GUI update to be processed on the main thread"""
    gui_queue.put((func, args))

# === ENHANCED DETECTION LOGIC ===
def run_detection():
    global cap, hands, is_running
    global current_word, caption_words, next_caption_words, display_caption
    global last_display_time, prediction_buffer, prev_prediction, last_update_time
    global session_stats

    if not model_loaded:
        queue_gui_update(messagebox.showerror, "Error", "AI Model not loaded. Please check model files.")
        return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False, 
        max_num_hands=1,
        min_detection_confidence=0.7, 
        min_tracking_confidence=0.7
    )

    cap = cv2.VideoCapture(settings["camera_index"])
    if not cap.isOpened():
        queue_gui_update(messagebox.showerror, "Camera Error", "Could not access camera. Please check camera permissions.")
        return

    # Set camera properties for better quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    session_stats["session_start"] = datetime.now()
    queue_gui_update(update_status, "🟢 Camera Active", COLORS["accent_secondary"])
    queue_gui_update(update_stats)

    # Create named OpenCV window for OBS
    cv2.namedWindow("SignBridge Live", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("SignBridge Live", 1280, 720)

    while is_running:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame from camera.")
            break

        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        hand_roi = None
        current_prediction = "None"
        confidence = 0.0

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Extract hand region with better padding
                x_coords = [lm.x for lm in hand_landmarks.landmark]
                y_coords = [lm.y for lm in hand_landmarks.landmark]
                x_min = int(min(x_coords) * w) - 30
                x_max = int(max(x_coords) * w) + 30
                y_min = int(min(y_coords) * h) - 30
                y_max = int(max(y_coords) * h) + 30
                x_min, y_min = max(x_min, 0), max(y_min, 0)
                x_max, y_max = min(x_max, w), min(y_max, h)
                hand_roi = frame[y_min:y_max, x_min:x_max]
                
                # Enhanced visual feedback
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (64, 224, 255), 3)
                cv2.circle(frame, (int((x_min + x_max) / 2), y_min - 10), 5, (64, 224, 255), -1)
                break
        else:
            current_prediction = "No hand detected"
            display_enhanced_overlay(frame, current_prediction, 0.0)
            cv2.imshow("SignBridge Live", frame)  # Display frame in OpenCV window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        if hand_roi is not None and hand_roi.size > 0:
            # Enhanced preprocessing
            gray = cv2.cvtColor(hand_roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (IMG_SIZE, IMG_SIZE))
            gray = gray / 255.0
            gray = gray.reshape(1, IMG_SIZE, IMG_SIZE, 1)
            
            prediction = model.predict(gray, verbose=0)
            confidence = float(np.max(prediction))
            pred_class = idx_to_label[np.argmax(prediction)]
            current_prediction = pred_class

            # Only process if confidence is above threshold
            if confidence >= settings["confidence_threshold"]:
                prediction_buffer.append(pred_class)
                if len(prediction_buffer) > frame_threshold:
                    prediction_buffer.pop(0)

                if prediction_buffer.count(pred_class) > frame_threshold * 0.8:
                    current_time = time.time()
                    if pred_class != prev_prediction or (current_time - last_update_time > repeat_delay):
                        process_prediction(pred_class)
                        prev_prediction = pred_class
                        last_update_time = current_time

            # Update caption display logic
            time_elapsed = time.time() - last_display_time
            total_len = sum(len(w) for w in next_caption_words)
            if ((total_len >= settings["max_caption_length"] or 
                 len(next_caption_words) >= 1 or 
                 time_elapsed >= settings["display_interval"]) and next_caption_words):
                update_display_caption()

        # Update UI elements using thread-safe method
        queue_gui_update(update_prediction_display, current_prediction, confidence)
        display_enhanced_overlay(frame, current_prediction, confidence)
        
        # Show the frame in OpenCV window
        cv2.imshow("SignBridge Live", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cleanup_camera()
    cv2.destroyAllWindows()
def process_prediction(pred_class):
    global current_word, next_caption_words, session_stats
    
    if pred_class in ["space", "nothing", "del"]:
        if current_word.strip():
            end_char = {"space": " ", "nothing": ".", "del": ","}.get(pred_class, "")
            next_caption_words.append(current_word + end_char)
            current_word = ""
            session_stats["words"] += 1
    else:
        current_word += pred_class

def update_display_caption():
    global caption_words, display_caption, next_caption_words, last_display_time, session_stats
    
    caption_words = next_caption_words.copy()
    display_caption = "".join(caption_words).strip()
    next_caption_words.clear()
    last_display_time = time.time()
    session_stats["translations"] += 1

    if translation_text and display_caption:
        def update_translation_text():
            # Get existing content from the text widget
            existing_content = translation_text.get(1.0, tk.END).strip()
            
            # Append new translation with space separator
            if existing_content:
                updated_content = existing_content + " " + display_caption
            else:
                updated_content = display_caption
            
            # Update the text widget
            translation_text.delete(1.0, tk.END)
            translation_text.insert(1.0, updated_content)
            
            # ALWAYS update caption_output.txt with the FULL content for OBS
            save_translation_to_file(updated_content)
        
        queue_gui_update(update_translation_text)
        
        # Add to history
        translation_history.append({
            "text": display_caption,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "word_count": len(display_caption.split())
        })
    
    queue_gui_update(update_stats)

def display_enhanced_overlay(frame, prediction, confidence):
    if display_caption:
        # Create semi-transparent overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Background box
        cv2.rectangle(overlay, (0, h - 80), (w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Main caption text
        text_size = cv2.getTextSize(display_caption, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        text_x = (w - text_size[0]) // 2
        cv2.putText(frame, display_caption, (text_x, h - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    # Prediction and confidence display
    pred_text = f"Detecting: {prediction}"
    conf_text = f"Confidence: {confidence:.2%}" if confidence > 0 else ""
    
    cv2.putText(frame, pred_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (64, 224, 255), 2)
    if conf_text and settings["show_confidence"]:
        color = (0, 255, 0) if confidence >= settings["confidence_threshold"] else (0, 165, 255)
        cv2.putText(frame, conf_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def cleanup_camera():
    global cap, is_running
    is_running = False
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    queue_gui_update(update_status, "🔴 Camera Inactive", COLORS["accent_danger"])

def save_translation_to_file(text):
    """Save translation to the main caption_output.txt file for OBS integration"""
    try:
        with open(caption_output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Caption updated in OBS file: {text[:50]}...")
    except Exception as e:
        print(f"[ERROR] Could not write to caption_output.txt: {e}")

def append_to_caption_file(text):
    """Append new translation to caption_output.txt (for cumulative display)"""
    try:
        # Read existing content
        existing_content = ""
        if os.path.exists(caption_output_path):
            with open(caption_output_path, "r", encoding="utf-8") as f:
                existing_content = f.read().strip()
        
        # Append new text with space separator
        if existing_content:
            updated_content = existing_content + " " + text
        else:
            updated_content = text
        
        # Write back the combined content
        with open(caption_output_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        print(f"✅ Caption appended to OBS file: {text[:30]}...")
        return updated_content
    except Exception as e:
        print(f"[ERROR] Could not append to caption_output.txt: {e}")
        return text

def clear_caption_file():
    """Clear the caption_output.txt file"""
    try:
        with open(caption_output_path, "w", encoding="utf-8") as f:
            f.write("")
        print("✅ Caption file cleared for new session")
    except Exception as e:
        print(f"[ERROR] Could not clear caption_output.txt: {e}")

# === UI UPDATE FUNCTIONS ===
def update_status(text, color):
    if status_label:
        status_label.config(text=text, fg=color)

def update_prediction_display(prediction, confidence):
    if prediction_label:
        prediction_label.config(text=f"Current: {prediction}")
    if confidence_label and settings["show_confidence"]:
        conf_text = f"Confidence: {confidence:.1%}" if confidence > 0 else "Confidence: --"
        color = COLORS["accent_secondary"] if confidence >= settings["confidence_threshold"] else COLORS["accent_warning"]
        confidence_label.config(text=conf_text, fg=color)

def update_stats():
    if stats_frame and session_stats["session_start"]:
        duration = datetime.now() - session_stats["session_start"]
        duration_str = str(duration).split('.')[0]  # Remove microseconds
        
        stats_text = f"Session: {duration_str} | Translations: {session_stats['translations']} | Words: {session_stats['words']}"
        for widget in stats_frame.winfo_children():
            if isinstance(widget, tk.Label) and "Session:" in widget.cget("text"):
                widget.config(text=stats_text)
                break

# === MAIN FUNCTIONS ===
def start_translation():
    global is_running
    if not is_running:
        # Clear the caption file for a fresh start
        clear_caption_file()
        is_running = True
        threading.Thread(target=run_detection, daemon=True).start()
        show_obs_info()

def stop_translation():
    global is_running
    is_running = False

def show_obs_info():
    """Show OBS integration instructions"""
    info_text = """🎥 OBS Studio Integration Guide

✅ Virtual Camera:

1.Open OBS Studio
2.Click ➕ in Sources → select Window Capture
3.Name it anything (e.g. SignBridge Window) → click OK
4.In the Window dropdown, select:
[python.exe]: SignBridge Live
5.Set Window Match Priority to:
Match title, otherwise find window of same executable
6.Click OK
7.Resize or crop the window as needed
8.Go to Scene Collection and Profile → click Save
9.Done — OBS will now auto-detect the window every time you launch SignBridge

💡 Real-time Updates:
• Virtual camera updates automatically.
• Window sharing reflects the app's display.

📁 File Location for Captions: """ + caption_output_path
    
    messagebox.showinfo("OBS Integration", info_text)
def show_instructions():
    instructions_window = tk.Toplevel(root)
    instructions_window.title("SignBridge Pro - Instructions")
    instructions_window.geometry("600x500")
    instructions_window.configure(bg=COLORS["bg_primary"])
    instructions_window.resizable(False, False)
    
    # Make window modal
    instructions_window.transient(root)
    instructions_window.grab_set()
    
    # Title
    title_label = tk.Label(instructions_window, text="📚 How to Use SignBridge Pro", 
                          font=("Segoe UI", 16, "bold"), 
                          bg=COLORS["bg_primary"], fg=COLORS["text_primary"])
    title_label.pack(pady=20)
    
    # Instructions text
    instructions_text = """
🚀 GETTING STARTED:
1. Click 'Start Translation' to activate the camera and overlay.
2. Perform sign language gestures in front of your webcam.
3. The translation will appear in this app's window.

✋ SIGN LANGUAGE TIPS:
• Keep your hand well-lit and visible
• Make clear, deliberate movements
• Wait for the system to recognize each sign
• Use 'space' gesture to separate words
• Use 'nothing' gesture to end sentences

⚙️ SPECIAL GESTURES:
• Space: Adds a space between words
• Nothing: Adds a period (.) to end sentences
• Del: Adds a comma (,) for pauses

🎥 TO USE WITH OBS OR VIDEO CALLS:
• In OBS, add a 'Window Capture' source and select this app's window.
• Position and crop as needed in your OBS scene.
• For video calls, share this app's window directly.

📊 FEATURES:
• Real-time confidence scoring
• Translation history tracking
• Customizable settings
• Auto-save functionality
• Session statistics

💡 TROUBLESHOOTING:
• Ensure good lighting conditions
• Check camera permissions
• Adjust confidence threshold in settings
• Restart if camera feed freezes

🔧 SETTINGS:
Access the Settings menu to customize:
- Confidence threshold
- Display timing
- Camera selection
- Auto-save options
"""
    
    text_widget = tk.Text(instructions_window, font=("Segoe UI", 11), 
                         bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                         wrap='word', padx=20, pady=20, 
                         insertbackground=COLORS["text_primary"],
                         selectbackground=COLORS["accent_primary"])
    text_widget.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    text_widget.insert(1.0, instructions_text)
    text_widget.config(state='disabled')  # Make read-only
    
    # Close button
    close_btn = tk.Button(instructions_window, text="✅ Got it!", 
                         command=instructions_window.destroy,
                         bg=COLORS["accent_secondary"], fg="white", 
                         font=("Segoe UI", 12, "bold"),
                         padx=30, pady=10, relief="flat")
    close_btn.pack(pady=(0,20))


def show_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("SignBridge Pro - Settings")
    settings_window.geometry("500x600")
    settings_window.configure(bg=COLORS["bg_primary"])
    settings_window.resizable(False, False)
    
    # Make window modal
    settings_window.transient(root)
    settings_window.grab_set()
    
    # Title
    title_label = tk.Label(settings_window, text="⚙️ Settings", 
                          font=("Segoe UI", 16, "bold"), 
                          bg=COLORS["bg_primary"], fg=COLORS["text_primary"])
    title_label.pack(pady=20)
    
    # Settings frame
    settings_frame = tk.Frame(settings_window, bg=COLORS["bg_primary"])
    settings_frame.pack(fill='both', expand=True, padx=20)
    
    # Confidence threshold
    conf_frame = tk.Frame(settings_frame, bg=COLORS["bg_primary"])
    conf_frame.pack(fill='x', pady=10)
    tk.Label(conf_frame, text="Confidence Threshold:", 
             bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
             font=("Segoe UI", 11)).pack(anchor='w')
    conf_var = tk.DoubleVar(value=settings["confidence_threshold"])
    conf_scale = tk.Scale(conf_frame, from_=0.5, to=1.0, resolution=0.1, 
                         orient='horizontal', variable=conf_var,
                         bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                         highlightbackground=COLORS["bg_primary"])
    conf_scale.pack(fill='x', pady=5)
    
    # Display interval
    interval_frame = tk.Frame(settings_frame, bg=COLORS["bg_primary"])
    interval_frame.pack(fill='x', pady=10)
    tk.Label(interval_frame, text="Display Interval (seconds):", 
             bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
             font=("Segoe UI", 11)).pack(anchor='w')
    interval_var = tk.DoubleVar(value=settings["display_interval"])
    interval_scale = tk.Scale(interval_frame, from_=1.0, to=5.0, resolution=0.5, 
                             orient='horizontal', variable=interval_var,
                             bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                             highlightbackground=COLORS["bg_primary"])
    interval_scale.pack(fill='x', pady=5)
    
    # Max caption length
    length_frame = tk.Frame(settings_frame, bg=COLORS["bg_primary"])
    length_frame.pack(fill='x', pady=10)
    tk.Label(length_frame, text="Max Caption Length:", 
             bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
             font=("Segoe UI", 11)).pack(anchor='w')
    length_var = tk.IntVar(value=settings["max_caption_length"])
    length_scale = tk.Scale(length_frame, from_=20, to=100, resolution=5, 
                           orient='horizontal', variable=length_var,
                           bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                           highlightbackground=COLORS["bg_primary"])
    length_scale.pack(fill='x', pady=5)
    
    # Checkboxes
    auto_save_var = tk.BooleanVar(value=settings["auto_save"])
    show_conf_var = tk.BooleanVar(value=settings["show_confidence"])
    virtual_cam_var = tk.BooleanVar(value=settings.get("virtual_camera", False))  # Default: Virtual camera off
    
    tk.Checkbutton(settings_frame, text="Auto-save translations", variable=auto_save_var,
                   bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
                   selectcolor=COLORS["bg_secondary"],
                   font=("Segoe UI", 11)).pack(anchor='w', pady=5)
    
    tk.Checkbutton(settings_frame, text="Show confidence scores", variable=show_conf_var,
                   bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
                   selectcolor=COLORS["bg_secondary"],
                   font=("Segoe UI", 11)).pack(anchor='w', pady=5)
    
    tk.Checkbutton(settings_frame, text="Enable Virtual Camera", variable=virtual_cam_var,
                   bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
                   selectcolor=COLORS["bg_secondary"],
                   font=("Segoe UI", 11)).pack(anchor='w', pady=5)
    
    # Camera selection
    camera_frame = tk.Frame(settings_frame, bg=COLORS["bg_primary"])
    camera_frame.pack(fill='x', pady=10)
    tk.Label(camera_frame, text="Camera Index:", 
             bg=COLORS["bg_primary"], fg=COLORS["text_primary"], 
             font=("Segoe UI", 11)).pack(anchor='w')
    camera_var = tk.IntVar(value=settings["camera_index"])
    camera_spin = tk.Spinbox(camera_frame, from_=0, to=5, textvariable=camera_var,
                            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                            font=("Segoe UI", 11))
    camera_spin.pack(fill='x', pady=5)
    
    def save_and_close():
        global settings
        settings.update({
            "confidence_threshold": conf_var.get(),
            "display_interval": interval_var.get(),
            "max_caption_length": length_var.get(),
            "auto_save": auto_save_var.get(),
            "show_confidence": show_conf_var.get(),
            "virtual_camera": virtual_cam_var.get(),  # Save virtual camera setting
            "camera_index": camera_var.get()
        })
        save_settings(settings)
        settings_window.destroy()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    # Buttons
    btn_frame = tk.Frame(settings_window, bg=COLORS["bg_primary"])
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="💾 Save Settings", command=save_and_close,
              bg=COLORS["accent_secondary"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)
    
    tk.Button(btn_frame, text="❌ Cancel", command=settings_window.destroy,
              bg=COLORS["accent_danger"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)
    def save_and_close():
        global settings
        settings.update({
            "confidence_threshold": conf_var.get(),
            "display_interval": interval_var.get(),
            "max_caption_length": length_var.get(),
            "auto_save": auto_save_var.get(),
            "show_confidence": show_conf_var.get(),
            "camera_index": camera_var.get()
        })
        save_settings(settings)
        settings_window.destroy()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    # Buttons
    btn_frame = tk.Frame(settings_window, bg=COLORS["bg_primary"])
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="💾 Save Settings", command=save_and_close,
              bg=COLORS["accent_secondary"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)
    
    tk.Button(btn_frame, text="❌ Cancel", command=settings_window.destroy,
              bg=COLORS["accent_danger"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)

def setup_meeting_mode():
    """Configure optimized settings for real-time meetings"""
    global settings
    
    meeting_settings = {
        "confidence_threshold": 0.75,  # Balanced for meeting pace
        "display_interval": 1.5,       # Quick updates for conversations
        "max_caption_length": 25,      # Short phrases for readability
        "auto_save": True,             # Always save for OBS
        "show_confidence": False,      # Clean interface for meetings
        "camera_index": settings.get("camera_index", 0)
    }
    
    if messagebox.askyesno("Meeting Mode", 
                          """🎯 Enable Meeting Mode?

This will optimize settings for real-time video calls:

• Quick response time (1.5s)
• Clean short phrases (25 chars)
• No confidence scores shown
• Auto-save enabled for OBS
• Balanced accuracy (75%)

Your current settings will be backed up."""):
        
        # Backup current settings
        backup_settings = settings.copy()
        backup_path = os.path.join(base_path, "settings_backup.json")
        try:
            with open(backup_path, 'w') as f:
                json.dump(backup_settings, f, indent=2)
        except Exception as e:
            print(f"Could not backup settings: {e}")
        
        # Apply meeting settings
        settings.update(meeting_settings)
        save_settings(settings)
        
        messagebox.showinfo("Meeting Mode", 
                           """✅ Meeting Mode Activated!

Settings optimized for:
• Video conferences
• Real-time conversations  
• OBS integration
• Clean overlay display

Your previous settings are backed up as 'settings_backup.json'

Restart translation for settings to take effect.""")
        
        return True
    return False

def restore_settings_backup():
    """Restore settings from backup"""
    global settings
    backup_path = os.path.join(base_path, "settings_backup.json")
    
    if os.path.exists(backup_path):
        if messagebox.askyesno("Restore Settings", "Restore your previous settings from backup?"):
            try:
                with open(backup_path, 'r') as f:
                    backup_settings = json.load(f)
                settings.update(backup_settings)
                save_settings(settings)
                messagebox.showinfo("Settings Restored", "Your previous settings have been restored!")
                return True
            except Exception as e:
                messagebox.showerror("Restore Error", f"Could not restore settings: {e}")
    else:
        messagebox.showwarning("No Backup", "No settings backup file found.")
    return False

def show_history():
    """Show translation history in a new window"""
    history_window = tk.Toplevel(root)
    history_window.title("SignBridge Pro - Translation History")
    history_window.geometry("700x500")
    history_window.configure(bg=COLORS["bg_primary"])
    
    # Make window modal
    history_window.transient(root)
    history_window.grab_set()
    
    # Title
    title_label = tk.Label(history_window, text="📜 Translation History", 
                          font=("Segoe UI", 16, "bold"), 
                          bg=COLORS["bg_primary"], fg=COLORS["text_primary"])
    title_label.pack(pady=20)
    
    # Create treeview for history
    columns = ("Time", "Translation", "Words")
    tree = ttk.Treeview(history_window, columns=columns, show="headings", height=15)
    
    # Configure columns
    tree.heading("Time", text="Time")
    tree.heading("Translation", text="Translation")
    tree.heading("Words", text="Words")
    
    tree.column("Time", width=100)
    tree.column("Translation", width=400)
    tree.column("Words", width=80)
    
    # Add data
    for item in translation_history:
        tree.insert("", "end", values=(item["timestamp"], item["text"], item["word_count"]))
    
    tree.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    
    # Buttons
    btn_frame = tk.Frame(history_window, bg=COLORS["bg_primary"])
    btn_frame.pack(pady=(0, 20))
    
    def export_history():
        if not translation_history:
            messagebox.showwarning("Export", "No translation history to export!")
            return
        
        # Ask user what type of export they want
        export_type = messagebox.askyesnocancel("Export History", 
            """Choose export type:

✅ YES = Export to separate backup file
❌ NO = Update main OBS caption file with full history  
🚫 CANCEL = Cancel export""")
        
        if export_type is None:  # Cancel
            return
        elif export_type:  # YES - Export to separate file
            default_filename = f"signbridge_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filename = filedialog.asksaveasfilename(
                initialdir=base_path,
                initialfile=default_filename,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Translation History"
            )
            if filename:
                try:
                    if filename.endswith('.json'):
                        # Export as JSON for structured data
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump({
                                "export_info": {
                                    "app": "SignBridge Pro",
                                    "version": "2.0",
                                    "export_date": datetime.now().isoformat(),
                                    "total_translations": len(translation_history)
                                },
                                "translations": translation_history
                            }, f, indent=2, ensure_ascii=False)
                    else:
                        # Export as text
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write("SignBridge Pro - Translation History\n")
                            f.write("=" * 50 + "\n")
                            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Total Translations: {len(translation_history)}\n")
                            f.write("=" * 50 + "\n\n")
                            for i, item in enumerate(translation_history, 1):
                                f.write(f"Translation #{i}\n")
                                f.write(f"Time: {item['timestamp']}\n")
                                f.write(f"Text: {item['text']}\n")
                                f.write(f"Word Count: {item['word_count']}\n")
                                f.write("-" * 30 + "\n")
                    messagebox.showinfo("Export", f"History exported successfully to:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export history:\n{str(e)}")
        else:  # NO - Update main OBS file with full history
            try:
                # Combine all translations into one text
                full_history_text = " ".join([item["text"] for item in translation_history])
                save_translation_to_file(full_history_text)
                
                # Also update the main text widget
                if translation_text:
                    translation_text.delete(1.0, tk.END)
                    translation_text.insert(1.0, full_history_text)
                
                messagebox.showinfo("History Updated", 
                    f"✅ Full translation history saved to OBS file:\n{caption_output_path}\n\nOBS will now show the complete session text!")
            except Exception as e:
                messagebox.showerror("Update Error", f"Failed to update OBS file:\n{str(e)}")
    
    def clear_history():
        global translation_history
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all translation history?"):
            translation_history.clear()
            tree.delete(*tree.get_children())
            # Also clear the main caption file
            clear_caption_file()
            if translation_text:
                translation_text.delete(1.0, tk.END)
            messagebox.showinfo("Cleared", "History and OBS caption file cleared!")
    
    tk.Button(btn_frame, text="📤 Export", command=export_history,
              bg=COLORS["accent_primary"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)
    
    tk.Button(btn_frame, text="🗑️ Clear", command=clear_history,
              bg=COLORS["accent_danger"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)
    
    tk.Button(btn_frame, text="✅ Close", command=history_window.destroy,
              bg=COLORS["bg_tertiary"], fg="white", 
              font=("Segoe UI", 11, "bold"), padx=20, pady=8, relief="flat").pack(side='left', padx=10)

def on_closing():
    global is_running
    if messagebox.askokcancel("Quit", "Do you want to quit SignBridge Pro?"):
        is_running = False
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        root.quit()
        root.destroy()

# === ENHANCED GUI SETUP ===
def create_gui():
    global root, status_label, prediction_label, translation_text, confidence_label, stats_frame

    root = tk.Tk()
    root.title("SignBridge Pro - AI Sign Language Translator")
    root.geometry("1000x700")
    root.configure(bg=COLORS["bg_primary"])
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.resizable(True, True)
    
    # Set window icon if available
    try:
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
            print(f"✅ Window icon loaded from: {icon_path}")
    except Exception as e:
        print(f"Could not load icon: {e}")

    # Start GUI queue processing
    root.after(100, process_gui_queue)

    # Create main container
    main_container = tk.Frame(root, bg=COLORS["bg_primary"])
    main_container.pack(fill='both', expand=True, padx=20, pady=20)

    # Header section
    header_frame = tk.Frame(main_container, bg=COLORS["bg_secondary"], relief="flat", bd=2)
    header_frame.pack(fill='x', pady=(0, 20))

    # Title with icon
    title_frame = tk.Frame(header_frame, bg=COLORS["bg_secondary"])
    title_frame.pack(pady=20)
    
    title_label = tk.Label(title_frame, text="🤟 SignBridge Pro", 
                          font=("Segoe UI", 24, "bold"), 
                          bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
    title_label.pack()
    
    subtitle_label = tk.Label(title_frame, text="Real-time AI Sign Language Translation", 
                             font=("Segoe UI", 12), 
                             bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
    subtitle_label.pack()

    # Status section
    status_frame = tk.Frame(main_container, bg=COLORS["bg_secondary"], relief="flat", bd=2)
    status_frame.pack(fill='x', pady=(0, 20))

    # Status indicators
    indicators_frame = tk.Frame(status_frame, bg=COLORS["bg_secondary"])
    indicators_frame.pack(pady=15)

    status_label = tk.Label(indicators_frame, text="🔴 Camera Inactive", 
                           font=("Segoe UI", 14, "bold"), 
                           bg=COLORS["bg_secondary"], fg=COLORS["accent_danger"])
    status_label.pack(side='left', padx=20)

    prediction_label = tk.Label(indicators_frame, text="Current: None", 
                               font=("Segoe UI", 12), 
                               bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
    prediction_label.pack(side='left', padx=20)

    if settings["show_confidence"]:
        confidence_label = tk.Label(indicators_frame, text="Confidence: --", 
                                   font=("Segoe UI", 12), 
                                   bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        confidence_label.pack(side='left', padx=20)

    # Control buttons section
    controls_frame = tk.Frame(main_container, bg=COLORS["bg_secondary"], relief="flat", bd=2)
    controls_frame.pack(fill='x', pady=(0, 20))

    buttons_frame = tk.Frame(controls_frame, bg=COLORS["bg_secondary"])
    buttons_frame.pack(pady=20)

    # Main control buttons
    start_btn = tk.Button(buttons_frame, text="🎥 Start Translation", 
                         command=start_translation,
                         bg=COLORS["accent_secondary"], fg="white", 
                         font=("Segoe UI", 14, "bold"),
                         padx=30, pady=12, relief="flat",
                         cursor="hand2")
    start_btn.pack(side='left', padx=10)

    stop_btn = tk.Button(buttons_frame, text="⏹️ Stop Translation", 
                        command=stop_translation,
                        bg=COLORS["accent_danger"], fg="white", 
                        font=("Segoe UI", 14, "bold"),
                        padx=30, pady=12, relief="flat",
                        cursor="hand2")
    stop_btn.pack(side='left', padx=10)

    # Secondary control buttons
    secondary_buttons_frame = tk.Frame(controls_frame, bg=COLORS["bg_secondary"])
    secondary_buttons_frame.pack(pady=(0, 15))

    instructions_btn = tk.Button(secondary_buttons_frame, text="📚 Instructions", 
                                command=show_instructions,
                                bg=COLORS["accent_primary"], fg="white", 
                                font=("Segoe UI", 11, "bold"),
                                padx=20, pady=8, relief="flat",
                                cursor="hand2")
    instructions_btn.pack(side='left', padx=5)

    settings_btn = tk.Button(secondary_buttons_frame, text="⚙️ Settings", 
                            command=show_settings,
                            bg=COLORS["bg_tertiary"], fg="white", 
                            font=("Segoe UI", 11, "bold"),
                            padx=20, pady=8, relief="flat",
                            cursor="hand2")
    settings_btn.pack(side='left', padx=5)

    history_btn = tk.Button(secondary_buttons_frame, text="📜 History", 
                           command=show_history,
                           bg=COLORS["bg_tertiary"], fg="white", 
                           font=("Segoe UI", 11, "bold"),
                           padx=20, pady=8, relief="flat",
                           cursor="hand2")
    history_btn.pack(side='left', padx=5)

    meeting_btn = tk.Button(secondary_buttons_frame, text="🎯 Meeting Mode", 
                           command=setup_meeting_mode,
                           bg=COLORS["accent_secondary"], fg="white", 
                           font=("Segoe UI", 11, "bold"),
                           padx=20, pady=8, relief="flat",
                           cursor="hand2")
    meeting_btn.pack(side='left', padx=5)

    restore_btn = tk.Button(secondary_buttons_frame, text="🔄 Restore", 
                           command=restore_settings_backup,
                           bg=COLORS["bg_tertiary"], fg="white", 
                           font=("Segoe UI", 11, "bold"),
                           padx=20, pady=8, relief="flat",
                           cursor="hand2")
    restore_btn.pack(side='left', padx=5)

    def clear_translation():
        if translation_text:
            translation_text.delete(1.0, tk.END)
        # Also clear the caption file for OBS
        clear_caption_file()
        global display_caption, current_word, caption_words, next_caption_words
        display_caption = ""
        current_word = ""
        caption_words.clear()
        next_caption_words.clear()

    def save_translation():
        if translation_text:
            content = translation_text.get(1.0, tk.END).strip()
            if content:
                # Update caption_output.txt with current content (for OBS)
                save_translation_to_file(content)
                
                # Ask if user wants to ALSO export to a separate backup file
                export_choice = messagebox.askyesno("Save Options", 
                    f"""✅ Current translation saved to OBS file:
{caption_output_path}

Would you like to ALSO export a backup copy to a separate file?""")
                
                if export_choice:
                    default_filename = f"signbridge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    filename = filedialog.asksaveasfilename(
                        initialdir=base_path,
                        initialfile=default_filename,
                        defaultextension=".txt",
                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                        title="Export Backup Copy"
                    )
                    if filename:
                        try:
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(f"SignBridge Pro Translation Backup\n")
                                f.write("=" * 40 + "\n")
                                f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"Word Count: {len(content.split())}\n")
                                f.write("=" * 40 + "\n\n")
                                f.write(content)
                            messagebox.showinfo("Backup Saved", f"Backup copy saved to:\n{filename}")
                        except Exception as e:
                            messagebox.showerror("Backup Error", f"Failed to save backup:\n{str(e)}")
                else:
                    messagebox.showinfo("Saved", f"Translation is live in OBS file:\n{caption_output_path}")
            else:
                messagebox.showwarning("Save", "No translation content to save!")

    clear_btn = tk.Button(secondary_buttons_frame, text="🗑️ Clear", 
                         command=clear_translation,
                         bg=COLORS["accent_warning"], fg="white", 
                         font=("Segoe UI", 11, "bold"),
                         padx=20, pady=8, relief="flat",
                         cursor="hand2")
    clear_btn.pack(side='left', padx=5)

    save_btn = tk.Button(secondary_buttons_frame, text="💾 Save", 
                        command=save_translation,
                        bg=COLORS["accent_primary"], fg="white", 
                        font=("Segoe UI", 11, "bold"),
                        padx=20, pady=8, relief="flat",
                        cursor="hand2")
    save_btn.pack(side='left', padx=5)

    # Translation display section
    translation_frame = tk.Frame(main_container, bg=COLORS["bg_secondary"], relief="flat", bd=2)
    translation_frame.pack(fill='both', expand=True, pady=(0, 20))

    # Translation header
    trans_header = tk.Frame(translation_frame, bg=COLORS["bg_secondary"])
    trans_header.pack(fill='x', pady=15)

    tk.Label(trans_header, text="📝 Real-time Translation", 
             font=("Segoe UI", 16, "bold"), 
             bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]).pack(side='left', padx=20)

    # Word count indicator
    word_count_label = tk.Label(trans_header, text="Words: 0", 
                               font=("Segoe UI", 11), 
                               bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
    word_count_label.pack(side='right', padx=20)

    # Translation text area with scrollbar
    text_container = tk.Frame(translation_frame, bg=COLORS["bg_secondary"])
    text_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    translation_text = tk.Text(text_container, 
                              font=("Segoe UI", 14), 
                              bg=COLORS["bg_primary"], 
                              fg=COLORS["text_primary"],
                              wrap='word', 
                              padx=20, 
                              pady=20,
                              insertbackground=COLORS["text_primary"],
                              selectbackground=COLORS["accent_primary"],
                              relief="flat",
                              bd=0)
    
    scrollbar = tk.Scrollbar(text_container, command=translation_text.yview, 
                            bg=COLORS["bg_tertiary"])
    translation_text.config(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side='right', fill='y')
    translation_text.pack(side='left', fill='both', expand=True)

    # Update word count function
    def update_word_count(*args):
        content = translation_text.get(1.0, tk.END).strip()
        word_count = len(content.split()) if content else 0
        word_count_label.config(text=f"Words: {word_count}")

    translation_text.bind('<KeyRelease>', update_word_count)
    translation_text.bind('<Button-1>', update_word_count)

    # Statistics and footer section
    footer_frame = tk.Frame(main_container, bg=COLORS["bg_secondary"], relief="flat", bd=2)
    footer_frame.pack(fill='x')

    # Statistics
    stats_frame = tk.Frame(footer_frame, bg=COLORS["bg_secondary"])
    stats_frame.pack(pady=15)

    stats_label = tk.Label(stats_frame, text="Session: 00:00:00 | Translations: 0 | Words: 0", 
                          font=("Segoe UI", 11), 
                          bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
    stats_label.pack()

    # Footer info
    footer_info = tk.Frame(footer_frame, bg=COLORS["bg_secondary"])
    footer_info.pack(pady=(0, 15))

    tk.Label(footer_info, text="🎮 OBS Ready", 
             font=("Segoe UI", 10, "bold"), 
             bg=COLORS["bg_secondary"], fg=COLORS["accent_secondary"]).pack(side='left', padx=10)

    tk.Label(footer_info, text="•", 
             font=("Segoe UI", 10), 
             bg=COLORS["bg_secondary"], fg=COLORS["text_muted"]).pack(side='left')

    tk.Label(footer_info, text="🤖 AI Powered", 
             font=("Segoe UI", 10, "bold"), 
             bg=COLORS["bg_secondary"], fg=COLORS["accent_primary"]).pack(side='left', padx=10)

    tk.Label(footer_info, text="•", 
             font=("Segoe UI", 10), 
             bg=COLORS["bg_secondary"], fg=COLORS["text_muted"]).pack(side='left')

    tk.Label(footer_info, text="⚡ Real-time Translation", 
             font=("Segoe UI", 10, "bold"), 
             bg=COLORS["bg_secondary"], fg=COLORS["accent_warning"]).pack(side='left', padx=10)

    # Version info
    version_label = tk.Label(footer_info, text="v2.0 Pro", 
                            font=("Segoe UI", 9), 
                            bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
    version_label.pack(side='right', padx=20)

    # Add hover effects to buttons
    def on_enter(widget, color):
        def handler(event):
            widget.config(bg=color)
        return handler

    def on_leave(widget, original_color):
        def handler(event):
            widget.config(bg=original_color)
        return handler

    # Apply hover effects
    buttons = [
        (start_btn, "#059669", COLORS["accent_secondary"]),
        (stop_btn, "#DC2626", COLORS["accent_danger"]),
        (instructions_btn, "#2563EB", COLORS["accent_primary"]),
        (settings_btn, "#475569", COLORS["bg_tertiary"]),
        (history_btn, "#475569", COLORS["bg_tertiary"]),
        (meeting_btn, "#059669", COLORS["accent_secondary"]),
        (restore_btn, "#475569", COLORS["bg_tertiary"]),
        (clear_btn, "#D97706", COLORS["accent_warning"]),
        (save_btn, "#2563EB", COLORS["accent_primary"])
    ]

    for btn, hover_color, original_color in buttons:
        btn.bind("<Enter>", on_enter(btn, hover_color))
        btn.bind("<Leave>", on_leave(btn, original_color))

    # Keyboard shortcuts
    def on_key_press(event):
        if event.state & 0x4:  # Ctrl key
            if event.keysym == 's':  # Ctrl+S
                save_translation()
            elif event.keysym == 'n':  # Ctrl+N
                clear_translation()
            elif event.keysym == 'i':  # Ctrl+I
                show_instructions()
            elif event.keysym == 'h':  # Ctrl+H
                show_history()
        elif event.keysym == 'F1':  # F1 for instructions
            show_instructions()
        elif event.keysym == 'F5':  # F5 to start
            if not is_running:
                start_translation()
        elif event.keysym == 'Escape':  # Escape to stop
            if is_running:
                stop_translation()

    root.bind('<Key>', on_key_press)
    root.focus_set()

    # Status bar with tips - Updated for OBS integration info
    tip_label = tk.Label(root, 
                        text="💡 OBS Live Integration Active | F1: Help | F5: Start | Esc: Stop | Ctrl+S: Save to OBS", 
                        font=("Segoe UI", 9), 
                        bg=COLORS["bg_tertiary"], 
                        fg=COLORS["text_muted"],
                        pady=5)
    tip_label.pack(side='bottom', fill='x')

    # Initial model status check and setup
    if not model_loaded:
        status_label.config(text="⚠️ Model Not Loaded", fg=COLORS["accent_warning"])
        error_msg = f"""⚠️ AI Model Loading Issue

The following files are required in your project structure:
• {model_path}
• {label_map_path}

Current folder structure should be:
📁 SIGNBRIDGEPROJECT/
├── 📁 model/
│   ├── sign_model.h5
│   └── label_map.npy
├── 📁 assets/
├── 📁 dist/
└── main.py

Please ensure these files exist and restart the application."""
        
        messagebox.showwarning("Model Files Missing", error_msg)
    else:
        print("✅ All systems ready!")

    return root

# === MAIN EXECUTION ===
if __name__ == "__main__":
    try:
        # Print startup information
        print("🚀 Starting SignBridge Pro...")
        print(f"📁 Base path: {base_path}")
        print(f"🧠 Model path: {model_path}")
        print(f"🏷️ Label map path: {label_map_path}")
        print(f"💾 Settings path: {settings_path}")
        print(f"📄 Caption output: {caption_output_path}")
        print(f"🎨 Assets path: {assets_path}")
        
        # Load settings
        settings = load_settings()
        print(f"⚙️ Settings loaded: {settings}")
        
        # Create and setup GUI
        root = create_gui()
        
        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Show welcome message only if model is loaded
        if model_loaded:
            welcome_msg = """🎉 Welcome to SignBridge Pro v2.0!

✨ Enhanced Features:
• Real-time AI sign language translation
• Professional OBS streaming integration  
• Smart confidence scoring system
• Translation history & export
• Customizable settings panel
• Keyboard shortcuts support

🚀 Ready to bridge communication gaps with AI!

🎮 Quick Start:
• Press F1 for detailed instructions
• Press F5 to start translation
• Press Escape to stop
• Ctrl+S to save current translation

Click 'Instructions' for complete guidance or 'Start Translation' to begin your session."""
        else:
            welcome_msg = """⚠️ SignBridge Pro - Setup Required

Please ensure your project has the required AI model files:

📁 Required Structure:
SIGNBRIDGEPROJECT/
├── 📁 model/
│   ├── sign_model.h5      ← AI model file
│   └── label_map.npy      ← Label mapping
├── 📁 assets/
├── 📁 dist/
└── main.py

Once you have these files, restart the application.
Contact support if you need the model files."""
        
        messagebox.showinfo("SignBridge Pro v2.0", welcome_msg)
        
        print("✅ GUI initialized successfully!")
        print("🎯 Application ready for use!")
        
        # Start the main application loop
        root.mainloop()
        
    except Exception as e:
        error_msg = f"❌ Application startup error: {e}"
        print(error_msg)
        if 'root' in locals() and root:
            messagebox.showerror("Application Error", f"A critical error occurred during startup:\n\n{str(e)}\n\nPlease check your project structure and model files.")
        input("Press Enter to exit...")
    finally:
        # Cleanup resources
        print("🧹 Cleaning up resources...")
        if 'cap' in globals() and cap:
            cap.release()
            print("📹 Camera released")
        cv2.destroyAllWindows()
        print("🪟 OpenCV windows closed")
        print("👋 SignBridge Pro shutdown complete")