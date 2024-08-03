import sys
sys.path.insert(0, 'lib')
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif  # Import the pillow_heif module to handle .heic files
import random

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Get list of images in the upload folder
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    
    # Shuffle images for random order
    random.shuffle(images)

    # Create image URLs and assign random rotation angles
    image_data = [
        {
            'url': os.path.join(app.config['UPLOAD_FOLDER'], image),
            'angle': random.randint(-15, 15)  # Random angle for scrapbook effect
        }
        for image in images
    ]
    
    return render_template('index.html', image_data=image_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Secure the filename and get the base name without extension
    filename = secure_filename(file.filename)
    base_name, ext = os.path.splitext(filename)
    jpg_filename = f"{base_name}.jpg"

    # Check for HEIC extension
    if ext.lower() == '.heic':
        # Use pillow-heif to handle HEIC files
        try:
            heif_file = pillow_heif.read_heif(file)  # Read the HEIC file
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw"
            )
            image = image.convert('RGB')  # Convert to RGB to ensure compatibility with JPG format
            jpg_path = os.path.join(app.config['UPLOAD_FOLDER'], jpg_filename)
            image.save(jpg_path, 'JPEG')  # Save the image as JPG
        except Exception as e:
            return jsonify({'error': f'Failed to process HEIC file: {str(e)}'})
    else:
        # Handle other image formats
        try:
            image = Image.open(file)
            image = image.convert('RGB')  # Convert to RGB to ensure compatibility with JPG format
            jpg_path = os.path.join(app.config['UPLOAD_FOLDER'], jpg_filename)
            image.save(jpg_path, 'JPEG')  # Save the image as JPG
        except Exception as e:
            return jsonify({'error': str(e)})

    return jsonify({'message': 'File uploaded and converted to JPG successfully', 'filename': jpg_filename})

@app.route('/static/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

