import time
import json
import ntptime
import network
import urequests
from BME280 import BME280
from i2c_lcd import I2cLcd
from machine import I2C, Pin, ADC, SoftI2C

# Load configuration
with open("config.json") as f:
    config = json.loads(f.read())

WIFI_SSID = config["WIFI_SSID"]
WIFI_PASSWORD = config["WIFI_PASSWORD"]

i2c_0 = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=10000)
bme280 = BME280(i2c=i2c_0)

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

i2c_1 = SoftI2C(scl=Pin(3), sda=Pin(2), freq=10000)
lcd = I2cLcd(i2c_1, I2C_ADDR, totalRows, totalColumns)
lcd.clear()

WINDOW_SIZE = 10
payload = [{} for _ in range(WINDOW_SIZE)]

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
        adc = ADC(Pin(26))
        value = adc.read_u16()
        light = value / 65535 * 100
    except OSError as e:
        print(f"Error reading light sensor: {e}")

    data = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "light": light
    }

    return data

# Send Data to Flask server
def send_data_to_server():
    url = "http://192.168.0.142:5000/weather"

    headers = {
        "Content-Type": "application/json"
    }

    temp = sum([data["temperature"] for data in payload]) / WINDOW_SIZE
    humidity = sum([data["humidity"] for data in payload]) / WINDOW_SIZE
    pressure = sum([data["pressure"] for data in payload]) / WINDOW_SIZE
    light = sum([data["light"] for data in payload]) / WINDOW_SIZE

    data = {
        "temperature": temp,
        "humidity": humidity,
        "pressure": pressure,
        "light": light
    }

    display_on_lcd(data)

    print("Sending data to Flask server...")

    response = urequests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print("Data sent successfully!: ", data)
    else:
        print("Failed to send data:", response.text)

    response.close()

def display_on_lcd(data):
    temp = round(data["temperature"], 2)
    humidity = int(data["humidity"])
    pressure = round(data["pressure"], 2)
    light = int(data["light"])

    lcd.clear()
    lcd.putstr(f"T:{temp}C H:{humidity}%")
    lcd.move_to(0, 1)
    lcd.putstr(f"P:{pressure} L:{light}%")
    lcd.move_to(0, 0)

connect_wifi()

try:
    ntptime.settime()
    print("Time synchronized successfully.")
except Exception as e:
    print("Failed to synchronize time:", e)

while True:
    print("Reading sensor data...")
    for i in range(WINDOW_SIZE):
        data = read_sensors()
        payload[i] = data

        time.sleep(1)

    send_data_to_server()
    time.sleep(10)
