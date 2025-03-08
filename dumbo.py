import cv2
import time
import logging
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from PIL import Image

# Initialize modules
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # Default speech rate

# Gemini API key (replace with your own)
genai.configure(api_key="AIzaSyD7Srj-VTI5tuY2od1xHl7XAKg-Khhc9rg")

# Image processing variables
image_description_cache = {}
is_describing = False

def speak(text):
    """Speak the given text and handle pyttsx3's run loop issue."""
    try:
        if engine._inLoop:  
            engine.endLoop()  # Stop existing loop if running
        engine.say(text)
        engine.runAndWait()
    except RuntimeError:
        logging.error("Error in speak(): run loop already started.")
    except KeyboardInterrupt:
        print("\nSpeech interrupted by user.")
        engine.stop()
        raise  # Re-raise KeyboardInterrupt for graceful exit

def listen():
    """Listen to user input via microphone after speech is completed."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("User said:", text)
        return text.lower()
    except sr.UnknownValueError:
        print("Speech Recognition could not understand the audio.")
        return ""
    except sr.RequestError:
        print("There was an issue with the voice service.")
        return ""

def is_scene_changed(prev_frame, current_frame, threshold=30):
    """Detect scene changes based on pixel difference percentage."""
    diff = cv2.absdiff(prev_frame, current_frame)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    non_zero_count = cv2.countNonZero(gray_diff)
    total_pixels = gray_diff.size
    change_percentage = (non_zero_count / total_pixels) * 100
    return change_percentage > threshold

def capture_image(frame, filename="captured_image.png"):
    """Save the captured image to a file and describe it."""
    cv2.imwrite(filename, frame)
    print("Image Captured:", filename)
    describe_image(filename)

def describe_image(image_path):
    """Generate a description of the image and handle voice interactions."""
    global is_describing, image_description_cache
    is_describing = True  # Block new captures

    try:
        if image_path in image_description_cache:
            scene_description = image_description_cache[image_path]
        else:
            image = Image.open(image_path)
            prompt = "Describe the scene naturally, considering spatial awareness."
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, image])
            scene_description = response.text
            image_description_cache[image_path] = scene_description

        print("\nImage Description:\n", scene_description)
        speak(scene_description)  # Speak before allowing follow-up questions

        # Allow follow-up questions
        while True:
            speak("Do you have any questions about the image? Say 'I have a question' or remain silent to continue.")
            user_response = listen()
            if "question" not in user_response:
                break  # Exit loop if no question

            speak("Please ask your question.")
            user_question = listen()
            if not user_question:
                continue

            answer = answer_question_from_image(image_path, user_question)
            print("\nANSWER:", answer)
            speak(answer)

    except Exception as e:
        logging.error(f"Error in describe_image: {e}")
        speak("Sorry, something went wrong. Please try again.")

    is_describing = False  # Allow new captures

def answer_question_from_image(image_path, question):
    """Answer user questions based on the image."""
    try:
        image = Image.open(image_path)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([question, image])
        return response.text
    except Exception as e:
        logging.error(f"Error in answer_question_from_image: {e}")
        return "I couldn't process your question."

def handle_general_question(user_input):
    """Handles general non-image-related user queries."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_input)
        return response.text
    except Exception as e:
        logging.error(f"Error in handle_general_question: {e}")
        return "I couldn't process your request."

def start_camera():
    """Continuously capture images only when the scene changes and description is done."""
    global is_describing

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    ret, prev_frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        return

    try:
        while True:
            ret, current_frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            prev_frame = cv2.resize(prev_frame, (1280, 720))
            current_frame = cv2.resize(current_frame, (1280, 720))

            if not is_describing and is_scene_changed(prev_frame, current_frame):
                capture_image(current_frame)
                prev_frame = current_frame

            # Listen for commands only after description is done
            if not is_describing:
                user_input = listen()
                if user_input:
                    if "shutdown" in user_input:
                        speak("Shutting down. Goodbye!")
                        break
                    elif "image" in user_input or "scene" in user_input:
                        speak("Please wait while I analyze the image.")
                        answer = answer_question_from_image("captured_image.png", user_input)
                        print("\nANSWER:", answer)
                        speak(answer)
                    else:
                        answer = handle_general_question(user_input)
                        print("\nANSWER:", answer)
                        speak(answer)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nKeyboard Interrupt detected. Exiting gracefully...")
        speak("Goodbye!")  # Allow it to finish speaking
        engine.stop()  # Stop pyttsx3 safely

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam released. Windows closed.")

if __name__ == "__main__":
    print("Starting 'The Blind Guy' AI assistant...")
    start_camera()
