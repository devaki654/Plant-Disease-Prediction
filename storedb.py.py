from pymongo import MongoClient
from datetime import datetime, timezone

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['plant_disease_db']

# Define the disease details
disease_details = {
    'Eggplantspot': {'Symptoms': 'Leaf spot with purple edges', 'Medicine': 'Fungicide A', 'Cure': 'Prune affected leaves'},
    'Healthy': {'Symptoms': 'No symptoms', 'Medicine': 'None', 'Cure': 'Maintain healthy conditions'},
    'Potatospot': {'Symptoms': 'Brown spots on leaves', 'Medicine': 'Copper-based fungicide', 'Cure': 'Remove affected leaves'},
    'Powdery': {'Symptoms': 'White powdery coating on leaves', 'Medicine': 'Fungicide B', 'Cure': 'Increase air circulation'},
    'Rust': {'Symptoms': 'Rust-colored spots on leaves', 'Medicine': 'Rust fungicide', 'Cure': 'Prune infected branches'},
    'Tomatospot': {'Symptoms': 'Dark spots on tomato leaves', 'Medicine': 'Tomato fungicide', 'Cure': 'Remove infected leaves'},
    'bananaspot': {'Symptoms': 'Spots on banana leaves', 'Medicine': 'Banana fungicide', 'Cure': 'Prune infected areas'},
    'chilispot': {'Symptoms': 'Spots on chili plant leaves', 'Medicine': 'Chili fungicide', 'Cure': 'Increase sunlight exposure'},
    'cottonspot': {'Symptoms': 'Spots on cotton leaves', 'Medicine': 'Cotton fungicide', 'Cure': 'Remove affected leaves'},
    'sugarcanespot': {'Symptoms': 'Yellow spots on sugarcane leaves', 'Medicine': 'Sugarcane fungicide', 'Cure': 'Remove infected leaves'}
}

# Function to store disease details in MongoDB
def store_all_disease_details():
    try:
        # Iterate through the disease_details dictionary and insert each entry
        for label, details in disease_details.items():
            # Ensure the collection name is in lowercase
            collection_name = label.lower()

            # Access the collection dynamically
            collection = db[collection_name]

            # Create a document to store
            document = {
                'predicted_label': label,
                'Symptoms': details['Symptoms'],
                'Medicine': details['Medicine'],
                'Cure': details['Cure'],
                'timestamp': datetime.now(timezone.utc)  # Using timezone-aware datetime
            }

            # Insert the document into the collection
            collection.insert_one(document)
            print(f"Result stored in collection '{collection_name}'.")

    except Exception as e:
        print(f"Error storing result in MongoDB: {e}")

# Call the function to store all disease details
store_all_disease_details()
