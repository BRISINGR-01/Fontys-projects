import csv
import random
import numpy as np

MAX_DIFF = {
    "temperature": 3,
    "humidity": 10,
    "light": 50
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
        return random.randint(0, 5)

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
                    day,
                    week,
                    f"{format(hour)}:{format(random.randint(0, 5))}:{format(random.randint(0, 59))}",
                    format(temperature[hour]),
                    humidity[hour],
                    light[hour],
                ])

with open('data.csv', 'w', newline="") as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow(["sensor_id", "day", "week", "time", "temperature", "humidity", "light"])
    writer.writerows(data)
