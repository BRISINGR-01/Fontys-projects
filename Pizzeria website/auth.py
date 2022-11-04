from flask import Blueprint, flash, redirect, request, url_for, render_template
from flask_login import login_user, logout_user, login_required, current_user
from cryptography.fernet import Fernet
from dev import EMAIL_PASSWORD, EMAIL_SENDER, ENCRYPTION_KEY
from models import User
import smtplib, datetime

from utils import EMPLOYEES_EMAILS

auth = Blueprint('auth', __name__)

fernet = Fernet(ENCRYPTION_KEY)

@auth.route('/login')
def login():
  return render_template('authentication/login.html')

@auth.route('/login', methods=['POST'])
def login_post():
  # get data from the form fields in the html
  email = request.form.get('email')
  password = request.form.get('password')
  remember = True if request.form.get('remember') else False
  next = request.form.get('next')

  # fetch user from db
  user = User.get_by(email=email)

  if not user:
    flash('The provided email is not registered.', 'error')
    return redirect(url_for('auth.login'))
  elif fernet.decrypt(user.password).decode() != password:
    flash('Incorrect password.', 'error')
    return redirect(url_for('auth.login'))
  else:
    login_user(user, remember=remember)
    # if the user tries to access a page which requires login
    # then they will be redirected to the login page
    # once they login they should return to the page they initially wanted to visit 
    # the url of said page is kept in a hidden field in the login form
    if (next != ''): return redirect(next)
    else: return redirect(url_for('profile'))

@auth.route('/sign-up')
def sign_up():
  return render_template('authentication/signup.html')

@auth.route('/sign-up', methods=['POST'])
def sign_up_post():
  email = request.form.get('email')
  name = request.form.get('name')
  password = request.form.get('password')
  remember = request.form.get('remember')
  next = request.form.get('next')

  user = User.get_by(email=email)

  if user:
    flash('Email address already exists', 'error')
    return redirect(url_for('auth.login'))
  else:
    user = User.create(email=email, name=name, password=fernet.encrypt(password.encode()).decode())
    login_user(user, remember=remember)
    if (next != ''): return redirect(next)
    else: return redirect(url_for('profile'))

@auth.route('/change-password', methods = ['GET', 'POST'])
@login_required
def change_password():
  isAuthenticated = current_user.email in EMPLOYEES_EMAILS
  if request.method == 'GET':
    return render_template('authentication/profile.html', change_password=True, name=current_user.name, isAuthenticated=isAuthenticated, currentOrder=current_user.get_current_order(), previousOrders=current_user.get_previous_orders())
  else:
    prev_password = request.form['previous_password']
    new_password = request.form['new_password']
    if prev_password != fernet.decrypt(current_user.password).decode():
      flash('Wrong password!')
      return render_template('authentication/profile.html', change_password=True, name=current_user.name, isAuthenticated=isAuthenticated, currentOrder=current_user.get_current_order(), previousOrders=current_user.get_previous_orders())
    elif prev_password == new_password:
      flash('New password cannot be the old password!')
      return render_template('authentication/profile.html', change_password=True, name=current_user.name, isAuthenticated=isAuthenticated, currentOrder=current_user.get_current_order(), previousOrders=current_user.get_previous_orders())

    current_user.password = fernet.encrypt(new_password.encode()).decode()
    email_text = f"""
    From: {EMAIL_SENDER}
    To: {current_user.email}
    Subject: Forgotten password - Pizzeria

    Hey {current_user.name},
    Your password was changed successfully at {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} :)
    Best regards,
    Pizzeria 15-4
    """

    try:
      server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
      server.ehlo()
      server.login(EMAIL_SENDER, EMAIL_PASSWORD)
      server.sendmail(EMAIL_SENDER, current_user.email, email_text)
      server.close()
    except:
      flash('A problem occured while sending the email!')
    flash('Password changed!')
    return redirect(url_for('profile'))

@auth.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('index'))

@auth.route('/delete-account')
@login_required
def delete_account():
  current_user.delete()
  return redirect(url_for('index'))


@auth.route('/forgot-password', methods=['POST', 'GET'])
def forgot_password():
  if request.method == 'GET' and not current_user:
    return render_template('authentication/forgotPassword.html')

  if current_user.is_active:
    user = current_user
  else:
    if 'email' not in request.form:
      return render_template('authentication/forgot-password.html')

    email = request.form['email']
    if email == '': 
      flash('Please enter an email', 'error')
      return redirect(url_for('auth.forgot_password'))

    user = User.get_by(email=email)
    if user == None:
      flash('The email is not registered', 'not_registered')
      return redirect(url_for('auth.forgot_password'))


  email_text = f"""
  From: {EMAIL_SENDER}
  To: {user.email}
  Subject: Forgotten password - Pizzeria

  Hey {user.name},
  Here is your password :)
  {fernet.decrypt(user.password).decode()}
  Best regards,
  Pizzeria 15-4
  """

  try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_SENDER, user.email, email_text)
    server.close()
    flash('Password sent by email')
  except:
    flash('An error occured', 'error')
    
  if current_user:
    return redirect(url_for('profile'))
  else:
    return redirect(url_for('auth.forgot_password'))