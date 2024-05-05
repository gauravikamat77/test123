import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import cv2
from PIL import Image
import numpy as np
import base64
import io

app = Flask(__name__)

# Define the upload and processed image directories
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('start_page.html')

@app.route('/select_and_process_image', methods=['POST'])
def select_and_process_image():
    try:
        if 'image_file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['image_file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Load the selected image
            img = cv2.imread(filepath)
            if img is None:
                return jsonify({'error': 'Failed to load image'})
            
            height, width, _ = img.shape
            
            # Convert to Grayscale
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Gaussian Blur
            img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)

            # Canny Edge Detection
            img_edge = cv2.Canny(img_gray, 100, 200)

            # Dilate Edges
            kernel_dilate = np.ones((1, 1), np.uint8)
            thick = cv2.dilate(img_edge, kernel_dilate, iterations=1)

            # Sharpening
            kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(thick, -1, kernel_sharpen)

            # Thresholding
            threshold_value = 120
            _, binary_inverse = cv2.threshold(sharpened, threshold_value, 255, cv2.THRESH_BINARY_INV)
            binary_inverse_pil = Image.fromarray(binary_inverse)

            # Resize the processed image to match the dimensions of the selected image
            binary_inverse_pil = binary_inverse_pil.resize((width, height))

            # Convert processed image to PIL format
            pil_img = binary_inverse_pil
            
            # Save the processed image
            processed_filename = f"processed_{filename}"
            processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            pil_img.save(processed_filepath)
            
            # Convert PIL image to base64
            buffered = io.BytesIO()
            pil_img.save(buffered, format="JPEG")
            processed_image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Modify the return statement to include the processed image filename
            return jsonify({'success': 'Image processed successfully!', 'data': {'processed_image_data': processed_image_data, 'processed_filename': processed_filename}})
        
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred during image processing'})

    return jsonify({'error': 'Invalid file format'})

   
@app.route('/page_one')
def page_one():
    # Add logic for Page One
    return render_template('page_one.html')


# from flask import send_from_directory

# @app.route('/process_image', methods=['POST'])
# def process_image():
#     try:
#         if 'image_file' not in request.files:
#             return jsonify({'error': 'No file part'})
        
#         file = request.files['image_file']
#         if file.filename == '':
#             return jsonify({'error': 'No selected file'})
        
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
#             # Load the selected image
#             img = cv2.imread(input_filepath)
#             if img is None:
#                 return jsonify({'error': 'Failed to load image'})
            
#             height, width, _ = img.shape
            
#             # Convert to Grayscale
#             img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#          # Gaussian Blur
#             img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)

#     # Canny Edge Detection
#             img_edge = cv2.Canny(img_gray, 100, 200)

#     # Dilate Edges
#             kernel_dilate = np.ones((1, 1), np.uint8)
#             thick = cv2.dilate(img_edge, kernel_dilate, iterations=1)

#     # Sharpening
#             kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
#             sharpened = cv2.filter2D(thick, -1, kernel_sharpen)

#     # Thresholding
#             threshold_value = 120
#             _, binary_inverse = cv2.threshold(sharpened, threshold_value, 255, cv2.THRESH_BINARY_INV)
#             binary_inverse_pil = Image.fromarray(binary_inverse)

#     # Resize the processed image to match the dimensions of the selected image
#             binary_inverse_pil = binary_inverse_pil.resize((width, height))
  
#             # Save the processed image
#             processed_filename = f"processed_{filename}"
#             processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
#             pil_img.save(processed_filepath)
            
#             # Convert processed image to PIL format
#             pil_img = Image.fromarray(binary_inverse_pil)
            
#             # Convert PIL image to base64
#             buffered = io.BytesIO()
#             pil_img.save(buffered, format="JPEG")
#             processed_image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
#             # Modify the return statement to include the processed image filename
#             return jsonify({'success': 'Image processed successfully!', 'data': {'processed_image_data': processed_image_data, 'processed_filename': processed_filename}})
        
#     except Exception as e:
#         print("Error:", e)
#         return jsonify({'error': 'An error occurred during image processing'})

# @app.route('/processed_images/<filename>')
# def processed_image(filename):
#     return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
