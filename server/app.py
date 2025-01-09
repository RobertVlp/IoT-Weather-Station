import json
import joblib
import sklearn
from flask import Flask, request, jsonify
from azure.iot.device import IoTHubDeviceClient, Message

app = Flask(__name__)

# Load ML model
model = joblib.load('weather_model.pkl')
scaler = joblib.load('weather_scaler.pkl')
scaler.feature_names_in_ = None

prediction_labels = {0: 'Cloudy', 1: 'Rainy', 2: 'Snowy', 3: 'Sunny'}

# Load configuration
with open("config.json") as f:
    config = json.loads(f.read())

CONNECTION_STRING = config["CONNECTION_STRING"]
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

@app.route('/weather', methods=['POST'])
def receive_weather_data():
    data = request.json
    print(f'Received data: {data}')

    # Make prediction
    model_data = [[data['temperature'], data['humidity'], data['pressure'], data['light']]]
    prediction = model.predict(scaler.transform(model_data))

    # Prepare data for Azure IoT Hub
    message = {
        'temperature': data['temperature'],
        'humidity': data['humidity'],
        'pressure': data['pressure'],
        'light': data['light'],
        'prediction': prediction_labels[prediction[0]]
    }

    try:
        # Send data to Azure IoT Hub
        msg = Message(json.dumps(message))
        client.send_message(msg)

        return jsonify(message), 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
