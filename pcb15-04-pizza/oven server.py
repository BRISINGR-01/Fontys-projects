url = 'http://145.93.149.161:5000/cycle-pizza-state'

import json
from flask import Flask
from flask import request, render_template
import time
from fhict_cb_01.CustomPymata4 import CustomPymata4
import requests

from utils import ARDUINO_TO_SERVER_ROUTE, MAIN_SERVER_URL, SERVER_TO_ARDUINO_ROUTE

#Setting up the web server
app = Flask(__name__)

#Board Variables
YELLOW_LED = 7
BLUE_LED = 6
GREEN_LED = 5
BUTTON1 = 9
BUTTON2 = 8
RED_LED = 4
POT_PIN = 0
MAX_ANGLE = 15

#Variables
pizzaId = ''
requestCounter = 0
startOven = 0
ovenState = -1 #ovenstate -1 means its turned fully off
removePizza = 0 
angle = 0
pizzaBakingTime = 0
queue = []
com = 'COM6'

#Functions
def setup(): #This function starts the board
    global board
    board = CustomPymata4(com_port = com)
    board.displayOn()
    board.set_pin_mode_digital_input_pullup(BUTTON1, callback = Left_Button_Changed)
    board.set_pin_mode_digital_input_pullup(BUTTON2, callback = Right_Button_Changed)
    board.set_pin_mode_analog_input(POT_PIN, callback=Reading_Potentiometer, differential=10)

def Left_Button_Changed(data): #Checks if the left button is pressed. However it will only do something when the oven is in the state of 'open'
    global startOven, ovenState
    if data[2] == 0 and ovenState == 0 and len(queue) != 0:
        startOven = 1
        print('LB pressed, oven is started')

def Right_Button_Changed(data):#Checks if the right button is pressed. However it will only do something when the is in the state of 'done'
    global removePizza, ovenState
    if data[2] == 0 and ovenState == 2:
        removePizza = 1
        print('RB pressed, pizza removed')

def Reading_Potentiometer(data):#Checks if the potentiometer is changed. Will be used to set the timer
    global angle
    sensor_value = data[2]
    angle = sensor_value * MAX_ANGLE/1023.0
    angle = round(angle)

def oven_open():#Turns the yellow led on, the red and green led are turned off 
    board.digital_write(YELLOW_LED, 1)
    board.digital_write(RED_LED, 0)
    board.digital_write(GREEN_LED, 0)

def oven_baking():#Turns the red led on, the yellow and green led are turned off
    board.digital_write(YELLOW_LED, 0)
    board.digital_write(RED_LED, 1)
    board.digital_write(GREEN_LED, 0)

def oven_done():#Turns the green led on, the yellow and red led are turned off
    board.digital_write(YELLOW_LED, 0)
    board.digital_write(RED_LED, 0)
    board.digital_write(GREEN_LED, 1)

def set_timer():#Sets the timer in minutes using the potentiometer
    global angle, pizzaBakingTime
    minutes = str(angle)
    displaySetTimerList = ['0','0','.','0','0']
    if len(str(minutes)) == 1:
        displaySetTimerList[0] = '0'
        displaySetTimerList[1] = minutes[0]
    else: 
        displaySetTimerList[0] = minutes[0]
        displaySetTimerList[1] = minutes[1]
    
    displaySetTimer = ''.join(displaySetTimerList)
    board.displayShow(displaySetTimer)
    pizzaBakingTime = angle * 60
    
def start_oven():#Starts the timer. Sets the oven state to 'baking'
    global countdownEnd, ovenState, startOven, pizzaBakingTime
    pizzaBakingTime = 15
    countdownEnd = time.time() + pizzaBakingTime
    requests.post(MAIN_SERVER_URL + '/cycle-pizza-state', json = {'pizzaID' : queue[0]})
    ovenState = 1
    print('Now baking!')
    startOven = 0

def countdown():#Uses the the time library the calculate the differences between the current time and the set time. 
    #The differnce is formatted into a string that is displayable on the boarddisplay
    global countdownEnd, ovenState, displayTimer, requestCounter, queue
    countdown = time.time()
    if time.ctime(countdownEnd) <= time.ctime(countdown):
        board.displayShow('00.00')
        done = {'pizzaID' : queue[0], 'bakingTime' : '00.00'}
        requests.post(MAIN_SERVER_URL + ARDUINO_TO_SERVER_ROUTE, json = done)
        ovenState = 2
    else:
        displayTimerList = list(time.ctime(countdownEnd-countdown))
        displayTimerList[16]= '.'
        displayTimer = ''.join(displayTimerList[14:19])
        board.displayShow(displayTimer)
        requestCounter += 1

def upload_timer():#Posts the timer to the website 
    global displayTimer, requestCounter, queue
    if requestCounter == 4:
        timer = {'pizzaID' : queue[0], 'bakingTime' : displayTimer}
        requests.post(MAIN_SERVER_URL + ARDUINO_TO_SERVER_ROUTE, json = timer)
        print(timer)
        requestCounter = 0

def remove_pizza():#Sets the oven back to the 'open state'
    global ovenState, removePizza
    ovenState = 0
    print('Pizza removed')
    requests.post(MAIN_SERVER_URL + '/cycle-pizza-state', json = {'pizzaID' : queue[0]})
    removePizza = 0
    queue.pop(0)
    print(queue)

#Main loop
def loop():
    while True:
        time.sleep(0.2)#200ms for the arduino to proccess the actions requested
        if ovenState == 0: #open
            oven_open()
            set_timer()
            if startOven == 1:
                start_oven()
        if ovenState == 1: #baking
            oven_baking()
            countdown()
            upload_timer()
        if ovenState == 2: #done
            oven_done()
            if removePizza == 1:
                remove_pizza()

#Web server routes
@app.route('/')
def index():

    return render_template('arduino.html')

@app.route('/start')
def start():
    global ovenState
    ovenState = 0
    loop()

@app.route(SERVER_TO_ARDUINO_ROUTE, methods = ['POST'])
def upload_ids():
    global pizzaId, queue
    data = request.get_json()
    print(data)
    pizzaId = data['pizzaID']
    pizzaName = data['pizzaName']

    queue.append(pizzaId)
    print(queue)

    return 'OK', 200

#Setup
setup()
app.run(host='0.0.0.0')