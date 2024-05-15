import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import cv2
from PIL import Image
import numpy as np
import base64
import io
import tkinter as tk
from PIL import ImageTk, Image
import base64
import requests
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

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

root = tk.Tk()
canvas = tk.Canvas(root, width=500, height=400)
canvas.pack()

brush_colour = "black"

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def draw_brush(event, brush_width, brush_type2):
    x1 = event.x - 1
    y1 = event.y - 1
    x2 = event.x + 1
    y2 = event.y + 1
    canvas.create_line(x1, y1, x2, y2, fill=brush_colour, width=brush_width, capstyle=brush_type2, smooth=True)


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
            binary_inverse_pil = binary_inverse_pil.resize((500, 400))
            binary_inverse_np = np.array(binary_inverse_pil)
            
            # Define the canvas dimensions
            canvas_width = 500
            canvas_height = 400

            # Define the number of rows and columns for your grid
            n_rows = 3
            n_cols = 3

            # Calculate cell width and cell height
            cell_width = canvas_width // n_cols
            cell_height = canvas_height // n_rows
            
            if canvas_width % n_cols != 0:
                cell_width += 1
            if canvas_height % n_rows != 0:
                cell_height += 1
            # Draw grid lines on the image
            for i in range(1, n_rows):
                cv2.line(binary_inverse_np, (0, i * cell_height), (canvas_width, i * cell_height), (0, 0, 255), 1)
            for j in range(1, n_cols):
                cv2.line(binary_inverse_np, (j * cell_width, 0), (j * cell_width, canvas_height), (0, 0, 255), 1)


            # Convert the numpy array back to a PIL image
            binary_inverse_pil_with_grid = Image.fromarray(binary_inverse_np)
            
            pil_img = binary_inverse_pil_with_grid
            
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

# Flask route to process images with the selected brush
@app.route('/process_with_brush', methods=['POST'])
def process_with_brush(self):
    try:
        # Get the selected brush option from the request
        brush_option = request.form.get('brush')
        # Apply the selected brush option
        if brush_option == 'round_brush':
            draw_brush(self)
        # Implement logic for other brush options as needed
        else:
            # Handle invalid brush option
            return jsonify({'error': 'Invalid brush option'})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred during image processing'})

        
        # elif brush_option == 'slash_brush':
        #     # Apply slash brush logic
        #     pass
        # elif brush_option == 'ubrush':
        #     # Apply up fan brush logic
        #     pass
        # elif brush_option == 'dbrush':
        #     # Apply down fan brush logic
        #     pass
        # elif brush_option == 'lbrush':
        #     # Apply left fan brush logic
        #     pass
        # elif brush_option == 'rbrush':
        #     # Apply right fan brush logic
        #     pass
        # elif brush_option == 'sbrush':
        #     # Apply smudge brush logic
        #     pass
        # elif brush_option == 'eraser':
        #     # Apply eraser logic
        #     pass
        # else:
        #     # Handle invalid brush option
        #     pass
        # return jsonify({'error': 'Invalid file format'})


@app.route('/receive_canvas_data', methods=['POST'])
def receive_canvas_data():
    # Get canvas data from the client request
    canvas_data = request.json.get('canvasData')
    
    # Return the canvas data along with the success status
    return jsonify({'status': 'success', 'canvasData': canvas_data})


@socketio.on('update_canvas')
def update_canvas(self):
    try:
        data = {'canvasData': 'your_canvas_data_here'}

       # Set the content type header to JSON
        headers = {'Content-Type': 'application/json'}

# Make the POST request with JSON data and headers
        response = requests.post('http://localhost:5000/process_with_brush', json=data, headers=headers)

# Check the response status
        if response.status_code == 200:
          print("Request successful")
          print(response.json())
        else:
          print("Error:", response.status_code)
        # Get canvas data from the server
        response = requests.post('http://localhost:5000/receive_canvas_data')
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()

            # Decode base64 canvas data to an image
            canvas_data = base64.b64decode(data.get('canvasData', ''))
            img = Image.open(io.BytesIO(canvas_data))
            photo = ImageTk.PhotoImage(img)

            # Update Tkinter canvas with the received image
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.photo = photo

        else:
            print("Failed to receive canvas data. Status code:", response.status_code)

    except Exception as e:
        print("Error:", e)

    # Schedule the next update
    self.after(1000, self.update_canvas)




if __name__ == '__main__':
    app.run(debug=True)
