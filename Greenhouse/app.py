import json, os, csv
from fhict_cb_01.CustomPymata4 import CustomPymata4
from flask import Flask, request, render_template, send_from_directory

from create_data import create_data, create_statistics

if (not os.path.exists("./data.csv")):
    create_data()
if (not os.path.exists("./statistics.json")):
    create_statistics()

with open('data.csv', 'r') as csvData:
    data = list(csv.reader(csvData))
    data.pop(0)


SENSOR_IDS = ["Alex's Arduino", "q3bPOMgDza", "Anw2bNFVHb", "rtPGM4n80v", "fFPR9fxgIf", "seZDwgOPZH",
              "d1ftuVwNyY", "sjLDuO4Lx4", "mFEYsuCfXe", "HyrOWwWXn5", "UeAEMUlYOu"]
WEEKS = [1, 2, 3, 4]

structuredData = {}
statisticsData = {}

def refresh_statistics(newData):
    global statisticsData

    statisticsData["highest_temperature"] = max(
        statisticsData["highest_temperature"], newData[4])
    statisticsData["highest_humidity"] = max(
        statisticsData["highest_humidity"], newData[5])
    statisticsData["highest_light"] = max(
        statisticsData["highest_light"], newData[6])

    statisticsData["lowest_temperature"] = min(
        statisticsData["lowest_temperature"], newData[4])
    statisticsData["lowest_humidity"] = min(
        statisticsData["lowest_humidity"], newData[5])
    statisticsData["lowest_light"] = min(
        statisticsData["lowest_light"], newData[6])

    dataLength = len(data)
    statisticsData["average_light"] = round(
        ((dataLength - 1) * statisticsData["average_light"] + newData[4]) / dataLength)
    statisticsData["average_humidity"] = round(
        ((dataLength - 1) * statisticsData["average_humidity"] + newData[5]) / dataLength)
    statisticsData["average_temperature"] = round(
        ((dataLength - 1) * statisticsData["average_temperature"] + newData[6]) / dataLength)

    with open('statistics.json', 'w') as stats_file:
        json.dump(statisticsData, stats_file)

def init_data():
    global statisticsData, structuredData

    for sensor in SENSOR_IDS:
        structuredData[sensor] = {}

        for week in WEEKS:
            structuredData[sensor][week] = {}

            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                structuredData[sensor][week][day] = []

    for (sensor_id, week, day, time, temperature, humidity, light) in data:
        week = int(week)
        if (sensor_id not in structuredData): add_sensor(sensor_id)
        if (week not in structuredData[sensor_id]):
            WEEKS.append(week)
            for sensor in SENSOR_IDS:
                structuredData[sensor][week] = {}

                for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                    structuredData[sensor][week][day] = []

        structuredData[sensor_id][week][day].append([sensor_id, week, day, time, temperature, humidity, light])

    with open("statistics.json", "r") as raw_stats:
        statisticsData = json.load(raw_stats)

def add_sensor(sensor_id):
    structuredData[sensor_id] = {}

    for week in WEEKS:
        structuredData[sensor_id][week] = {}

        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            structuredData[sensor_id][week][day] = []

def add_data(newData):
    sensor = newData[0]
    if (sensor not in SENSOR_IDS): add_sensor(sensor)

    structuredData[sensor][newData[1]][newData[2]] = newData[2:]
    with open('data.csv', 'a', newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(newData)

init_data()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html", data=data[-1], statistics=statisticsData)


@app.route("/history")
def history():
    return render_template("history.html", data=json.dumps(structuredData, separators=(',', ':')), statistics=statisticsData)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/post_data", methods=['POST'])
def receive_data():
    json_data = request.get_json()
    add_data(json_data)
    refresh_statistics(json_data)
    return "OK", 200


@app.route("/get_data")
def send_data():
    return json.dumps(structuredData, separators=(',', ':'))
