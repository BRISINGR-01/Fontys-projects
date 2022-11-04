import csv, uuid, json
from flask_login import UserMixin
from utils import DATABASE_FILES, EMPLOYEES_EMAILS, SERVER_TO_ARDUINO_ROUTE, STATES, SMART_OVEN_URL, csvHelper, get_menu_data, DRINK_LIST
import requests

class User(UserMixin):
  def __init__(self, id, name, email, password, orderID = None):
    self.id = id
    self.name = name
    self.email = email
    self._password = password
    self._orderID = orderID

  def get_by(id = False, email = False, name = False):
    'Get a user from the database using one of the following: their id, email or name'
    
    with open(DATABASE_FILES.USERS, 'r') as file:
      for user in csv.DictReader(file):
        if (user['id'] == id or csvHelper.decode(user['email']) == email or csvHelper.decode(user['name']) == name):
          return User(user['id'], csvHelper.decode(user['name']), csvHelper.decode(user['email']), user['password'], user['orderID'])

  def create(email, password, name):
    'Generates id, creates a `User` instance and adds it to the database'
    
    id = uuid.uuid4()

    user = User(id, name, email, password)
    csvHelper.add(DATABASE_FILES.USERS, user.get_csv_values())

    return user

  def set_order_id(self, id):
    self._orderID = id
    csvHelper.edit(DATABASE_FILES.USERS, self.get_csv_values())

  def get_order_id(self): 
    return self._orderID

  def set_password(self, password):
    self._password = password
    csvHelper.edit(DATABASE_FILES.USERS, self.get_csv_values())

  def get_password(self): 
    return self._password

  def get_csv_values(self):
    'get values for putting into a csv database'

    return [self.id, csvHelper.encode(self.name), csvHelper.encode(self.email), self.password, self.orderID]
    # id and password are generated, not user inputed, so they don't need protection

  csvValues = property(get_csv_values)
  orderID = property(get_order_id, set_order_id)
  password = property(get_password, set_password)

  def delete(self):
    csvHelper.delete(DATABASE_FILES.USERS, self.id)

  def placeOrder(self, pizzas):
    order = Order.create(pizzas, self.id)
    self.orderID = order.id
    return order

  def get_current_order(self):
    order = Order.get_by_id(self.orderID)
    if (order): 
      return order.get_html_value()
    else:
      return None
  
  def get_previous_orders(self):
    orders = []
    with open(DATABASE_FILES.ORDERS, 'r') as ordersData:
      for row in csv.DictReader(ordersData):
        if row['userID'] == self.id and row['id'] != self.orderID: # active order shouldn't be included
          orders.append(Order(*row.values()).get_html_value())

    return orders[::-1] # reverse the list to show the orders chronologically
  
  def get_all():
    users = []
    with open(DATABASE_FILES.USERS, 'r') as file:
      for user in csv.DictReader(file):
        users.append({
          "name": csvHelper.decode(user["name"]), 
          "id": user["id"],
          "isAdmin": csvHelper.decode(user["email"]) in EMPLOYEES_EMAILS
        })
    
    return users


class Order():
  def __init__(self, id, content, userID, state = STATES.IS_NEXT):
    self.id = id

    self.content = content if isinstance(content, list) else json.loads(content)
    self.userID = userID
    self.state = state

  def get_by_id(id):
    'Get an order from the database using its id'
    orderData = csvHelper.get_by_id(DATABASE_FILES.ORDERS, id)
    if orderData:
      return Order(*orderData.values())
    else:
      return None

  def create(content, user = None):
    'Generates id, creates an `Order` instance and adds it to the database'

    id = uuid.uuid4()
    pizzaIDs = []
    for pizza, amount, price, jsonId in content:
      for _ in range(amount):
        pizzaIDs.append(Pizza.create(pizza, jsonId, id).id)

    if user:
      order = Order(id, pizzaIDs, user.id, STATES.IS_NEXT)
      user.orderID = order.id
    else:
      order = Order(id, pizzaIDs, None, STATES.IS_NEXT)
    csvHelper.add(DATABASE_FILES.ORDERS, order.get_csv_values())

    return order

  def cycle_state(self):
    'Cycle to the next state - is next, making or done'

    self.state = STATES.ORDER_STATES[STATES.ORDER_STATES.index(self.state) + 1]

    csvHelper.edit(DATABASE_FILES.ORDERS, self.get_csv_values())

  def get_total_price(self):
    # sum all the prices, multiply by 100, remove the decimal part, devide by 100 - this is to avoid this: https://0.30000000000000004.com/
    pizzas = [Pizza.get_by_id(pizzaID) for pizzaID in self.content]
    pizzaPrices = [pizza.price for pizza in pizzas]

    return int(sum(pizzaPrices) * 100) / 100

  def get_order_list(self):
    'Generate a list of the ordered items to display to the user' 

    def get_index(arr, item):
      if len(arr) == 0: return None

      for i in range(len(arr)):
        if item.name == arr[i]['name'] and item.state == arr[i]['state']:
            return i
    
    orderList = []

    for item in [Pizza.get_by_id(id) for id in self.content]:
      itemIndex = get_index(orderList, item)
      if itemIndex != None:
        orderList[itemIndex]['count'] += 1
      else:
        orderList.append({
          'name': item.name,
          'price': item.price,
          'count': 1,
          'image': item.imagePath,
          'state': item.state
        })

    return orderList

  def get_csv_values(self):
    'get values for putting into a csv database'

    return [self.id, json.dumps(self.content), self.userID]

  def get_html_value(self):
    'Returns the value to pass in the `render_template` function'

    return {'id': self.id, 'items': self.get_order_list(), 'total': self.get_total_price(), 'state': self.state}
  
