# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf.file import FileField, FileAllowed

class RecipeForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    content = TextAreaField('Inhalt  (Zutaten und Anweisungen)', validators=[DataRequired()])
    category = SelectField('Kategorie', choices=[('savory', 'Herzhaft'), ('sweet', 'Süß'), ('vegetarien', 'Vegetarisch')], validators=[DataRequired()])    
    difficulty = SelectField('Schwierigkeitsgrad', choices=[('easy', 'Einfach'), ('medium', 'Mittel'), ('difficult', 'Schwierig')], validators=[DataRequired()])
    picture = FileField('Rezeptfoto', validators=[FileAllowed(['jpg', 'png', 'jpeg'])]) 
    submit = SubmitField('Rezept veröffentlichen')

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', 
                           validators=[DataRequired(), Length(min=2, max=20)]) # Mettez à jour ce champ
    email = StringField('E-mail', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    confirm_password = PasswordField('Passwort bestätigen', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

class UpdateProfileForm(FlaskForm):
    username = StringField('Benutzername', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Profilbild aktualisieren', 
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Aktualisieren')