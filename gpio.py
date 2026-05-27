import RPi.GPIO as GPIO
import time

# Set the GPIO mode (BCM or BOARD)
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin you want to use
pin_number = 18  # Change this to the desired pin number

# Set up the GPIO pin as an output
GPIO.setup(pin_number, GPIO.OUT)
GPIO.setwarnings(False)

# Turn on the GPIO pin
GPIO.output(pin_number, GPIO.LOW)
print(f"GPIO pin {pin_number} turned off                                                                 .")

# Wait for 5 seconds (you can adjust the duration as needed)