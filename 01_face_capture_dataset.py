import cv2
import os
from picamera2 import Picamera2

# Constants
COUNT_LIMIT = 500
POS=(30,60)  #top-left
FONT=cv2.FONT_HERSHEY_COMPLEX #font type for text overlay
HEIGHT=1.5  #font_scale
TEXTCOLOR=(0,0,255)  #BGR- RED
BOXCOLOR=(255,0,255) #BGR- BLUE
WEIGHT=3  #font-thickness
FACE_DETECTOR=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# For each person, enter one numeric face id
face_id = input('\n----Enter User-id and press <return>----')
print("\n [INFO] Initializing face capture. Look at the camera and wait!")

# Create an instance of the PiCamera2 object
cam = Picamera2()
## Set the resolution of the camera preview
cam.preview_configuration.main.size = (640, 360)
cam.preview_configuration.main.format = "RGB888"
cam.preview_configuration.controls.FrameRate=30
cam.preview_configuration.align()
cam.configure("preview")
cam.start()

count=0

while True:
    # Capture a frame from the camera
    frame=cam.capture_array()
    # Display count of images taken
    cv2.putText(frame,'Count:'+str(int(count)),POS,FONT,HEIGHT,TEXTCOLOR,WEIGHT)

    # Convert frame from BGR to grayscale
    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Create a DS faces- array with 4 elements- x,y coordinates (top-left corner), width and height
    faces = FACE_DETECTOR.detectMultiScale( # detectMultiScale has 4 parameters
            frameGray,      # The grayscale frame to detect
            scaleFactor=1.1,# how much the image size is reduced at each image scale-10% reduction
            minNeighbors=5, # how many neighbors each candidate rectangle should have to retain it
            minSize=(30, 30)# Minimum possible object size. Objects smaller than this size are ignored.
    )
    for (x,y,w,h) in faces:
        # Create a bounding box across the detected face
        cv2.rectangle(frame, (x,y), (x+w,y+h), BOXCOLOR, 3) # 5 parameters - frame, topleftcoords,bottomrightcooords,boxcolor,thickness
        count += 1 # increment count

        # if dataset folder doesnt exist create:
        if not os.path.exists("dataset"):
            os.makedirs("dataset")

        # Save the captured bounded-grayscale image into the datasets folder
        file_path = os.path.join("dataset", f"User.{face_id}.{count}.jpg")

        # Check if the user ID already exists in the dataset
        existing_files = [f for f in os.listdir("dataset") if f.startswith(f"User.{face_id}.")]
        
        if existing_files:
            # If the user ID exists, get the count from the last image
            last_count = max(int(file.split(".")[2]) for file in existing_files)
            count = last_count + 1

            # Update the file path for the new image
            file_path = os.path.join("dataset", f"User.{face_id}.{count}.jpg")

        # Write the newer images
        cv2.imwrite(file_path, frameGray[y:y+h, x:x+w])


    # Display the original frame to the user
    cv2.imshow('FaceCapture', frame)
    # Wait for 30 milliseconds for a key event (extract sigfigs) and exit if 'ESC' or 'q' is pressed
    key = cv2.waitKey(100) & 0xff
    # Checking keycode
    if key == 27:  # ESCAPE key
        break
    elif key == 113:  # q key
        break
    elif count >= COUNT_LIMIT: # Take COUNT_LIMIT face samples and stop video capture
        break

# Release the camera and close all windows
print("\n [INFO] Exiting Program and cleaning up stuff")
cam.stop()
cv2.destroyAllWindows()
