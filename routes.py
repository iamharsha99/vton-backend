from flask import Blueprint, request, session, jsonify, send_file
import os
from video_processing import load_shirt_images, stream_video_feed

bp = Blueprint('routes', __name__)

# Initial load of shirt images
shirt_images = load_shirt_images()

@bp.route('/api/shirts', methods=['GET', 'POST'])
def shirts():
    """Handles fetching and updating the list of shirt images and the selected shirt."""
    global shirt_images
    # Fetch shirt files from the static directory
    shirt_files = [os.path.basename(img) for img in os.listdir('static/uploads') if img.endswith('.png')]
    selected_shirt_index = session.get('shirt_index', 0)
    
    # Ensure selected_shirt_index is valid
    if not (0 <= selected_shirt_index < len(shirt_files)):
        selected_shirt_index = 0
        session['shirt_index'] = selected_shirt_index

    if request.method == 'POST':
        shirt_index = request.json.get('shirt_index')
        if shirt_index is not None and isinstance(shirt_index, int):
            if 0 <= shirt_index < len(shirt_files):
                session['shirt_index'] = shirt_index
                return jsonify({"message": "Shirt selection updated", "selected_shirt_index": shirt_index}), 200
            else:
                return jsonify({"error": "Invalid shirt selection"}), 400
        return jsonify({"error": "Invalid input"}), 400

    return jsonify({"shirts": shirt_files, "selected_shirt_index": selected_shirt_index})

@bp.route('/api/upload_shirt', methods=['POST'])
def upload_shirt():
    """Handles uploading a new shirt image."""
    global shirt_images
    file = request.files.get('file')
    
    if file and file.filename.endswith('.png'):
        # Save file to the uploads folder
        file_path = os.path.join('static/uploads', file.filename)
        
        try:
            file.save(file_path)
            # Reload shirt images after uploading new shirt
            shirt_images = load_shirt_images()
            return jsonify({"message": "Shirt uploaded successfully!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type. Only .png files allowed."}), 400

@bp.route('/api/stream_video_feed')
def stream_video_feed_route():
    """Streams the live video feed with the selected shirt overlay."""
    shirt_index = session.get('shirt_index', 0)
    try:
        # Stream video with the selected shirt index overlay
        return stream_video_feed(shirt_index)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
