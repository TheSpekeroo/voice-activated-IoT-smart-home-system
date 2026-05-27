from pocketsphinx import LiveSpeech

def live_speech_recognition():
    # Create a pocketsphinx LiveSpeech object
    speech = LiveSpeech()

    print("Starting speech recognition. Please speak...")

    # Infinite loop to continuously detect speech input
    for phrase in speech:
        try:
            # Print the recognized text using pocketsphinx
            recognized_text = str(phrase)
            print("Recognized speech: {}".format(recognized_text))
            if recognized_text=="turn on":
                print("Logic is on")
            elif recognized_text=="turn off":
                print("Logic is off")
            elif recognized_text=="find":
                print("Finding Users")
            else:
                print("Unrecognized Commands")
        except KeyboardInterrupt:
            # Exit the loop if the user presses Ctrl+C
            break

if __name__ == "__main__":
    live_speech_recognition()

