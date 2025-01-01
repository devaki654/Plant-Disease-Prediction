import os
import base64
import numpy as np
from flask import Flask, request, render_template, jsonify
from keras.models import load_model
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime, timezone
from tensorflow.keras.preprocessing.image import load_img, img_to_array

app = Flask(__name__)

# Load the pre-trained model
model_path = 'video.keras'  # Path to your trained model
try:
    model = load_model(model_path)
    print('Model loaded.')
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

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
db = client['plant_disease_db']

# Function to process the image and get predictions
def get_result(image_path):
    try:
        img = load_img(image_path, target_size=(150, 150))  # Resize the image to match model input
        x = img_to_array(img)  # Convert the image to an array
        x = x.astype('float32') / 255.0  # Normalize the pixel values
        x = np.expand_dims(x, axis=0)  # Add batch dimension for model input

        predictions = model.predict(x)[0]  # Get model predictions
        return predictions
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# Store the prediction result in MongoDB
def store_result_in_mongodb(image_filename, predicted_label):
    try:
        document = {
            'image_filename': image_filename,
            'predicted_label': predicted_label,
            'timestamp': datetime.now(timezone.utc)  # Using timezone-aware datetime
        }
        collection = db['predictions']
        collection.insert_one(document)
    except Exception as e:
        print(f"Error storing result in MongoDB: {e}")

# Fetch details from MongoDB for a specific label and return formatted details
def fetch_details_from_db(label):
    try:
        # Normalize the label to match your collection names
        normalized_label = label
        
        if normalized_label in db.list_collection_names():
            result = db[normalized_label].find_one()  # Fetch one document from the collection
            if result:
                formatted_details = {
                    'Symptoms': result.get('Symptoms', 'No data available'),
                    'Medicine': result.get('Medicine', 'No data available'),
                    'Cure': result.get('Cure', 'No data available')
                }
                return formatted_details
            else:
                return {'Symptoms': 'No data available', 'Medicine': 'No data available', 'Cure': 'No data available'}
        else:
            return {'Symptoms': 'Collection not found', 'Medicine': 'Collection not found', 'Cure': 'Collection not found'}
    except Exception as e:
        print(f"Error fetching details from MongoDB: {e}")
        return {'Symptoms': 'Error fetching details', 'Medicine': 'Error fetching details', 'Cure': 'Error fetching details'}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')  # Serve the HTML page

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']  # Get the uploaded image file

        basepath = os.path.dirname(__file__)
        upload_path = os.path.join(basepath, 'uploads')
        
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        file_path = os.path.join(upload_path, secure_filename(f.filename))
        f.save(file_path)
        
        # Get the image prediction result
        predictions = get_result(file_path)
        if predictions is None:
            return jsonify({'error': 'Error processing the image.'}), 500

        predicted_label = labels[np.argmax(predictions)]  # Find the predicted label
        
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

if __name__ == '__main__':
    app.run(debug=True)
