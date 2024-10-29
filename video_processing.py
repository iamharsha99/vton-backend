import cv2
import mediapipe as mp
import os
from flask import Response

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

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


# Video streaming function with shirt overlay
def stream_video_feed(shirt_index):
    def generate_video_feed():
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise RuntimeError("Could not open video source.")

        shirt_images = load_shirt_images()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert the BGR image to RGB for MediaPipe processing
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            # Draw pose landmarks and overlay shirt if landmarks are detected
            if results.pose_landmarks:
                #mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Get pose landmarks
                landmarks = results.pose_landmarks.landmark
                height, width, _ = frame.shape
                x11, y11 = int(landmarks[11].x * width), int(landmarks[11].y * height)
                x12, y12 = int(landmarks[12].x * width), int(landmarks[12].y * height)

                # Calculate shirt position and dimensions
                shoulder_x = int((x11 + x12) / 2)  # Midpoint for x-position
                shoulder_y = int((y11 + y12) / 2)  # Midpoint for y-position
                shoulder_width = abs(x11 - x12)  # Distance between shoulders

                shirt_width = int(shoulder_width * 1.5)  # Adjust factor for suitable width
                shirt_height = int(shirt_width * (581 / 440))  # Maintain aspect ratio

                if shirt_width > 0 and shirt_images:
                    shirt_image = shirt_images[shirt_index]

                    if shirt_image is not None and shirt_image.shape[2] == 4:  # Ensure image has an alpha channel
                        # Resize and calculate position
                        shirt_image = cv2.resize(shirt_image, (shirt_width, shirt_height))
                        shirt_x = shoulder_x - int(shirt_width / 2)
                        shirt_y = shoulder_y - int(shirt_height * 0.3)  # Move up slightly for better fit

                        # Overlay the shirt image
                        frame = overlay_image(frame, shirt_image, (shirt_x, shirt_y))

            # Convert frame to JPEG for streaming
            _, jpeg = cv2.imencode('.jpg', frame)
            if not _:
                raise RuntimeError("Failed to encode frame.")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        cap.release()

    return Response(generate_video_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
