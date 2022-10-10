import csv
import json
import os
import random

MAX_DIFF = {
    "temperature": 1,
    "humidity": 5,
    "light": 30
}

MAX_UP = {
    "temperature": 30,
    "humidity": 85,
    "light": 1000
}

MAX_DOWN = {
    "temperature": 13,
    "humidity": 65,
    "light": 600
}


def create_curve(type):
    def getCons():
        return random.randint(0, 10)

    up = MAX_UP[type]
    down = MAX_DOWN[type]

    points = []
    consequitive = getCons()
    direction = random.getrandbits(1)  # True for up, False for down

    for _ in range(0, 24):
        if (len(points) == 0):
            points.append(random.randint(down, up))
        else:
            difference = random.randint(0, MAX_DIFF[type])

            if (not direction):
                difference *= -1

            newValue = difference + points[-1]

            if (newValue > up):
                points.append(up)
                direction = False
                consequitive = getCons()
            elif (newValue < down):
                points.append(down)
                direction = True
                consequitive = getCons()
            else:
                points.append(newValue)
                if (consequitive == 0):
                    direction = not direction
                    consequitive = getCons()
                else:
                    consequitive -= 1

    return points

def create_data():
    data = []

    SENSOR_IDS = ["q3bPOMgDza", "Anw2bNFVHb", "rtPGM4n80v", "fFPR9fxgIf", "seZDwgOPZH",
                "d1ftuVwNyY", "sjLDuO4Lx4", "mFEYsuCfXe", "HyrOWwWXn5", "UeAEMUlYOu"]


    def format(num):
        if (num < 10):
            return "0" + str(num)
        else:
            return num


    for sensor in SENSOR_IDS:
        for week in [1, 2, 3, 4]:
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                temperature = create_curve("temperature")
                humidity = create_curve("humidity")
                light = create_curve("light")
                for hour in list(range(0, 24)):
                    data.append([
                        sensor,
                        week,
                        day,
                        f"{format(hour)}:{format(random.randint(0, 5))}:{format(random.randint(0, 59))}",
                        format(temperature[hour]),
                        humidity[hour],
                        light[hour],
                    ])

    with open('data.csv', 'w', newline="") as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["sensor_id", "week", "day", "time", "temperature", "humidity", "light"])
        writer.writerows(data)

    return data

def create_statistics():
    if (not os.path.exists("./data.csv")): create_data()

    with open('data.csv', 'r') as csvData:
        data = list(csv.reader(csvData))
        data.pop(0)

        

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

        statisticsData["highest_temperature"] = max(
            statisticsData["highest_temperature"], int(value[4]))
        statisticsData["highest_humidity"] = max(
            statisticsData["highest_humidity"], int(value[5]))
        statisticsData["highest_light"] = max(
            statisticsData["highest_light"], int(value[6]))

        statisticsData["lowest_temperature"] = min(
            statisticsData["lowest_temperature"], int(value[4]))
        statisticsData["lowest_humidity"] = min(
            statisticsData["lowest_humidity"], int(value[5]))
        statisticsData["lowest_light"] = min(
            statisticsData["lowest_light"], int(value[6]))

        statisticsData["average_light"] = int(totalLight / len(data))
        statisticsData["average_humidity"] = int(totalHumidity / len(data))
        statisticsData["average_temperature"] = int(
            totalTemperature / len(data))

    with open('statistics.json', 'w') as stats_file:
        json.dump(statisticsData, stats_file)