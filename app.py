from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import bcrypt

from database import db
from models import User, Recipe, Comment, Rating
from forms import RecipeForm
from forms import RegistrationForm
import os
import secrets
from PIL import Image
from forms import UpdateProfileForm

def save_recipe_picture(form_picture):
    """Saves a recipe photo and returns its filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/recipe_pics', picture_fn)

    output_size = (800, 600)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# Flask application initialization
app = Flask(__name__)
# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'eaa965d5287047173c78915003489b88f298346aa212e4e9'

# Database object initialization with the app
db.init_app(app)

# Login manager initialization
#db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# --- USER LOADER FUNCTION ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
# All your routes are defined here

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
   
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Incorrect email or password."

    return render_template('login.html')

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/add_recipe", methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_recipe_picture(form.picture.data)
        else:
            picture_file = 'default_recipe.jpg'

        new_recipe = Recipe(
            title=form.title.data,
            content=form.content.data,
            date_posted=datetime.utcnow(),
            user_id=current_user.id,
            category=form.category.data,  
            difficulty=form.difficulty.data, 
        )
        db.session.add(new_recipe)
        db.session.commit()
        return redirect(url_for('dashboard')) 
    return render_template('add_recipe.html', form=form) 

@app.route("/recipes")
def list_recipes():
    search_query = request.args.get('query') 
    category_filter = request.args.get('category')
    difficulty_filter = request.args.get('difficulty')

    # Start the base query
    recipes = Recipe.query

    if search_query:
        recipes = recipes.filter(Recipe.title.ilike(f'%{search_query}%'))
    
    if category_filter:
        recipes = recipes.filter_by(category=category_filter)

    if difficulty_filter:
        recipes = recipes.filter_by(difficulty=difficulty_filter)

    recipes = recipes.all()
    return render_template('recipes.html', recipes=recipes)

@app.route("/recipe/<int:recipe_id>", methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'POST':
        # Make sure the user is logged in to submit a comment
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        comment_content = request.form['comment_content']
        new_comment = Comment(
            content=comment_content,
            user_id=current_user.id,
            recipe_id=recipe.id,
            date_posted=datetime.utcnow()
        )
        db.session.add(new_comment)
        db.session.commit()
        
        # Redirect the user to the same page to avoid form resubmission
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))

    return render_template('recipe_detail.html', recipe=recipe)

@app.route("/rate/<int:recipe_id>", methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    # Get the rating from the form
    score = request.form['score']
    
    # Check if the user has already rated this recipe
    existing_rating = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing_rating:
        # Update the existing rating
        existing_rating.score = score
    else:
        # Create a new rating
        new_rating = Rating(score=score, user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(new_rating)
    
    db.session.commit()
    
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route("/profile", defaults={'user_id': None})
@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    # If the URL doesn't contain an ID, show the profile of the logged-in user
    if user_id is None:
        user_to_show = current_user
         # If it's the logged-in user's profile, also include their favorites
        user_favorites = current_user.favorites_recipes
    else:
        # Otherwise, retrieve the user by their ID
        user_to_show = User.query.get_or_404(user_id)
        # For other users, the favorites list should not be displayed (or left empty)
        user_favorites = [] 
    
    # Get all recipes for this user
    user_recipes = Recipe.query.filter_by(user_id=user_to_show.id).all()
    
    return render_template('profile.html', user=user_to_show, recipes=user_recipes, user_favorites=user_favorites)

def save_picture(form_picture):
    """Saves a profile picture and returns its filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/profile/update", methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_picture = picture_file
        
        current_user.username = form.username.data
        db.session.commit()
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
    
    # Prepare the data for the template, including the image path
    image_file = url_for('static', filename='profile_pics/' + current_user.profile_picture)
    return render_template('update_profile.html', title='Modifier le profil', form=form, image_file=image_file)

@app.route("/toggle_favorite/<int:recipe_id>")
@login_required
def toggle_favorite(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if the recipe is already in favorites
    if recipe in current_user.favorites_recipes:
        current_user.favorites_recipes.remove(recipe)
    else:
        current_user.favorites_recipes.append(recipe)
    
    db.session.commit()
    
    return redirect(url_for('recipe_detail', recipe_id=recipe.id))

@app.route("/recipe/<int:recipe_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        return "You are not authorized to modify this recipe.", 403

    #  Pass the recipe object directly to the form to pre-populate it
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.content = form.content.data
        recipe.category = form.category.data
        recipe.difficulty = form.difficulty.data   

        if form.picture.data:
            picture_file = save_recipe_picture(form.picture.data)
            recipe.image_file = picture_file

        db.session.commit()
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    elif request.method == 'GET':
        form.title.data = recipe.title
        form.content.data = recipe.content
        form.category.data = recipe.category
        form.difficulty.data = recipe.difficulty

    return render_template('add_recipe.html', title='Modifier la recette', form=form)

@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        return "You are not authorized to delete this recipe.", 403
    
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- APPLICATION LAUNCH ---
# This block must be at the end of the file
if __name__ == '__main__':
    app.run(debug=True)

