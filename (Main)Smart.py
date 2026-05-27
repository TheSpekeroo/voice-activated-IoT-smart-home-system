import cv2
import os
import numpy as np
import RPi.GPIO as GPIO
import time
import subprocess
from picamera2 import Picamera2
from pocketsphinx import LiveSpeech

# Parameters
id = 0
font = cv2.FONT_HERSHEY_COMPLEX
height = 1
boxColor = (0, 0, 255)      # BGR- GREEN
boxColor2 = (255, 0, 255)  # BGR- BLUE
nameColor = (255, 255, 255)  # BGR- WHITE
confColor = (255, 255, 0)    # BGR- TEAL
textColor = (0, 0, 255)  # BGR- RED
weight = 1 # font-thickness

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
# names related to id
names = ['New User', 'Ralph', 'Tom', 'Yeonghun']

# Create an instance of the PiCamera2 object
cam = Picamera2()
## Initialize and start realtime video capture
# Set the resolution of the camera preview
cam.preview_configuration.main.size = (640, 360)
cam.preview_configuration.main.format = "RGB888"
cam.preview_configuration.controls.FrameRate = 30
cam.preview_configuration.align()
cam.configure("preview")
cam.start()


#GPIO Setup
GPIO.setmode(GPIO.BCM)
pin_number = 18
GPIO.setup(pin_number, GPIO.OUT)
GPIO.setwarnings(False)


def live_speech_recognition():
    # Create a pocketsphinx LiveSpeech object
    speech = LiveSpeech()

    print("Please say 'start' to activate facial recognition.")

    # Listen for the keyword "start"
    for phrase in speech:
        if str(phrase) == "start":
            print("Starting facial recognition. Please wait...")
            face_recognition_loop()
            break
        else:
            print("Keyword not detected. Please say 'start' to activate facial recognition.")

def speech_recognition_commands(recognized_name):
    print("State your commands. Please speak...")

    # Infinite loop to continuously detect speech input
    for phrase in LiveSpeech():
        try:
            recognized_text = str(phrase)
            print("Recognized speech:", recognized_text)

            if recognized_text == "turn on":
                print("Turning on for recognized user:", recognized_name)
                GPIO.output(pin_number, GPIO.HIGH) #Turn On LED
            elif recognized_text == "turn off":
                print("Turning off for recognized user:", recognized_name)
                GPIO.output(pin_number, GPIO.LOW) #Turn Off LED
            elif recognized_text == "find":
                print("Finding Users for recognized user:", recognized_name)
                face_recognition()
                print("[INFO] Exiting Program and cleaning up stuff")
                cam.stop()
                cv2.destroyAllWindows()
            elif recognized_text == "add user":
                print("Adding New User")
                add_user()
                # Release the camera and close all windows
                print("\n [INFO] Exiting Program and cleaning up stuff")
                cam.stop()
                cv2.destroyAllWindows()
            elif recognized_text == "train":
                print("Training Face Recognition")
                train()
                
            elif recognized_text == "delete user":
                try:
                    user_id_to_delete = int(input("Enter the user ID to delete: "))
                    delete_user(user_id_to_delete)
                    print(f"Deleted images for user ID: {user_id_to_delete}")
                except ValueError:
                    print("Invalid user ID. Please enter a valid numeric ID.")
                
            elif recognized_text == "count faces":
                print("Counting Faces for recognized user:", recognized_name)
                face_counter()
                print("\n [INFO] Exiting Program and cleaning up stuff")
                cam.stop()
                cv2.destroyAllWindows()
                
            elif recognized_text == "stop":
                print("Resetting Interaction for recognized user:", recognized_name)
                # Release the camera and close all windows
                print("\n [INFO] Exiting Program and cleaning up stuff")
                cam.stop()
                cv2.destroyAllWindows()
                live_speech_recognition()
            else:
                print("Unrecognized Commands")

        except KeyboardInterrupt:
            break


