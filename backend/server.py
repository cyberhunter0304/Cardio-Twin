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

# Alert thresholds
alert_thresholds = {
    "heart_rate_high": 170,
    "heart_rate_low": 50,
    "blood_pressure_high": 140,
    "blood_pressure_low": 90,
    "st_depression_high": 2.0
}

# Store alerts
alerts = []
alert_lock = Lock()

# Live simulation data
latest_data = {
    "trestbps": 120,  # Blood Pressure
    "chol": 200,      # Cholesterol (static)
    "thalach": 150,   # Heart Rate
    "exang": 0,       # Angina
    "oldpeak": 1.0,   # ST Depression
    "prediction": "Waiting...",
    "future_predictions": []  # Store future predictions
}

running = False  # Control simulation
data_lock = Lock()  # Thread-safe access to latest_data

# Store previous values for smoothing
previous_values = {
    "trestbps": 120,
    "thalach": 100,
    "oldpeak": 1.0
}

def smooth_value(current, previous, max_change=5):
    """Smoothly transition between values with a maximum change limit."""
    if abs(current - previous) > max_change:
        if current > previous:
            return previous + max_change
        else:
            return previous - max_change
    return current

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

def check_alerts():
    """Check for any threshold violations and create alerts."""
    global alerts
    with alert_lock:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Check heart rate
        if latest_data["thalach"] > alert_thresholds["heart_rate_high"]:
            alerts.append({
                "timestamp": current_time,
                "type": "heart_rate",
                "message": f"High heart rate detected: {latest_data['thalach']} BPM",
                "severity": "high",
                "acknowledged": False
            })
        elif latest_data["thalach"] < alert_thresholds["heart_rate_low"]:
            alerts.append({
                "timestamp": current_time,
                "type": "heart_rate",
                "message": f"Low heart rate detected: {latest_data['thalach']} BPM",
                "severity": "medium",
                "acknowledged": False
            })
            
        # Check blood pressure
        if latest_data["trestbps"] > alert_thresholds["blood_pressure_high"]:
            alerts.append({
                "timestamp": current_time,
                "type": "blood_pressure",
                "message": f"High blood pressure detected: {latest_data['trestbps']} mmHg",
                "severity": "high",
                "acknowledged": False
            })
        elif latest_data["trestbps"] < alert_thresholds["blood_pressure_low"]:
            alerts.append({
                "timestamp": current_time,
                "type": "blood_pressure",
                "message": f"Low blood pressure detected: {latest_data['trestbps']} mmHg",
                "severity": "medium",
                "acknowledged": False
            })
            
        # Check ST depression
        if latest_data["oldpeak"] > alert_thresholds["st_depression_high"]:
            alerts.append({
                "timestamp": current_time,
                "type": "st_depression",
                "message": f"High ST depression detected: {latest_data['oldpeak']}",
                "severity": "critical",
                "acknowledged": False
            })

def generate_future_predictions():
    """Generate predictions for various future time points."""
    global latest_data
    future_predictions = []
    
    # Current values as base
    base_trestbps = latest_data["trestbps"]
    base_thalach = latest_data["thalach"]
    base_oldpeak = latest_data["oldpeak"]
    
    # Define time points and their corresponding scale factors for variation
    time_points = [
        (30, 2.0),   # 30 minutes - significant variation
        (360, 3.0),  # 6 hours - large variation
        (1440, 4.0), # 1 day - very large variation
        (2880, 5.0)  # 2 days - maximum variation
    ]
    
    for minutes, scale_factor in time_points:
        # Calculate time label
        if minutes < 60:
            time_label = f"+{minutes}min"
        elif minutes < 1440:
            hours = minutes // 60
            time_label = f"+{hours}h"
        else:
            days = minutes // 1440
            time_label = f"+{days}d"
        
        # Generate values with increasing variation based on time
        future_trestbps = int(np.clip(
            np.random.normal(loc=base_trestbps, scale=5*scale_factor),
            90, 200
        ))
        future_thalach = int(np.clip(
            np.random.normal(loc=base_thalach, scale=8*scale_factor),
            60, 200
        ))
        future_oldpeak = round(np.clip(
            np.random.normal(loc=base_oldpeak, scale=0.5*scale_factor),
            0, 6.2
        ), 2)
        
        # Prepare input for ML model
        input_data = np.array([[  
            float(user_static_data["age"]), float(user_static_data["sex"]), float(user_static_data["cp"]),
            float(future_trestbps), float(latest_data["chol"]), float(user_static_data["fbs"]),
            float(user_static_data["restecg"]), float(future_thalach), float(latest_data["exang"]),
            float(future_oldpeak), float(user_static_data["slope"])
        ]], dtype=np.float64)
        
        # Make Prediction
        prediction = heart_model.predict(input_data)[0]
        
        future_predictions.append({
            "time": time_label,
            "trestbps": future_trestbps,
            "thalach": future_thalach,
            "oldpeak": future_oldpeak,
            "prediction": "High Risk" if prediction == 1 else "Low Risk"
        })
    
    return future_predictions

