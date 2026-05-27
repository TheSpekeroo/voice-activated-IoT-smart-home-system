import cv2
import os
from picamera2 import Picamera2
import time

# Constants
POS = (30, 60)  # top-left
FONT = cv2.FONT_HERSHEY_COMPLEX  # font type for text overlay
HEIGHT = 1.5  # font_scale
TEXTCOLOR = (0, 0, 255)  # BGR- RED
BOXCOLOR = (255, 0, 255)  # BGR- BLUE
WEIGHT = 3  # font-thickness
FACE_DETECTOR = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Create an instance of the PiCamera2 object
cam = Picamera2()
## Set the resolution of the camera preview
cam.preview_configuration.main.size = (640, 360)
cam.preview_configuration.main.format = "RGB888"
cam.preview_configuration.controls.FrameRate = 30
cam.preview_configuration.align()
cam.configure("preview")
cam.start()

start_time = time.time()
max_faces = 0

while True:
    # Capture a frame from the camera
    frame = cam.capture_array()

    # Convert frame from BGR to grayscale
    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Create a DS faces- array with 4 elements- x,y coordinates (top-left corner), width and height
    faces = FACE_DETECTOR.detectMultiScale(
        frameGray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    num_faces = len(faces)
    cv2.putText(frame, f"Faces: {num_faces}", (10, 60), FONT, HEIGHT, TEXTCOLOR, WEIGHT)

    for (x, y, w, h) in faces:
        # Create a bounding box across the detected face
        cv2.rectangle(frame, (x, y), (x+w, y+h), BOXCOLOR, 3)

    # Display the original frame to the user
    cv2.imshow('FaceCapture', frame)

    # Check elapsed time
    elapsed_time = time.time() - start_time

    # After 5 seconds, print the maximum number of faces and reset the timer
    if elapsed_time >= 5:
        print(f"Maximum number of faces detected in 5 seconds: {max_faces}")
        start_time = time.time()  # Reset the timer
        max_faces = 0

    # Update the maximum faces count
    max_faces = max(max_faces, num_faces)

    # Wait for 30 milliseconds for a key event and exit if 'ESC' or 'q' is pressed
    key = cv2.waitKey(100) & 0xff

    # Checking keycode
    if key == 27:  # ESCAPE key
        break
    elif key == 113:  # q key
        break

# Release the camera and close all windows
print("\n [INFO] Exiting Program and cleaning up stuff")
cam.stop()
cv2.destroyAllWindows()