def face_recognition_loop():
    cam.start()
    while True:
        # Capture a frame from the camera
        frame = cam.capture_array()

        # Convert frame from BGR to grayscale
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Create a DS faces- array with 4 elements- x, y coordinates top-left corner), width and height
        faces = face_detector.detectMultiScale(
            frameGray,      # The grayscale frame to detect
            scaleFactor=1.1,  # how much the image size is reduced at each image scale-10% reduction
            minNeighbors=5,  # how many neighbors each candidate rectangle should have to retain it
            minSize=(150, 150)  # Minimum possible object size. Objects smaller than this size are ignored.
        )

        for (x, y, w, h) in faces:
            namepos = (x + 5, y - 5)  # shift right and up/outside the bounding box from top
            confpos = (x + 5, y + h - 5)  # shift right and up/intside the bounding box from bottom
            # create a bounding box across the detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)  # 5 parameters - frame, topleftcoords,bottomrightcooords,boxcolor,thickness

            # recognizer.predict() method takes the ROI as input and
            # returns the predicted label (id) and confidence score for the given face region.
            id, confidence = recognizer.predict(frameGray[y:y + h, x:x + w])

            # If confidence is less than 100, it is considered a perfect match
            if confidence < 100:
                id = names[id]
                confidence = f"{100 - confidence:.0f}%"
                if id != "unknown":
                    cam.stop()
                    cv2.destroyAllWindows()
                    speech_recognition_commands(id)
            else:
                id = "unknown"
                confidence = f"{100 - confidence:.0f}%"

            # Display name and confidence of the person whose face is recognized
            cv2.putText(frame, str(id), namepos, font, height, nameColor, 2)
            cv2.putText(frame, str(confidence), confpos, font, height, confColor, 1)

        # Display realtime capture output to the user
        cv2.imshow('Raspi Face Recognizer', frame)

        # Wait for 30 milliseconds for a key event (extract sigfigs) and exit if 'ESC' or 'q' is pressed
        key = cv2.waitKey(100) & 0xff
        # Checking keycode
        if key == 27:  # ESCAPE key
            break
        elif key == 113:  # q key
            break

def face_recognition():
    cam.start()
    #Count Users
    start_time = time.time()  # Record the start time
    recognized_users = set()
    while True:
        # Capture a frame from the camera
        frame = cam.capture_array()

        # Convert frame from BGR to grayscale
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Create a DS faces- array with 4 elements- x,y coordinates top-left corner), width and height
        faces = face_detector.detectMultiScale(
            frameGray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(150, 150)
        )
        for (x, y, w, h) in faces:
            # Recognize the face
            id, confidence = recognizer.predict(frameGray[y:y + h, x:x + w])

            # If confidence is less than 100, it is considered a perfect match
            if confidence < 100:
                user_name = names[id]
                recognized_users.add(user_name)

            # Draw bounding box and display information
            namepos = (x + 5, y - 5)
            confpos = (x + 5, y + h - 5)
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3)
            cv2.putText(frame, str(user_name), namepos, font, height, nameColor, 2)
            cv2.putText(frame, str(confidence), confpos, font, height, confColor, 1)

        # Display real-time capture output to the user
        cv2.imshow('Raspi Face Recognizer', frame)

        # Check if 10 seconds have passed
        elapsed_time = time.time() - start_time
        if elapsed_time >= 10:
            print("\n [INFO] Recognized Users:")
            for user in recognized_users:
                print(user)
            recognized_users = set()
            break

        # Wait for 30 milliseconds for a key event (extract sigfigs) and exit if 'ESC' or 'q' is pressed
        key = cv2.waitKey(100) & 0xff
        # Checking keycode
        if key == 27:  # ESCAPE key
            break
        elif key == 113:  # q key
            break