class Pizza():
  def __init__(self, id, name, state, bakingTimeLeft, bakingTimeTotal, price, imagePath, jsonId, orderID = None):
    self.id = id
    self.name = name
    self.state = state
    self.price = float(price)
    self.bakingTimeLeft = bakingTimeLeft
    self.bakingTimeTotal = bakingTimeTotal
    self.jsonId = jsonId
    self.imagePath = imagePath
    self.orderID = orderID

  def get_by_id(id):
    'Get a pizza from the database using its id'
    data = csvHelper.get_by_id(DATABASE_FILES.PIZZAS, id)
    if data:
      return Pizza(*data.values())
    else:
      return None

  def create(name, jsonId,  orderID):
    'Generates id, creates a `Pizza` instance and adds it to the database'

    id = str(uuid.uuid4())
    data = get_menu_data(jsonId)
    pizza = Pizza(id, name, STATES.IS_NEXT, None, None, data['price'], data['imagePath'], jsonId, orderID)
    csvHelper.add(DATABASE_FILES.PIZZAS, pizza.get_csv_values())

    return pizza

  def cycle_state(self, refreshPage = None):
    'Cycle to the next state - `is next`, `making`, `baking` or `done`'

    self.state = STATES.PIZZA_STATES[STATES.PIZZA_STATES.index(self.state) + 1]
    csvHelper.edit(DATABASE_FILES.PIZZAS, self.get_csv_values())
    if refreshPage: refreshPage()

    if self.state == STATES.WAITING:
      # tell the smart oven that the pizza should start baking
      try:
        requests.post(SMART_OVEN_URL + SERVER_TO_ARDUINO_ROUTE, json={'pizzaID': self.id, 'pizzaName': self.name})
      except requests.ConnectionError:
        print('Couldn\'t connect to smart oven')
        
  def get_csv_values(self):
    'get values for putting into a csv database'

    return [self.id, self.name, self.state, self.bakingTimeLeft, self.bakingTimeTotal, self.price, self.imagePath, self.jsonId, self.orderID]

  def get_html_value(self):
    'Returns the value to pass in the `render_template` function'
    return {
      'id': str(self.id),
      'name': self.name,
      'state': self.state,
      'bakingTimeTotal': self.bakingTimeTotal,
      'bakingTimeLeft': self.bakingTimeLeft,
      'imagePath': self.imagePath
    }

  def set_val(self, bakingTimeLeft = None, bakingTimeTotal = None, price = None, imagePath = None):
    'Edits the `Pizza` instance and saves changes to the database'

    if bakingTimeLeft: self.bakingTimeLeft = bakingTimeLeft
    if bakingTimeTotal: self.bakingTimeTotal = bakingTimeTotal
    if price: self.price = price
    if imagePath: self.imagePath = imagePath

    csvHelper.edit(DATABASE_FILES.PIZZAS, self.get_csv_values())

  def get_all():
    p = []
    
    with open(DATABASE_FILES.PIZZAS, 'r') as pizzas:
      rows = list(csv.reader(pizzas))
      rows.pop(0)
      for row in rows:
        pizza = Pizza(*row)
        if pizza.jsonId not in DRINK_LIST:
          p.append(pizza.get_html_value())
    return p
