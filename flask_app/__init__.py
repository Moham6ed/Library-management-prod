import os
from flask import Flask, flash, render_template, redirect, request, session
from flask_app import model
import datetime
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import BooleanField, StringField, SelectField, PasswordField, DateField, TimeField, IntegerField, EmailField, validators, FileField
from flask_session import Session
from functools import wraps
from flask_talisman import Talisman
import pyotp
from flask_qrcode import QRcode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
# Talisman activé avec HTTPS désactivé (force_https=False)
Talisman(app, 
    force_https=False,  # Désactive la redirection HTTPS forcée
    content_security_policy={
        'default-src' : '\'none\'',
        'style-src': [ 'https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css' ],
        'img-src' : ['\'self\'', 'data:'],
        'script-src' : '\'none\''
    })
CSRFProtect(app)
Session(app)
QRcode(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.context_processor
def inject_():
    return {'book_search_form': BookSearchForm()}

def login_required(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    if not 'user' in session:
      return redirect('/login')
    return func(*args, **kwargs)
  return wrapper


@app.route('/', methods=['GET'])
def home():
    connection = model.connect()
    lists_of_books = model.get_lists(connection)
    for book in lists_of_books:
      print(book)
    return render_template('home.html',lists_of_books=lists_of_books)

@app.route('/show_books/<int:id_list_books>', methods=['GET'])
def show_books(id_list_books):
  try :  
    connection = model.connect()
    
    books = model.get_books_in_list(connection, id_list_books)
   
    return render_template('books.html', books=books)
  except Exception as e:
    flash('Liste est vide !')
    return redirect('/')

@app.route('/show_book/<int:id_book>', methods=['GET'])
def show_book(id_book):
    connection = model.connect()
    book = model.get_book(connection, id_book)
    return render_template('book.html', book=book)

@app.route('/delete_book/<int:id_book>', methods=['POST'])
@login_required
def delete_book(id_book):
    connection = model.connect()
    reponse = model.delete_book(connection, id_book)
    flash(reponse)
    return redirect('/')


class LoginForm(FlaskForm):
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])

class signinForm(FlaskForm):
  name = StringField('name', validators=[validators.DataRequired()])
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])
  password_confirm = PasswordField('password_confirm', validators=[validators.DataRequired()])

class ListForm(FlaskForm):
    name = StringField('Nom de la liste', validators=[validators.DataRequired()]) 
    description = StringField('Description', validators=[validators.DataRequired()])
    image = FileField('Image', validators=[validators.DataRequired()])

class BookSearchForm(FlaskForm):
    nameBook = StringField('Nom du livre', validators=[validators.DataRequired()])

class BookForm(FlaskForm):
    title = StringField('Titre', validators=[validators.DataRequired()])
    author = StringField('Auteur', validators=[validators.DataRequired()])
    genre = SelectField('Catégorie', coerce=int, validators=[validators.DataRequired()])  
    isbn = IntegerField('ISBN', validators=[validators.DataRequired()])
    publication_date = StringField('Date de publication', validators=[validators.DataRequired()])
    description = StringField('Description', validators=[validators.DataRequired()])
    image = FileField('Image', validators=[validators.DataRequired()])


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

@app.route('/list/create', methods=['GET', 'POST'])
@login_required
def list_create():
    form = ListForm()
    if form.validate_on_submit():
        try:
            connection = model.connect()
            image_file = request.files.get('image')
            image_url = None
            if image_file and model.allowed_file(image_file.filename) :
                if not model.is_valid_image(image_file):
                    return render_template('list_edit.html', form=form)
                list_name = secure_filename(form.name.data)
                filename = f"{list_name}.png"

                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                image_url = f'/static/{filename}'
            else:
                return render_template('list_edit.html', form=form)

            book_list = {
                'id': None,
                'list_name': form.name.data,
                'description': form.description.data,
                'image_url': image_url
            }
            model.insert_book_list(connection, book_list)
            return redirect('/')
        except Exception as exception:
            app.logger.exception(exception)
    return render_template('list_edit.html', form=form)


@app.route('/book/create', methods=['GET', 'POST'])
@login_required
def book_create():
    form = BookForm() 
    connection = model.connect()

    lists = model.get_lists(connection)
    form.genre.choices = [(lst['id'], lst['list_name']) for lst in lists]  

    if form.validate_on_submit():
        try:
            
            image_file = request.files.get('image')
            image_url = None
            if image_file and model.allowed_file(image_file.filename) :
                if not model.is_valid_image(image_file):
                    return render_template('list_edit.html', form=form)
                book_name = secure_filename(str(form.isbn.data))
                filename = f"{book_name}.png"

                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                image_url = f'/static/{filename}'
            else:
                return render_template('book_edit.html', form=form)


            book = {  
                'title': form.title.data,
                'author': form.author.data,
                'genre': str(form.genre.data),
                'isbn': form.isbn.data,
                'publication_date': form.publication_date.data,
                'description': form.description.data,
                'image_url': image_url
            }
          
            book_id = model.insert_book(connection, book)

            book_list_relation = {
                'book_id': book_id,
                'list_id': form.genre.data
            }
            model.insert_book_list_relation(connection, book_list_relation)

            return redirect('/')
        
        except Exception as exception:
            app.logger.exception(exception) 
            return render_template('book_edit.html', form=form)

    return render_template('book_edit.html', form=form)


@app.route('/book/search', methods=['POST'])
def book_search():
    form = BookSearchForm()  
    if form.validate_on_submit():
        try:
            connection = model.connect()
            books=model.searchBook(connection, form.nameBook.data)
        except Exception as exception:
            app.logger.exception(exception)
            flash("Le livre n'a pas été trouvé !")
            return redirect('/')
    return render_template('books.html',books=books)



