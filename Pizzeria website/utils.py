import csv, json, re, os
from flask import render_template, redirect, url_for, flash


# constants
PIZZAS_MENU = 'pizzas.json'
EMPLOYEES_EMAILS = ['luigi@gmail.it', 'mario@gmail.it']
SERVER_TO_ARDUINO_ROUTE = '/upload_ids'
ARDUINO_TO_SERVER_ROUTE = '/update-pizza-time'
SMART_OVEN_URL = 'http://145.93.88.152:5000'
MAIN_SERVER_URL = 'http://localhost:5000'
DRINK_LIST = ['7','8','9','10']

orderList = []
listDisplay = []
idList = []
amountList = []
priceList = []
totalPrice = 0

# data scheme for the databases
class DATA_ORDER:
  USERS = ['id', 'name', 'email', 'password', 'orderID']
  ORDERS = ['id', 'content', 'userID', 'state']
  PIZZAS = ['id', 'name', 'state', 'bakingTimeLeft', 'bakingTimeTotal', 'price', 'imagePath', 'jsonId', 'orderID']

class DATABASE_FILES:
  USERS = 'users.csv'
  ORDERS = 'orders.csv'
  PIZZAS = 'pizzas.csv'

  # ensure that all database files exist and are correct
  def __init__(self):
    for name in ['USERS', 'ORDERS', 'PIZZAS']:
      if (not os.path.exists(getattr(self, name))):
        with open(getattr(self, name), 'w', newline='') as userData:
          writer = csv.writer(userData, delimiter=',', quoting=csv.QUOTE_ALL)
          writer.writerow(getattr(DATA_ORDER, name))
          if name == 'USERS':
            writer.writerow(["770f8f11-f61b-4f36-a045-44738e073e49","'Luigi","'luigi@gmail.it","gAAAAABjUtLUb3kj3oF6I2SgVgYycLfiLVfeQDxQF7TymOmN6NUa-oUJ6hrS9KBFQACti7_XSOF_THDulX8C_0BzsELBJze5Uw==",""])
            writer.writerow(["88cea9e2-a5d1-4e87-8e03-08e4414c3546","'Mario","'mario@gmail.it","gAAAAABjUtLmY4QSiDL0tZiPyfSi--J_yIstqmjmB_L6j7Yp14dUePGABLQDZm7P8UQMLOVvwvvhbKkRJUOVSi5IOp2LPlEvYQ==",""])

class STATES:
  IS_NEXT = 'is next'
  MAKING = 'making'
  WAITING = 'waiting'
  BAKING = 'baking'
  DONE = 'done'

  PIZZA_STATES = [IS_NEXT, MAKING, WAITING, BAKING, DONE]
  ORDER_STATES = [IS_NEXT, MAKING, DONE]

def get_menu_data(id = None):
  with open(PIZZAS_MENU) as jsonData:
    if id == None:
      return json.load(jsonData)
    else:
      return json.load(jsonData)[id]


def employee_login(user, file, **kwargs):
  '''
  this function is for routes which are reserved only for employees, such as the mario ordering page, luigi's cooking page...
  
  the `**kwargs` is for passing arguments
  ex: `render_template('file.html',order='Peperoni', temperature=23)`
  '''
  if (user.email in EMPLOYEES_EMAILS): return render_template(file, **kwargs)
  else: 
    flash('Incorrect credentials. Page reserved for employees')
    return redirect(url_for('auth.login'))

class csvHelper:
  def encode(value):
    'protect against values starting with =, -, +'
    return f'\'{value}'

  def decode(value):
    'decypher protected data'
    return re.sub('^\'', '', value)

  def get_by_id(csvFile, id):
    with open(csvFile, 'r') as ordersData:
        for row in csv.DictReader(ordersData):
          if (row['id'] == id): return row

  def add(csvFile, data):
    'Adds a new row to the database'

    with open(csvFile, 'a', newline='') as dataFile:
        writer = csv.writer(dataFile, delimiter=',', quoting=csv.QUOTE_ALL) # quoting escapes commas and quotation marks
        writer.writerow(data)

  def edit(csvFile, editedRow):
    'Edits the database. Second parameter should be the changed row'

    with open(csvFile, 'r') as fileToRead:
      rows = [row if row[0] != editedRow[0] else editedRow for row in csv.reader(fileToRead)]
      with open(csvFile, 'w', newline='') as fileToWrite:
        writer = csv.writer(fileToWrite, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)

  def delete(csvFile, rowID):
    'Deletes from a database by id'
    
    with open(csvFile, 'r') as fileToRead:
      data = [row for row in csv.reader(fileToRead) if row[0] != rowID]
      with open(csvFile, 'w', newline='') as fileToWrite:
        writer = csv.writer(fileToWrite, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerows(data)

def add_to_order(id, amount):
  global orderList, listDisplay, idList, amountList, priceList, totalPrice
  pizza = get_menu_data(id)['name']
  price = get_menu_data(id)['price']
  #Checks if the amount is there and is a int. If not it will be 1 
  if amount == "" or amount.isnumeric() == False:
    amount = 1
  else:
    amount = int(amount)

  if pizza in idList:
    index = idList.index(pizza)
    amountList[index] = int(amountList[index]) + amount
    priceList[index] = price * amountList[index]
    combined = (idList[index],amountList[index], priceList[index], id)
    listDisplay[index] = (combined)
  else:
    idList.append(pizza)
    amountList.append(amount)
    priceList.append(price * amountList[-1])
    combined = (idList[-1], amountList[-1], priceList[-1], id)
    listDisplay.append(combined)
  
  if len(priceList) == 0:
    totalPrice = 0
  else:
    totalPrice = 0
    priceIndex = 0
    while priceIndex < len(priceList):
      totalPrice = totalPrice + priceList[int(priceIndex)]
      priceIndex += 1

    orderList = listDisplay

  return orderList, listDisplay, idList, amountList, priceList, totalPrice

def get_json_length():
    with open(PIZZAS_MENU) as jsonData:
      length = len(json.load(jsonData))
      return length

def fill_template():
  menu_list = []
  index = 1
  while index <= get_json_length():
    name = get_menu_data(str(index))['name']
    price = get_menu_data(str(index))['price']
    imagePath = get_menu_data(str(index))['imagePath']
    combined = (index ,name, price, imagePath)
    menu_list.append(combined)
    index +=1 
  return menu_list