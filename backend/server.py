import random
import time
import threading
import pickle
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Lock

app = Flask(__name__)
CORS(app)

# Load the trained ML Model
with open('heart_model.pkl', 'rb') as file:
    heart_model = pickle.load(file)

# Store user input
user_static_data = {
    "age": 50,
    "sex": 1,
    "cp": 0,
    "fbs": 0,
    "restecg": 0,
    "slope": 1
}

# Live simulation data
latest_data = {
    "trestbps": 120,  # Blood Pressure
    "chol": 200,      # Cholesterol
    "thalach": 150,   # Heart Rate
    "exang": 0,       # Angina
    "oldpeak": 1.0,   # ST Depression
    "prediction": "Waiting..."
}

running = False  # Control simulation
data_lock = Lock()  # Thread-safe access to latest_data


@app.route('/start', methods=['POST'])
def start_simulation():
    """Start the simulation with user inputs."""
    global user_static_data, running
    data = request.json
    if not data:
        return jsonify({"error": "No input data received"}), 400

    # Populate user_static_data with default values if fields are missing
    user_static_data = {
        "age": data.get("age", 50),
        "sex": data.get("sex", 1),
        "cp": data.get("cp", 0),
        "fbs": data.get("fbs", 0),
        "restecg": data.get("restecg", 0),
        "slope": data.get("slope", 1)
    }

    # Validate user_static_data
    for key, value in user_static_data.items():
        if value == '':
            print(f"❌ Error: Empty value found in user_static_data for key: {key}")
            user_static_data[key] = 0  # Set default value if empty

    running = True
    print("[INFO] Simulation started with:", user_static_data)
    print("[INFO] Running flag set to:", running)
    return jsonify({"message": "Simulation started"})


def simulate_realistic_data():
    """Simulate real human-like heart readings using Gaussian distribution."""
    global latest_data
    while True:
        if not running:
            print("[INFO] Simulation is paused. Waiting...")
            time.sleep(1)
            continue

        try:
            # Simulate human-like variations using Gaussian (normal) distribution
            with data_lock:
                latest_data["trestbps"] = int(np.clip(np.random.normal(loc=120, scale=10), 90, 200))  # BP (90-200)
                latest_data["chol"] = int(np.clip(np.random.normal(loc=200, scale=30), 100, 400))    # Cholesterol (100-400)
                latest_data["thalach"] = int(np.clip(np.random.normal(loc=150, scale=15), 60, 200))  # Heart Rate (60-200)
                latest_data["exang"] = random.choice([0, 1])  # Binary: 0 or 1
                latest_data["oldpeak"] = round(np.clip(np.random.normal(loc=1.5, scale=1.0), 0, 6.2), 1)

                # Prepare input for ML model (Ensure correct shape & type)
                input_data = np.array([[  
                    float(user_static_data["age"]), float(user_static_data["sex"]), float(user_static_data["cp"]),
                    float(latest_data["trestbps"]), float(latest_data["chol"]), float(user_static_data["fbs"]),
                    float(user_static_data["restecg"]), float(latest_data["thalach"]), float(latest_data["exang"]),
                    float(latest_data["oldpeak"]), float(user_static_data["slope"])
                ]], dtype=np.float64)  # Convert to float64

                # Debugging: Print input data
                print("[INFO] Input Data for ML Model:", input_data)

                # Make Prediction
                prediction = heart_model.predict(input_data)[0]  
                latest_data["prediction"] = "High Risk" if prediction == 1 else "Low Risk"

                # Debugging: Print Updated Values
                print("Updated Data:", latest_data)

        except Exception as e:
            print("❌ Error in ML Model Prediction:", e)
            latest_data["prediction"] = "Error"

        time.sleep(1)  # Update every 1 second


# Start the simulation thread
threading.Thread(target=simulate_realistic_data, daemon=True).start()
print("[INFO] Simulation thread started.")


@app.route('/prediction', methods=['GET'])
def get_prediction():
    """Return the latest simulated heart health data."""
    try:
        with data_lock:
            # Convert NumPy types to JSON-safe Python types
            safe_latest_data = {
                k: int(v) if isinstance(v, np.integer) else float(v) if isinstance(v, np.floating) else v
                for k, v in latest_data.items()
            }
            return jsonify(safe_latest_data)
    except Exception as e:
        print("JSON Serialization Error:", e)
        return jsonify({"error": "Failed to generate prediction data"}), 500


if __name__ == "__main__":
    print("[INFO] Starting Flask server...")
    app.run(debug=True)