def simulate_realistic_data():
    """Simulate real human-like heart readings using Gaussian distribution."""
    global latest_data, previous_values
    while True:
        if not running:
            print("[INFO] Simulation is paused. Waiting...")
            time.sleep(1)
            continue

        try:
            with data_lock:
                # Generate new values with smaller variations
                new_trestbps = int(np.clip(np.random.normal(loc=120, scale=5), 90, 200))
                new_thalach = int(np.clip(np.random.normal(loc=100, scale=30), 60, 200))
                new_oldpeak = round(np.clip(np.random.normal(loc=1.5, scale=0.5), 0, 6.2), 2)

                # Smooth the transitions
                latest_data["trestbps"] = smooth_value(new_trestbps, previous_values["trestbps"], 3)
                latest_data["thalach"] = smooth_value(new_thalach, previous_values["thalach"], 10)
                latest_data["oldpeak"] = round(smooth_value(new_oldpeak, previous_values["oldpeak"], 0.2), 2)

                # Update previous values
                previous_values["trestbps"] = latest_data["trestbps"]
                previous_values["thalach"] = latest_data["thalach"]
                previous_values["oldpeak"] = latest_data["oldpeak"]

                # Keep cholesterol static
                latest_data["chol"] = 200  # Static cholesterol value
                latest_data["exang"] = random.choice([0, 1])

                # Check for alerts
                check_alerts()

                # Prepare input for ML model
                input_data = np.array([[  
                    float(user_static_data["age"]), float(user_static_data["sex"]), float(user_static_data["cp"]),
                    float(latest_data["trestbps"]), float(latest_data["chol"]), float(user_static_data["fbs"]),
                    float(user_static_data["restecg"]), float(latest_data["thalach"]), float(latest_data["exang"]),
                    float(latest_data["oldpeak"]), float(user_static_data["slope"])
                ]], dtype=np.float64)

                # Make Prediction
                prediction = heart_model.predict(input_data)[0]  
                latest_data["prediction"] = "High Risk" if prediction == 1 else "Low Risk"
                
                # Generate future predictions
                latest_data["future_predictions"] = generate_future_predictions()

        except Exception as e:
            print("❌ Error in ML Model Prediction:", e)
            latest_data["prediction"] = "Error"

        time.sleep(2)  

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

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Return the list of unacknowledged alerts."""
    with alert_lock:
        unacknowledged = [alert for alert in alerts if not alert["acknowledged"]]
        return jsonify(unacknowledged)

@app.route('/alerts/<int:index>/acknowledge', methods=['POST'])
def acknowledge_alert(index):
    """Acknowledge a specific alert."""
    with alert_lock:
        if 0 <= index < len(alerts):
            alerts[index]["acknowledged"] = True
            return jsonify({"message": "Alert acknowledged"})
        return jsonify({"error": "Invalid alert index"}), 400

@app.route('/thresholds', methods=['GET', 'POST'])
def manage_thresholds():
    """Get or update alert thresholds."""
    global alert_thresholds
    if request.method == 'POST':
        new_thresholds = request.json
        for key, value in new_thresholds.items():
            if key in alert_thresholds:
                try:
                    value = float(value)
                    if value < 0:
                        return jsonify({"error": f"Negative values are not allowed for {key}"}), 400
                    alert_thresholds[key] = value
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid value for {key}"}), 400
        return jsonify({"message": "Thresholds updated"})
    return jsonify(alert_thresholds)

if __name__ == "__main__":
    print("[INFO] Starting Flask server...")
    app.run(debug=True)