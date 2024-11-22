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
    
    connection = model.connect()
    
    books = model.get_books_in_list(connection, id_list_books)
   
    return render_template('books.html', books=books)

@app.route('/show_book/<int:id_book>', methods=['GET'])
def show_book(id_book):
    
    connection = model.connect()
    
    book = model.get_book(connection, id_book)
   
    return render_template('book.html', book=book)

@app.route('/delete_book/<int:id_book>', methods=['GET','POST'])
def delete_book(id_book):
    
    connection = model.connect()
    #raise exception ...
    respons = model.delete_book(connection, id_book)
   
    return redirect('/')#render_template('book.html', book=book)


class LoginForm(FlaskForm):
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])

class signinForm(FlaskForm):
  name = StringField('name', validators=[validators.DataRequired()])
  email = EmailField('email', validators=[validators.DataRequired()])
  password = PasswordField('password', validators=[validators.DataRequired()])
  password_confirm = PasswordField('password_confirm', validators=[validators.DataRequired()])

class ListForm(FlaskForm):
    name = StringField('Nom de la liste', validators=[validators.DataRequired()])  # Texte du label en français
    description = StringField('Description', validators=[validators.DataRequired()])
    image = FileField('Image', validators=[validators.DataRequired()])

class BookSearchForm(FlaskForm):
    nameBook = StringField('Nom du livre', validators=[validators.DataRequired()])

class BookForm(FlaskForm):
    title = StringField('Titre', validators=[validators.DataRequired()])
    author = StringField('Auteur', validators=[validators.DataRequired()])
    genre = SelectField('Catégorie', coerce=int, validators=[validators.DataRequired()])  # Utiliser SelectField et coerce pour l'ID
    isbn = IntegerField('ISBN', validators=[validators.DataRequired()])
    publication_date = StringField('Date de publication', validators=[validators.DataRequired()])
    description = StringField('Description', validators=[validators.DataRequired()])
    stock = IntegerField('Quantité', validators=[validators.DataRequired()])
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
            # Traitement du fichier image
            image_file = request.files.get('image')
            image_url = None
            if image_file and model.allowed_file(image_file.filename) :
                # Vérifie si l'image est valide
                if not model.is_valid_image(image_file):
                    return render_template('list_edit.html', form=form)
                # Utilisation de 'list_name' pour générer le nom de fichier
                list_name = secure_filename(form.name.data)
                filename = f"{list_name}.png"

                # Créez le dossier si nécessaire
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                # Enregistrement de l'image dans le dossier spécifié
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                # Génération de l'URL pour accéder à l'image
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
    """
    Cette fonction gère la création d'un nouveau livre dans l'application.

    - Si la méthode est GET, elle affiche un formulaire pour entrer les détails d'un nouveau livre.
    - Si la méthode est POST et que le formulaire est validé, elle insère le livre dans la base de données
      et récupère son ID pour créer une relation avec la liste de genres sélectionnée.
    - En cas d'erreur lors de l'insertion, elle affiche le formulaire avec un message d'erreur.

    La fonction s'assure également que le champ de sélection "genre" est rempli avec les options
    disponibles, récupérées depuis la table des listes.
    """
    form = BookForm() 
    connection = model.connect()

    # Récupérer les listes pour remplir le champ "genre"
    lists = model.get_lists(connection)
    form.genre.choices = [(lst['id'], lst['list_name']) for lst in lists]  # Affiche 'list_name', mais utilise 'id' comme valeur

    if form.validate_on_submit():
        try:
            # Traitement du fichier image
            image_file = request.files.get('image')
            image_url = None
            if image_file and model.allowed_file(image_file.filename) :
                # Vérifie si l'image est valide
                if not model.is_valid_image(image_file):
                    return render_template('list_edit.html', form=form)
                # Utilisation de 'list_name' pour générer le nom de fichier
                book_name = secure_filename(str(form.isbn.data))
                filename = f"{book_name}.png"

                # Créez le dossier si nécessaire
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                # Enregistrement de l'image dans le dossier spécifié
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)

                # Génération de l'URL pour accéder à l'image
                image_url = f'/static/{filename}'
            else:
                return render_template('book_edit.html', form=form)

            # Construire un dictionnaire avec les données du formulaire
            book = {  
                'title': form.title.data,
                'author': form.author.data,
                'genre': str(form.genre.data),
                'isbn': form.isbn.data,
                'publication_date': form.publication_date.data,
                'description': form.description.data,
                'stock': form.stock.data,
                'image_url': image_url
            }
            # Insérer le livre dans la base de données et récupérer son ID
            book_id = model.insert_book(connection, book)


            # Créer la relation entre le livre et la liste choisie
            book_list_relation = {
                'book_id': book_id,
                'list_id': form.genre.data
            }
            model.insert_book_list_relation(connection, book_list_relation)

            return redirect('/')
        
        except Exception as exception:
            app.logger.exception(exception)  # Log de l'exception
            return render_template('book_edit.html', form=form)

    return render_template('book_edit.html', form=form)

"""

Description:
Route:
    - /book/search : Permet la recherche de livres par titre.
"""

@app.route('/book/search', methods=['POST'])
def book_search():
    form = BookSearchForm()  
    if form.validate_on_submit():
        try:
            connection = model.connect()
            books=model.searchBook(connection, form.nameBook.data)
        except Exception as exception:
            app.logger.exception(exception)
            return redirect('/')
    return render_template('books.html',books=books)



