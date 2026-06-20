import os
import certifi # <-- 1. Import certifi here
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
CORS(app)

mongo_uri = os.getenv("MONGO_URI")

# 2. Add tlsCAFile=certifi.where() to your MongoClient
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except ConnectionFailure:
    print("❌ Failed to connect to MongoDB. Check your connection string.")
# 2. Select the database and collection
db = client['sample_mflix']
users_collection = db['users']

# --- ROUTES ---

@app.route('/users', methods=['GET'])
def get_users():
    """Retrieve all users from the database."""
    try:
        users = []
        # Find all documents in the collection
        for user in users_collection.find():
            users.append({
                "id": str(user['_id']), 
                "name": user.get('name', 'No Name Provided'), 
                "email": user.get('email', 'No Email Provided')
            })
            
        return jsonify(users), 200
    except Exception as e:
        # Added error handling just in case the query fails
        return jsonify({"error": str(e)}), 500


@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user in the database."""
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing name or email"}), 400

    new_user = {
        "name": data['name'],
        "email": data['email']
    }
    
    # Insert the document into MongoDB
    try:
        result = users_collection.insert_one(new_user)
        return jsonify({
            "message": "User created successfully", 
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app on port 3000
    app.run(debug=True, port=3000)