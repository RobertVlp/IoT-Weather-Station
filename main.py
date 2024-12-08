import time
import json
import ntptime
import network
import urequests
import ubinascii
from BME280 import BME280
from machine import I2C, Pin, ADC
from AzureSasToken import GenerateAzureSasToken

# Wi-Fi Details
WIFI_SSID = "TP-Link_FxF"
WIFI_PASSWORD = "fxf2503#"

# Azure IoT Hub Details
HUB_NAME = "iot-weather-station.azure-devices.net"
DEVICE_ID = "raspberrypipico"
DEVICE_KEY = "m+nGJa3R/bPs+TVbHbeT3rfVlQARIlJrK9O8iAMhVsA="

i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=10000)
bme280 = BME280(i2c=i2c)

try:
    ntptime.settime()
    print("Time synchronized successfully.")
except Exception as e:
    print("Failed to synchronize time:", e)

# Wi-Fi Connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        time.sleep(1)

    print("Connected to Wi-Fi:", wlan.ifconfig())

def read_sensors():
    try:
        temperature = float(bme280.temperature.rstrip("C"))
        humidity = float(bme280.humidity.rstrip("%"))
        pressure = float(bme280.pressure.rstrip("hPa"))
    except OSError as e:
        print(f"Error reading sensor data: {e}")

    try:
        adc = ADC(Pin(26, Pin.PULL_UP))
        value = adc.read_u16()
        light = round(value / 65535 * 100, 2) * 100

    except OSError as e:
        print(f"Error reading light sensor: {e}")

    data = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "light": light
    }

    return json.dumps(data)

# Send Data to Azure IoT Hub
def send_data_to_azure():
    sas_token = GenerateAzureSasToken(f"{HUB_NAME}/devices/{DEVICE_ID}", DEVICE_KEY, int(time.time()) + 3600)

    url = f"https://{HUB_NAME}/devices/{DEVICE_ID}/messages/events?api-version=2018-06-30"

    headers = {
        "Authorization": sas_token,
        "Content-Type": "application/json"
    }

    payload = read_sensors()
    print("Sending data to Azure IoT Hub...")

    response = urequests.post(url, headers=headers, data=payload)

    if response.status_code == 204:
        print("Data sent successfully!: ", payload)
    else:
        print("Failed to send data:", response.text)

    response.close()

connect_wifi()

while True:
    send_data_to_azure()
    time.sleep(30)  # Send data every 30 seconds