from flask import Blueprint, request, jsonify, Response
import os
from video_processing import load_shirt_images, stream_video_feed
import threading

bp = Blueprint('routes', __name__)

# Global variable to hold the shirt images and shirt index
shirt_images = []
shirt_index = 0

# Initial load of shirt images
shirt_images = load_shirt_images()

# API to get the list of shirts
@bp.route('/api/shirts', methods=['GET'])
def shirts():
    """Handles fetching the list of shirt images."""
    # Fetch shirt files from the static directory
    shirt_files = [os.path.basename(img) for img in os.listdir('static/uploads') if img.endswith('.png')]
    
    return jsonify({"shirts": shirt_files})

# API to upload a new shirt
@bp.route('/api/upload_shirt', methods=['POST'])
def upload_shirt():
    """Handles uploading a new shirt image."""
    file = request.files.get('file')
    
    if file and file.filename.endswith('.png'):
        # Save file to the uploads folder
        file_path = os.path.join('static/uploads', file.filename)
        
        try:
            file.save(file_path)
            # Reload shirt images after uploading new shirt
            global shirt_images
            shirt_images = load_shirt_images()
            return jsonify({"message": "Shirt uploaded successfully!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type. Only .png files allowed."}), 400

# API to stream video with a shirt
@bp.route('/api/stream_video_feed', methods=['GET'])
def stream_video_feed_route():
    global shirt_index
    shirt_index = request.args.get('shirt_index', 0, type=int)
    print(f"Streaming video with shirt index: {shirt_index}")
    
    # Run the video stream in a separate thread to prevent blocking
    thread = threading.Thread(target=stream_video_feed, args=(shirt_index,))
    thread.daemon = True
    thread.start()
    
    return Response(stream_video_feed(shirt_index), mimetype='multipart/x-mixed-replace; boundary=frame')
