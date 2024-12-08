import time
import json
import ntptime
import network
import urequests
import ubinascii
from BME280 import BME280
from i2c_lcd import I2cLcd
from machine import I2C, Pin, ADC, SoftI2C
from AzureSasToken import GenerateAzureSasToken

# Load configuration
with open("config.json") as f:
    config = json.loads(f.read())

WIFI_SSID = config["WIFI_SSID"]
WIFI_PASSWORD = config["WIFI_PASSWORD"]

HUB_NAME = config["HUB_NAME"]
DEVICE_ID = config["DEVICE_ID"]
DEVICE_KEY = config["DEVICE_KEY"]

i2c_0 = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=10000)
bme280 = BME280(i2c=i2c_0)

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

i2c_1 = SoftI2C(scl=Pin(3), sda=Pin(2), freq=10000)
lcd = I2cLcd(i2c_1, I2C_ADDR, totalRows, totalColumns)
lcd.clear()

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

# Read Sensor Data
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
        "light": int(light)
    }

    display_on_lcd(data)

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

def display_on_lcd(data):
    lcd.putstr(f"T:{data['temperature']}C H:{data['humidity']}%")
    lcd.move_to(0, 1)
    lcd.putstr(f"P:{data['pressure']} L:{data['light']}%")
    lcd.move_to(0, 0)

connect_wifi()

while True:
    send_data_to_azure()
    time.sleep(30)  # Send data every 30 seconds
