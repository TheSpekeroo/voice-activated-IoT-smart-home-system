# 🤖 Smart IoT Kiosk — Voice & Face Recognition on Raspberry Pi 4

A voice-activated, face-recognizing IoT system built on **Raspberry Pi 4**. Users speak a wake word to activate the camera, are identified via **LBPH face recognition**, and then issue **voice commands** to control GPIO-connected hardware (e.g., LEDs), manage the user database, and query the environment — all hands-free.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Voice Commands](#voice-commands)
- [User Management Workflow](#user-management-workflow)
- [Project Structure](#project-structure)
- [Bonus Modules](#bonus-modules)

---

## Overview

This system operates as a smart interactive kiosk. On startup, it listens for the wake word **"start"** via a microphone. Once heard, it activates the Pi Camera, identifies the person in front of it using a trained **LBPH (Local Binary Patterns Histograms)** face model, and unlocks a set of voice-controlled commands personalized to the recognized user. Unrecognized faces are labeled as unknown and denied command access.

The system also includes standalone utility modules for face mask detection (with MQTT alerting and GPIO buzzer/LED feedback), face counting, and GPIO control.

---

## Features

- 🎙️ **Wake-word activation** — system stays idle until "start" is spoken
- 👤 **LBPH face recognition** — fast, lightweight, runs entirely on-device
- 🗣️ **Voice command interface** — controls GPIO and database via speech after identity is confirmed
- 💡 **GPIO hardware control** — turn a connected device (e.g., LED, relay) on/off by voice
- 👥 **Live face counter** — counts the maximum number of faces in a 10-second window
- 🔍 **Multi-user finder** — scans for and logs all recognized users in a 10-second window
- ➕ **Add / 🗑️ Delete users** by voice command, without restarting the system
- 🔁 **Re-train on the fly** — retrain the LBPH model from voice without stopping the program
- 😷 **Face mask detector** — bonus module with MQTT publishing and buzzer/LED alerts
- 📸 **Dataset capture** — guided face capture tool collects up to 500 images per user

---

## System Architecture

```
Microphone
    │
    ▼
PocketSphinx (offline STT)
    │  Wake word: "start"
    ▼
Pi Camera (Picamera2)          ← 640×360 @ 30 FPS
    │
    ▼
Haar Cascade Face Detector     ← haarcascade_frontalface_default.xml
    │
    ▼
LBPH Face Recognizer           ← trainer/trainer.yml
    │
    ├── Known user → speech_recognition_commands(name)
    │       │
    │       ├── "turn on"  → GPIO pin HIGH
    │       ├── "turn off" → GPIO pin LOW
    │       ├── "find"     → scan & log recognized users (10s)
    │       ├── "count faces" → count max faces (10s)
    │       ├── "add user" → capture dataset → retrain
    │       ├── "train"    → retrain LBPH model
    │       ├── "delete user" → remove dataset images
    │       └── "stop"     → return to wake-word listening
    │
    └── Unknown user → display "unknown", stay in recognition loop
```

---

## Hardware Requirements

- Raspberry Pi 4 (2GB RAM or higher recommended)
- Raspberry Pi Camera Module (or USB webcam compatible with Picamera2)
- USB Microphone (for PocketSphinx speech recognition)
- LED or relay connected to **GPIO pin 18** (BCM)
- *(Optional for mask detection module)* Buzzer on GPIO 21, Red LED on GPIO 14, Green LED on GPIO 15

---

## Software Requirements

- Raspberry Pi OS (Bullseye or later)
- Python 3.9+
- PocketSphinx (offline speech recognition)
- Picamera2 library

### Python Dependencies

Install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

```
numpy==1.24.3
opencv-python==4.7.0.72
opencv-contrib-python==4.7.0.72
picamera2==0.3.9
Pillow==9.5.0
```

Additional dependencies not in `requirements.txt`:

```bash
pip install pocketsphinx RPi.GPIO
# For the mask detection bonus module only:
pip install tensorflow imutils paho-mqtt
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/smart-iot-kiosk.git
   cd smart-iot-kiosk
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pocketsphinx RPi.GPIO
   ```

3. **Connect hardware:**
   - Attach the Pi Camera and USB microphone.
   - Wire an LED (or relay) to **GPIO 18** (BCM) with an appropriate resistor.

4. **Capture a face dataset** for at least one user (see [User Management Workflow](#user-management-workflow)).

5. **Train the face model:**
   ```bash
   python 02_face_training.py
   ```
   This generates `trainer/trainer.yml`.

6. **Update the `names` list** in `_Main_Smart.py` to match your enrolled user IDs:
   ```python
   names = ['New User', 'Ralph', 'Tom', 'Yeonghun']
   #         index 0     id 1    id 2    id 3
   ```

---

## Usage

### Launch the system

```bash
python _Main_Smart.py
```

The system will start listening for the wake word. Say **"start"** to activate the camera and begin face recognition. Once your face is identified, you can issue voice commands.

Press **`ESC`** or **`q`** at any time to exit the camera window.

---

## Voice Commands

These commands are available after a known user has been recognized:

| Command | Action |
|---|---|
| `"turn on"` | Sets GPIO pin 18 HIGH (turns on connected device) |
| `"turn off"` | Sets GPIO pin 18 LOW (turns off connected device) |
| `"find"` | Scans for recognized users for 10 seconds and prints results |
| `"count faces"` | Counts the maximum number of faces visible over 10 seconds |
| `"add user"` | Prompts for a user ID and captures up to 500 face images |
| `"train"` | Retrains the LBPH model from the current dataset |
| `"delete user"` | Prompts for a user ID and removes all their dataset images |
| `"stop"` | Closes the camera and returns to wake-word listening mode |

---

## User Management Workflow

### Adding a new user (standalone)

```bash
python 01_face_capture_dataset.py
```

Enter a numeric user ID when prompted. The script captures up to 500 grayscale face images into the `dataset/` folder as `User.<id>.<count>.jpg`. It automatically resumes count from the last image if the ID already exists.

### Training the model (standalone)

```bash
python 02_face_training.py
```

Reads all `.jpg` files from `dataset/`, extracts face regions, and trains the LBPH recognizer. Saves the model to `trainer/trainer.yml`. Prints the number of unique users trained.

### Live recognition only (standalone)

```bash
python 03_face_recogition.py
```

Runs face recognition in a standalone loop without voice command integration.

### Adding / deleting users at runtime

While the main system is running, say `"add user"` or `"delete user"` — no restart required. After adding a user, say `"train"` to update the model immediately.

---

## Project Structure

```
smart-iot-kiosk/
│
├── _Main_Smart.py                  # Main entry point — wake word → face ID → voice commands
│
├── 01_face_capture_dataset.py      # Standalone: capture face images for a new user
├── 02_face_training.py             # Standalone: train LBPH model from dataset
├── 03_face_recogition.py           # Standalone: face recognition loop (no voice)
│
├── commands.py                     # Standalone: voice command demo (PocketSphinx)
├── face_recognition.py             # Standalone: 10-second multi-user recognizer
├── face_counter.py                 # Standalone: 10-second face counter
├── gpio.py                         # Standalone: basic GPIO on/off demo
│
├── detect_mask_picam_mqtt.py       # Bonus: face mask detector with MQTT + GPIO alerts
│
├── haarcascade_frontalface_default.xml  # Haar cascade classifier for face detection
├── requirements.txt                # Python dependencies
│
├── dataset/                        # Auto-created: captured face images (User.<id>.<n>.jpg)
└── trainer/
    └── trainer.yml                 # Auto-created: trained LBPH model
```

---

## Bonus Modules

### Face Mask Detector (`detect_mask_picam_mqtt.py`)

A standalone mask detection module using a MobileNetV2-based classifier. When a face without a mask is detected:

- Publishes an MQTT message to topic `mask_detector` on `localhost:1883`
- Activates a **buzzer** (GPIO 21) and **red LED** (GPIO 14)
- Displays `"No Face Mask Detected"` on-screen in red

When a mask is worn:
- Turns on the **green LED** (GPIO 15)
- Displays `"Thank You. Mask On."` in green

**Additional requirements for this module:**
```bash
pip install tensorflow imutils paho-mqtt
```

Requires a pre-trained mask detector model (`mask_detector.model`) and a Caffe face detector (`face_detector/deploy.prototxt` + `res10_300x300_ssd_iter_140000.caffemodel`).
