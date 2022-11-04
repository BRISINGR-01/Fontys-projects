import json
import os, urllib

from flask_socketio import SocketIO
from flask import Flask, render_template, send_from_directory, request, redirect, url_for
from flask_login import LoginManager, login_required, current_user

from utils import DATABASE_FILES, PIZZAS_MENU, EMPLOYEES_EMAILS, employee_login, get_menu_data, add_to_order, fill_template
from auth import auth as auth_blueprint
from dev import SECRET_KEY
from models import Order, Pizza, User

app = Flask(__name__)

orderList = []
listDisplay = []
idList = []
amountList = []
priceList = []
totalPrice = 0
timer = '00.00'

app.secret_key = SECRET_KEY
app.register_blueprint(auth_blueprint)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login' # when a user tries to enter a url which requires an account, they will be redirected here
login_manager.init_app(app)

# ensure there are database files 
DATABASE_FILES()

def refreshPages():
  socketio.emit('reload')

@login_manager.user_loader
def load_user(id):
  return User.get_by(id=id)

@app.route('/')
def index():
  return render_template('home.html')

@app.route('/profile')
@login_required
def profile():
  isAuthenticated = current_user.email in EMPLOYEES_EMAILS
  return render_template('authentication/profile.html', name=current_user.name, isAuthenticated=isAuthenticated, currentOrder=current_user.get_current_order(), previousOrders=current_user.get_previous_orders())

@app.route('/chef-space')
@login_required
def chef_space():
  return employee_login(current_user, 'chef-space.html', items=Pizza.get_all())

@app.route('/cycle-pizza-state', methods=['POST'])
def cycle_pizza_state():
  data = request.get_json()
  pizza = Pizza.get_by_id(data['pizzaID'])
  if not pizza: return 'Bad Request', 400

  if ('bakingTime' in data  and data['bakingTime'] != None):
    pizza.set_val(bakingTimeTotal=data['bakingTime'])
    pizza.set_val(bakingTimeLeft=data['bakingTime'])

  pizza.cycle_state(refreshPages) # this should be at the end, so that it doesn't block the rest of the function (it waits for response from the arduino)
  return 'OK', 200

@app.route('/update-pizza-time', methods=['POST'])
def update_time():
  global timer
  data = request.get_json()
  pizza = Pizza.get_by_id(data['pizzaID'])
  if not pizza: return 'Bad Request', 400

  data["totalTime"] = pizza.bakingTimeTotal

  pizza.set_val(bakingTimeLeft=data['bakingTime'])
  timer = data['bakingTime']
  socketio.emit('update-time', data)
  return 'OK', 200

@app.route('/cycle-pizza-state-by-luigi', methods=['POST'])
def cycle_pizza_state_luigi():
  pizzaID = request.get_data().decode()
  pizza = Pizza.get_by_id(pizzaID)

  pizza.cycle_state(refreshPages) # this should be at the end, so that it doesn't block the rest of the function (it waits for response from the arduino)
  return redirect(url_for('chef_space'))

@app.route('/cashier')
@login_required
def cashier():
  global timer
  return employee_login(current_user, 'cashier.html', data = listDisplay, Oven = timer, total_price = totalPrice, menu = fill_template())

@app.route('/add_cashier', methods=['POST'])
def add_cashier():
  global orderList, listDisplay, idList, amountList, priceList, totalPrice
  id = request.form['add']
  amount = request.form['amt']
  orderList, listDisplay, idList, amountList, priceList, totalPrice = add_to_order(id, amount)

  return redirect(url_for('cashier'))

@app.route('/order', methods=['POST'])
@login_required
def send_order():
  global totalPrice, orderList
  order = Order.create(orderList, current_user)
  current_user.orderID = order.id
  idList.clear()
  amountList.clear()
  priceList.clear()
  orderList.clear()
  listDisplay.clear()
  totalPrice = 0
  refreshPages()
  return redirect(url_for('cashier'))

@app.route('/customer_page')
@login_required
def menu():

  return render_template('customer_page.html', data = listDisplay, total_price = totalPrice, menu = fill_template())

@app.route('/add_customer', methods = ['POST'])
def add_customer():
  global orderList, listDisplay, idList, amountList, priceList, totalPrice
  id = request.form['add']
  amount = '1'
  orderList, listDisplay, idList, amountList, priceList, totalPrice = add_to_order(id, amount)

  return redirect(url_for('menu'))

@app.route('/tracker_page', methods=['POST', 'GET'])
@login_required
def tracker():
  if request.method == 'POST':
    global totalPrice, orderList
    Order.create(orderList, current_user)
    idList.clear()
    amountList.clear()
    priceList.clear()
    orderList.clear()
    listDisplay.clear()
    totalPrice = 0
    refreshPages()
 
  return redirect(url_for('profile'))

@app.route('/payment_page')
@login_required
def payment():
  return render_template('payment_page.html', data = listDisplay, total_price = totalPrice)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
  if request.method == "GET":
    return employee_login(current_user, "admin.html", admins=EMPLOYEES_EMAILS, users=User.get_all())

  name = request.form.get("name")
  price = request.form.get("price")
  image_url = request.form.get("image")
  items = get_menu_data()
  index = len(items) + 1
  image_path = os.path.basename(urllib.parse.urlparse(image_url).path)


  try:
    urllib.request.urlretrieve(image_url, os.path.join("static", "svgs", image_path)) # download and save image
  except:
    image_path = "no image.png"
    print("image not retrieved")

  items[index] = {
    "name": name,
    "price": price,
    "imagePath": image_path
  }

  with open(PIZZAS_MENU, "w") as menu:
    menu.write(json.dumps(items))
    menu.close()

  refreshPages()
  return redirect(url_for("admin"))

@app.route('/delete-account/<id>')
@login_required
def delete(id):
  User.get_by(id=id).delete()
  return redirect(url_for("admin"))

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'logo.ico', mimetype='image/vnd.microsoft.icon')

app.debug = True
# app.run(host='0.0.0.0')

if __name__ == '__main__':
  socketio.run(app, host='0.0.0.0')
