import os
import base64
import numpy as np
import logging
import sys
from flask import Flask, request, render_template, jsonify
from keras.models import load_model
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime, timezone
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Model path
model_path = r"C:\Users\cuted\Desktop\plant disease prediction\modell.keras"
logger.info(f"Model path: {os.path.abspath(model_path)}")

# Load the model
try:
    model = load_model(model_path)
    logger.info('Model loaded successfully.')
except Exception as e:
    logger.error(f"Error loading model: {e}")

# Label dictionary
labels = {
    0: 'Eggplantspot',
    1: 'Healthy',
    2: 'Potatospot',
    3: 'Powdery',
    4: 'Rust',
    5: 'Tomatospot',
    6: 'bananaspot',
    7: 'chilispot',
    8: 'cottonspot',
    9: 'sugarcanespot'
}

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['plant_disease_db']  # Use or create the database
collection = db['images']  # Use or create the collection to store the disease info

# Function to process the image and get predictions
def get_result(image_path):
    try:
        # Resize the image to match the model's expected input shape (224, 224)
        img = load_img(image_path, target_size=(224, 224))  # Change to (224, 224)
        x = img_to_array(img)  # Convert the image to an array
        x = x.astype('float32') / 255.0  # Normalize the pixel values
        x = np.expand_dims(x, axis=0)  # Add batch dimension for model input

        predictions = model.predict(x)[0]  # Get model predictions
        return predictions
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None

# Store the prediction result in MongoDB under the collection named after the predicted label
def store_result_in_mongodb(image_filename, predicted_label):
    try:
        # Create a collection name based on the predicted label
        collection_name = predicted_label.lower()  # Convert label to lowercase for consistency
        collection = db[collection_name]  # Access the collection dynamically

        # Create a document to store with additional fields for Symptoms, Medicine, and Cure
        document = {
            'image_filename': image_filename,
            'predicted_label': predicted_label,
            'Symptoms': 'Sample symptom for ' + predicted_label,
            'Medicine': 'Sample medicine for ' + predicted_label,
            'Cure': 'Sample cure for ' + predicted_label,
            'timestamp': datetime.now(timezone.utc)  # Using timezone-aware datetime
        }

        # Insert the document into the collection
        collection.insert_one(document)
        logger.info(f"Result stored in collection '{collection_name}'.")
    except Exception as e:
        logger.error(f"Error storing result in MongoDB: {e}")

# Fetch details from MongoDB for a specific label from the corresponding collection
def fetch_details_from_db(label):
    try:
        # Normalize the label to match your collection names
        collection_name = label.lower()  # Convert label to lowercase for consistency

        # Fetch details from the specific collection
        collection = db[collection_name]
        result = collection.find_one({'predicted_label': label})
        
        if result:
            formatted_details = {
                'symptoms': result.get('Symptoms', 'No data available'),
                'medicine': result.get('Medicine', 'No data available'),
                'cure': result.get('Cure', 'No data available')
            }
            return formatted_details
        else:
            return {'Symptoms': 'No data available', 'Medicine': 'No data available', 'Cure': 'No data available'}
    except Exception as e:
        logger.error(f"Error fetching details from MongoDB: {e}")
        return {'Symptoms': 'Error fetching details', 'Medicine': 'Error fetching details', 'Cure': 'Error fetching details'}

@app.route('/', methods=['GET'])
def index():
    logger.info('Serving index page')
    return render_template('index.html')  # Serve the HTML page

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']  # Get the uploaded image file
        logger.info(f"Received file: {f.filename}")

        basepath = os.path.dirname(__file__)
        upload_path = os.path.join(basepath, 'uploads')
        
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        file_path = os.path.join(upload_path, secure_filename(f.filename))
        f.save(file_path)
        logger.info(f"File saved to: {file_path}")
        
        # Get the image prediction result
        predictions = get_result(file_path)
        if predictions is None:
            logger.error('Error processing the image.')
            return jsonify({'error': 'Error processing the image.'}), 500

        predicted_label = labels[np.argmax(predictions)]  # Find the predicted label
        logger.info(f"Predicted label: {predicted_label}")
        
        store_result_in_mongodb(f.filename, predicted_label)
        
        # Fetch details from MongoDB for the predicted label
        db_details = fetch_details_from_db(predicted_label)

        # Convert the image to base64 to display it on the frontend
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({
            'image_base64': encoded_string,  # Send base64-encoded image
            'predicted_label': predicted_label,
            'db_details': db_details
        })

@app.route('/exit', methods=['GET'])
def exit_app():
    logger.info("Shutting down the server.")
    sys.exit("Server is shutting down...")

if __name__ == '__main__':
    app.run(debug=True)
