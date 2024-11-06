import cv2
import mediapipe as mp
import os
from flask import Response, jsonify

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Initialize a global variable to store the current video capture object
cap = None

# Function to load shirt images
def load_shirt_images():
    shirt_folder_path = "static/uploads"
    shirt_images = []
    for img in os.listdir(shirt_folder_path):
        if img.endswith('.png'):
            image_path = os.path.join(shirt_folder_path, img)
            shirt_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if shirt_image is not None and shirt_image.shape[2] == 4:  # Ensure image has an alpha channel
                shirt_images.append(shirt_image)
    return shirt_images

# Function to overlay image with transparency
def overlay_image(background, overlay, position):
    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, _ = overlay.shape

    # Define region of interest
    y1, y2 = position[1], position[1] + ol_h
    x1, x2 = position[0], position[0] + ol_w

    # Ensure the overlay is within the bounds of the background
    if y1 < 0 or y2 > bg_h or x1 < 0 or x2 > bg_w or ol_h == 0 or ol_w == 0:
        return background  # Skip if the overlay goes out of bounds

    alpha_overlay = overlay[:, :, 3] / 255.0
    alpha_background = 1.0 - alpha_overlay

    # Apply overlay image with alpha blending
    for c in range(3):  # Apply for each color channel (BGR)
        background[y1:y2, x1:x2, c] = (
            alpha_overlay * overlay[:, :, c] + 
            alpha_background * background[y1:y2, x1:x2, c]
        )

    return background

def stream_video_feed(shirt_index):
    global cap  # Declare 'cap' as global

    def generate_video_feed():
        global cap  # Access the global 'cap'

        # If the camera was previously opened, close it before reopening
        if cap is not None and cap.isOpened():
            print("Releasing the camera...")
            cap.release()

        # Open the camera again
        print("Opening the camera...")
        cap = cv2.VideoCapture(0)

        # Check if the camera is opened
        if not cap.isOpened():
            print("Error: Could not open video source.")
            raise RuntimeError("Could not open video source.")
        
        print("Camera opened successfully.")

        # Ensure shirt images are available
        shirt_images = load_shirt_images()
        if not shirt_images:
            print("Error: No shirt images loaded!")
            raise RuntimeError("No shirt images loaded!")

        while True:
            ret, frame = cap.read()

            # If reading the frame fails, handle the error
            if not ret:
                print("Error: Failed to read frame from the camera.")
                break

            try:
                # Convert the BGR image to RGB for MediaPipe processing
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                # Draw pose landmarks and overlay shirt if landmarks are detected
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    height, width, _ = frame.shape
                    x11, y11 = int(landmarks[11].x * width), int(landmarks[11].y * height)
                    x12, y12 = int(landmarks[12].x * width), int(landmarks[12].y * height)

                    shoulder_x = int((x11 + x12) / 2)
                    shoulder_y = int((y11 + y12) / 2)
                    shoulder_width = abs(x11 - x12)

                    shirt_width = int(shoulder_width * 1.5)
                    shirt_height = int(shirt_width * (581 / 440))

                    if shirt_width > 0:
                        shirt_image = shirt_images[shirt_index]
                        shirt_image = cv2.resize(shirt_image, (shirt_width, shirt_height))
                        shirt_x = shoulder_x - int(shirt_width / 2)
                        shirt_y = shoulder_y - int(shirt_height * 0.3)

                        # Overlay the shirt image
                        frame = overlay_image(frame, shirt_image, (shirt_x, shirt_y))
            except Exception as e:
                print(f"Error during frame processing: {e}")
                break

            try:
                # Convert frame to JPEG for streaming
                _, jpeg = cv2.imencode('.jpg', frame)
                if not _:
                    print("Error: Failed to encode frame.")
                    break

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

            except Exception as e:
                print(f"Error during JPEG encoding: {e}")
                break


    return generate_video_feed()
