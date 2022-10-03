from itertools import count
import json
import random
from fhict_cb_01.CustomPymata4 import CustomPymata4
from flask import Flask, render_template, send_from_directory
from datetime import datetime
import os, csv

app = Flask(__name__)

BUTTON1PIN = 8
REDLEDPIN = 4
DHTPIN = 12
LDRPIN = 2

SENSOR_IDS = ["q3bPOMgDza", "Anw2bNFVHb", "rtPGM4n80v", "fFPR9fxgIf", "seZDwgOPZH", "d1ftuVwNyY", "sjLDuO4Lx4", "mFEYsuCfXe", "HyrOWwWXn5", "UeAEMUlYOu"]

humidity_measurement = None
temperature_measurement = None
light_measurement = None


with open('data.csv', 'r') as csvData:
    data = list(csv.reader(csvData))
    data.pop(0)

structuredData = {}
statisticsData = {}

def measure_DHT(data):
    global humidity_measurement, temperature_measurement
    if (data[3] == 0):
        humidity_measurement = data[4]
        temperature_measurement = data[5]

def measure_LDR(data):
    global light_measurement
    light_measurement = data[2]

board = None
try:
    board = CustomPymata4(com_port="COM7")
    board.set_pin_mode_dht(DHTPIN, sensor_type=11,differential=.05, callback=measure_DHT)
    board.set_pin_mode_analog_input(LDRPIN, callback=measure_LDR, differential=10)
except:
    print("The arduino is not connected")

def current_time():
    def format(num):
        if (num < 10):
            return "0" + str(num)
        else:
            return num

    now = datetime.now()

    return f"{format(now.hour)}:{format(now.minute)}:{format(now.second)}"

def refresh_data():
    global data, statisticsData, structuredData
    today = datetime.now().strftime("%A")
    if (board is None):
        data.append([SENSOR_IDS[0], today, 41, current_time(), random.randint(13,35), random.randint(56,85), random.randint(600,800)])
    elif (light_measurement is not None):
        data.append([SENSOR_IDS[0], today, 41, current_time(), temperature_measurement, humidity_measurement, light_measurement])

    if (41 not in structuredData[SENSOR_IDS[0]]): 
        structuredData[SENSOR_IDS[0]][41] = {}
        structuredData[SENSOR_IDS[0]][41][today] = []
    if (today not in structuredData[SENSOR_IDS[0]][41]):
        structuredData[SENSOR_IDS[0]][41][today] = []

    structuredData[SENSOR_IDS[0]][41][today].append(data[-1])

def refresh_statistics():
    global statisticsData

    statisticsData["highest_temperature"] = max(statisticsData["highest_temperature"], data[-1][4])
    statisticsData["highest_humidity"] = max(statisticsData["highest_humidity"], data[-1][5])
    statisticsData["highest_light"] = max(statisticsData["highest_light"], data[-1][6])
    
    statisticsData["lowest_temperature"] = min(statisticsData["lowest_temperature"], data[-1][4])
    statisticsData["lowest_humidity"] = min(statisticsData["lowest_humidity"], data[-1][5])
    statisticsData["lowest_light"] = min(statisticsData["lowest_light"], data[-1][6])

    dataLength = len(data)
    statisticsData["average_light"] = round(((dataLength - 1) * statisticsData["average_light"] + data[-1][4]) / dataLength)
    statisticsData["average_humidity"] = round(((dataLength - 1) * statisticsData["average_humidity"] + data[-1][5]) / dataLength)
    statisticsData["average_temperature"] = round(((dataLength - 1) * statisticsData["average_temperature"] + data[-1][6]) / dataLength)

def init_data():
    global statisticsData, structuredData

    for sensor in SENSOR_IDS:
        structuredData[sensor] = {}
        sensorData = list(filter(lambda val: val[0] == sensor, data))

        for week in list(range(1,5)):
            structuredData[sensor][week] = {}
            weekData = list(filter(lambda val: int(val[2]) == week, sensorData))

            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                structuredData[sensor][week][day] = [val for val in weekData if val[1] == day]

        statisticsData = {}

        statisticsData["average_light"] = 0
        statisticsData["average_humidity"] = 0
        statisticsData["average_temperature"] = 0
        
        statisticsData["highest_light"] = float('-inf')
        statisticsData["highest_humidity"] = float('-inf')
        statisticsData["highest_temperature"] = float('-inf')
        
        statisticsData["lowest_light"] = float('inf')
        statisticsData["lowest_humidity"] = float('inf')
        statisticsData["lowest_temperature"] = float('inf')

    totalTemperature = 0
    totalHumidity = 0
    totalLight = 0

    for value in data:
        totalTemperature += int(value[4])
        totalHumidity += int(value[5])
        totalLight += int(value[6])

        statisticsData["highest_temperature"] = max(statisticsData["highest_temperature"], int(value[4]))
        statisticsData["highest_humidity"] = max(statisticsData["highest_humidity"], int(value[5]))
        statisticsData["highest_light"] = max(statisticsData["highest_light"], int(value[6]))
        
        statisticsData["lowest_temperature"] = min(statisticsData["lowest_temperature"], int(value[4]))
        statisticsData["lowest_humidity"] = min(statisticsData["lowest_humidity"], int(value[5]))
        statisticsData["lowest_light"] = min(statisticsData["lowest_light"], int(value[6]))

        statisticsData["average_light"] = int(totalLight / len(data))
        statisticsData["average_humidity"] = int(totalHumidity / len(data))
        statisticsData["average_temperature"] = int(totalTemperature / len(data))
init_data()

@app.route("/")
def home():
    refresh_data()
    refresh_statistics()
    return render_template("home.html", data=data[-1], statistics=statisticsData)


@app.route("/history")
def history():
    refresh_data()
    refresh_statistics()
    return render_template("history.html", data=json.dumps(structuredData, separators=(',', ':')), statistics=statisticsData)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
