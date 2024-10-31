import os
from flask import Flask, flash, render_template, redirect, request, session
from flask_app import model
import datetime
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import BooleanField, StringField, SelectField, PasswordField, DateField, TimeField, IntegerField, EmailField, validators
from flask_session import Session
from functools import wraps
from flask_talisman import Talisman
import pyotp
from flask_qrcode import QRcode

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Talisman(app, content_security_policy={
    'default-src' : '\'none\'',
    'style-src': [ 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css' ],
    'img-src' : ['\'self\'', 'data:'],
    'script-src' : '\'none\''
  })
CSRFProtect(app)
Session(app)
QRcode(app)


def login_required(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    if not 'user' in session:
      return redirect('/login')
    return func(*args, **kwargs)
  return wrapper


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


class LoginForm(FlaskForm):
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])

class signinForm(FlaskForm):
  name = StringField('name', validators=[validators.DataRequired()])
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])
  password_confirm = PasswordField('password_confirm', validators=[validators.DataRequired()])


@app.route('/login', methods=['GET', 'POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    try:
      connection = model.connect()
      user = model.get_user(connection, form.email.data, form.password.data)
      if model.totp_enabled(connection, user):
        session['totp_user'] = user
        return redirect('/totp')
      session['user'] = user
      return redirect('/')
    except Exception as exception:
      app.log_exception(exception)
  return render_template('login.html', form=form)


@app.route('/logout', methods = ['POST'])
@login_required
def logout():
  session.pop('user')
  flash('Déconnexion réussie !')
  return redirect('/')


class PasswordChangeForm(FlaskForm):
  old_password = PasswordField('old_password', validators=[validators.DataRequired()])
  new_password = PasswordField('new_password', validators=[validators.DataRequired(), 
                                                           validators.EqualTo('password_confirm')])
  password_confirm = PasswordField('password_confirm', validators=[validators.DataRequired()])
  totp_enabled = BooleanField('totp_enabled')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
  form = PasswordChangeForm()
  if form.validate_on_submit():
    try:
      connection = model.connect()
      email = session['user']['email']
      model.change_password(connection, email, form.old_password.data, form.new_password.data)
      totp_secret = session['totp_secret'] if form.totp_enabled.data else None
      model.update_totp_secret(connection, session['user']['id'], totp_secret)
      flash('Mot de passe modifié !')
      return redirect('/')
    except Exception as exception:
      app.log_exception(exception)
  totp_secret = pyotp.random_base32()
  session['totp_secret'] = totp_secret
  totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
    name=session['user']['email'], issuer_name='Soccer')
  return render_template('change_password.html', form=form, totp_uri=totp_uri)


class UserCreationForm(FlaskForm):
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired(), 
                                                   validators.EqualTo('confirm')])
  confirm = PasswordField('confirm', validators=[validators.DataRequired()])


@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
  form = UserCreationForm()
  if form.validate_on_submit():
    try:
      connection = model.connect()
      model.add_user(connection, form.email.data, form.password.data)
      flash('Nouvel utilisateur créé !')
      return redirect('/')
    except Exception as exception:
      app.log_exception(exception)
  return render_template('create_user.html', form=form)


class TotpForm(FlaskForm):
  totp = StringField('totp', validators=[
     validators.DataRequired(), 
     validators.Length(min=6, max=6)])


@app.route('/totp', methods=['GET', 'POST'])
def totp():
  if 'totp_user' not in session:
    return redirect('/')
  user = session['totp_user']
  connection = model.connect()
  if not model.totp_enabled(connection, user):
    return redirect('/')
  form = TotpForm()
  if form.validate_on_submit():
    try:
      totp_secret = model.totp_secret(connection, user)
      totp_code = form.totp.data
      if pyotp.TOTP(totp_secret).verify(totp_code):
        session['user'] = user
        return redirect('/')
    except Exception as exception:
      app.log_exception(exception)
  return render_template('totp.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
  form = signinForm()
  if form.validate_on_submit():
    try:
      connection = model.connect()
      if model.compare_password(form.password.data, form.password_confirm.data) :
        user = model.add_user(connection, form.name.data ,form.email.data, form.password.data)
        return redirect('/login')
    except Exception as exception:
      app.log_exception(exception)
  return render_template('sign_in.html', form=form)