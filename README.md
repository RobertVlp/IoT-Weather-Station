## IoT Weather Station

A simple weather station that uses a Raspberry Pi Pico W and sensors to collect temperature, humidity, pressure and light data. The data is then sent to a cloud service (Azure IoT Hub) for storage and visualization.

A ML model is used to predict the weather based on the collected data. The model is trained using a dataset of weather data from Kaggle.

### Setup
1. Clone the repository
2. Create a virtual environment for the server and install the required packages
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. Create a `config.json` file inside the server directory with the following content:
```json
{
    "CONNECTION_STRING": "<your-iot-hub-connection-string>",
}
```
4. Create a `config.json` file in the root directory and upload it to the Raspberry Pi Pico W:
```json
{
    "WIFI_SSID": "<your-wifi-ssid>",
    "WIFI_PASSWORD": "<your-wifi-password>",
    "SERVER_URL": "<your-server-url>",
}
```
5. Upload the BME280 and lcd libraries to the Raspberry Pi Pico W
6. Run the server
```bash
flask run --host=0.0.0.0
```
7. Run the main.py script on the Raspberry Pi Pico W

### Hardware
- Raspberry Pi Pico W
- BME280 sensor
- LDR sensor
- LCD display 16x2

### Software
- MicroPython
- Azure services (IoT Hub, Stream Analytics, Power BI)
