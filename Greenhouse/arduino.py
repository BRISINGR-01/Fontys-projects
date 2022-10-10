import datetime, sys, requests, time
from fhict_cb_01.CustomPymata4 import CustomPymata4

DHTPIN = 12
LDRPIN = 2

ID="Arduino"

humidity_measurement = None
temperature_measurement = None
light_measurement = None

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
  if (sys.argv[1] != None):
    board = CustomPymata4(com_port="COM" + sys.argv[1])
  else:
    board = CustomPymata4(com_port="COM4")
    board.set_pin_mode_dht(DHTPIN, sensor_type=11,
                           differential=.05, callback=measure_DHT)
    board.set_pin_mode_analog_input(
        LDRPIN, callback=measure_LDR, differential=10)
except:
    print("The arduino is not connected")

url = "http://localhost:5000"

def get_structured_data():
  def current_time():
    def format(num):
        if (num < 10):
            return "0" + str(num)
        else:
            return num

    now = datetime.datetime.now()

    return f"{format(now.hour)}:{format(now.minute)}:{format(now.second)}"

  today = datetime.datetime.now().strftime("%A")
  week_num = datetime.datetime.now().isocalendar()[1]
  time_stamp = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S") 

  return [ID, week_num, today, current_time(), temperature_measurement, humidity_measurement, light_measurement]

while True:
  time.sleep(5)
  try:
    response = requests.post(url + "/post_data", json=get_structured_data())
    print(response)
  except requests.ConnectionError:
    print("Couldn't connect to " + url)
    