def add_user():
    # Constants
    COUNT_LIMIT = 500
    POS=(30,60)  #top-left
    FONT=cv2.FONT_HERSHEY_COMPLEX #font type for text overlay
    HEIGHT=1.5  #font_scale
    TEXTCOLOR=(0,0,255)  #BGR- RED
    BOXCOLOR=(255,0,255) #BGR- BLUE
    WEIGHT=3  #font-thickness

    # For each person, enter one numeric face id
    face_id = input('\n----Enter User-id and press <return>----')
    print("\n [INFO] Initializing face capture. Look at the camera and wait!")
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
        faces = face_detector.detectMultiScale( # detectMultiScale has 4 parameters
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

def train():
    # Using LBPH(Local Binary Patterns Histograms) recognizer
    recognizer=cv2.face.LBPHFaceRecognizer_create()
    face_detector=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    path='dataset'

    # function to read the images in the dataset, convert them to grayscale values, return samples
    def getImagesAndLabels(path):
        faceSamples=[]
        ids = []

        for file_name in os.listdir(path):
            if file_name.endswith(".jpg"):
                id = int(file_name.split(".")[1])
                img_path = os.path.join(path, file_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

                faces = face_detector.detectMultiScale(img)

                for (x, y, w, h) in faces:
                    faceSamples.append(img[y:y+h, x:x+w])
                    ids.append(id)

        return faceSamples, ids


    def trainRecognizer(faces, ids):
        recognizer.train(faces, np.array(ids))
        # Create the 'trainer' folder if it doesn't exist
        if not os.path.exists("trainer"):
            os.makedirs("trainer")
        # Save the model into 'trainer/trainer.yml'
        recognizer.write('trainer/trainer.yml')


    print("\n [INFO] Training faces. It will take a few seconds. Wait ...")
    # Get face samples and their corresponding labels
    faces, ids = getImagesAndLabels(path)

    #Train the LBPH recognizer using the face samples and their corresponding labels
    trainRecognizer(faces, ids)


    # Print the number of unique faces trained
    num_faces_trained = len(set(ids))
    print("\n [INFO] {} faces trained. Exiting Program".format(num_faces_trained))

def face_counter():
    start_time = time.time()
    max_faces = 0
    cam.start()
    while True:
        # Capture a frame from the camera
        frame = cam.capture_array()

        # Convert frame from BGR to grayscale
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Create a DS faces- array with 4 elements- x,y coordinates (top-left corner), width and height
        faces = face_detector.detectMultiScale(
            frameGray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        num_faces = len(faces)
        cv2.putText(frame, f"Faces: {num_faces}", (10, 60), font, height, textColor, weight)

        for (x, y, w, h) in faces:
            # Create a bounding box across the detected face
            cv2.rectangle(frame, (x, y), (x+w, y+h), boxColor2, 3)

        # Display the original frame to the user
        cv2.imshow('FaceCapture', frame)

        # Check elapsed time
        elapsed_time = time.time() - start_time

        # After 5 seconds, print the maximum number of faces and reset the timer
        if elapsed_time >= 10:
            print(f"Maximum number of faces detected in 10 seconds: {max_faces}")
            break

        # Update the maximum faces count
        max_faces = max(max_faces, num_faces)

        # Wait for 30 milliseconds for a key event and exit if 'ESC' or 'q' is pressed
        key = cv2.waitKey(100) & 0xff

        # Checking keycode
        if key == 27:  # ESCAPE key
            break
        elif key == 113:  # q key
            break    

def delete_user(user_id):
    user_id_str = str(user_id)
    user_files = [f for f in os.listdir("dataset") if f.startswith(f"User.{user_id_str}.")]
    
    if not user_files:
        print(f"No images found for user ID: {user_id}")
        return
    print(f"Deleting images for user ID: {user_id}")
    for file_name in user_files:
        file_path= os.path.join("dataset",file_name)
        os.remove(file_path)
        print(f"Deleted: {file_path}")

if __name__ == "__main__":
    live_speech_recognition()
