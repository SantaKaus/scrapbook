import sys
sys.path.insert(0, 'lib')
from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif  # Import the pillow_heif module to handle .heic files
import random
import boto3
from botocore.exceptions import NoCredentialsError
from io import BytesIO

app = Flask(__name__)

# Configuration
S3_BUCKET = 'kausnmar'  # Replace with your S3 bucket name
S3_REGION = 'us-east-2'  # Replace with your S3 region

# AWS Credentials (hardcoded for development)

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION,
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

@app.route('/')
def index():
    # List images from the S3 bucket
    images = list_s3_images()

    # Shuffle images for random order
    random.shuffle(images)

    # Create image URLs and assign random rotation angles
    image_data = [
        {
            'url': f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{image}",
            'angle': random.randint(-15, 15)  # Random angle for scrapbook effect
        }
        for image in images
    ]
    print(image_data)

    return render_template('index.html', image_data=image_data)

def list_s3_images():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except Exception as e:
        print(f"Error listing images from S3: {e}")
        return []

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

    # Convert image to JPG
    try:
        if ext.lower() == '.heic':
            # Handle HEIC files
            heif_file = pillow_heif.read_heif(file)
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw"
            )
        else:
            # Handle other image formats
            image = Image.open(file)

        image = image.convert('RGB')  # Convert to RGB
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')  # Save image to BytesIO
        image_bytes.seek(0)

        # Upload to S3
        s3_client.upload_fileobj(image_bytes, S3_BUCKET, f"{jpg_filename}", ExtraArgs={'ACL': 'public-read'})

    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'})

    return jsonify({'message': 'File uploaded and converted to JPG successfully', 'filename': jpg_filename})

if __name__ == '__main__':
    app.run(debug=True)
