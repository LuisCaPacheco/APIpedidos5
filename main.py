import os

from flask import Flask, render_template, redirect, url_for, flash
from decouple import config
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from wtforms import StringField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange

app = Flask(_name_)
# Configuración de la base de datos (MariaDB)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql://{config('DB_USER')}:{config('DB_PASSWORD')}@{config('DB_HOST')}/{config('DB_NAME')}"

app.config['UPLOAD_FOLDER'] = 'static/archivos'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Tamaño máximo de la imagen (2 MB)
db = SQLAlchemy(app)

SECRET_KEY = config('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)


class ProductForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    precio = FloatField('Precio', validators=[DataRequired(),
                                              NumberRange(min=0.99, message='El precio debe ser un número positivo.')])
    imagen = FileField('Imagen', validators=[DataRequired()])


@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)


@app.route('/page_principal')
def page_principal():
    return render_template('page_principal.html')


@app.route('/create', methods=['GET', 'POST'])
def create():
    form = ProductForm()

    if form.validate_on_submit():
        imagen = form.imagen.data
        imagen_nombre = secure_filename(imagen.filename)

        if not Product.query.filter_by(imagen=imagen_nombre).first():
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_nombre))

            product = Product(
                imagen=imagen_nombre,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                precio=form.precio.data
            )

            db.session.add(product)
            db.session.commit()

            flash('Producto agregado con éxito', 'success')
            return redirect(url_for('index'))
        else:
            flash('El nombre de la imagen ya está en uso', 'danger')

    return render_template('create.html', form=form)


@app.route('/list_products')
def list_products():
    # Lógica para obtener la lista de productos, por ejemplo:
    products = Product.query.all()
    return render_template('list_products.html', products=products)


@app.route('/read/<int:id>')
def read(id):
    product = Product.query.get(id)
    return render_template('read.html', product=product)


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    product = Product.query.get(id)
    form = ProductForm(obj=product)  # Rellena el formulario con los datos existentes

    if form.validate_on_submit():
        # Update the product object with form data
        form.populate_obj(product)

        # Check if a new image was uploaded
        new_image = form.imagen.data
        if new_image:
            # Save the new image with the same name as the old one
            new_image_nombre = secure_filename(new_image.filename)
            new_image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_image_nombre)
            new_image.save(new_image_path)
            product.imagen = new_image_nombre

        db.session.commit()
        flash('Producto editado con éxito', 'success')
        return redirect(url_for('read', id=id))

    return render_template('update.html', form=form, product=product)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    product = Product.query.get(id)

    # Delete the product image from the 'static/archivos' folder
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.imagen)
    if os.path.exists(image_path):
        os.remove(image_path)

    # Delete the product from the database
    db.session.delete(product)
    db.session.commit()
    flash('Producto eliminado con éxito', 'success')
    return redirect(url_for('index'))


if _name_ == '_main_':
    app.run(debug=True)