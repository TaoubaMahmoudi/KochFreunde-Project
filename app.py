from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import bcrypt
import requests
import os
import secrets
from PIL import Image
from database import db
# Ensure User, Recipe, Comment, Rating models are imported
from models import User, Recipe, Comment, Rating 
# Ensure all necessary forms are imported
from forms import RecipeForm, RegistrationForm, UpdateProfileForm


# --- GLOBAL API CONFIG ---
# WARNING: API key is hardcoded as requested. For production, use environment variables.
SPOONACULAR_API_KEY = "ca5e476c4b0249ca94ff328cedbb7f81" 
BASE_URL = "https://api.spoonacular.com/recipes" # Base for detail lookup
API_URL = f"{BASE_URL}/findByIngredients"     # Base for ingredient search
# -------------------------

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


# Flask application initialization
app = Flask(__name__)
# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'eaa965d5287047173c78915003489b88f298346aa212e4e9'

# Database object initialization with the app
db.init_app(app)

# Login manager initialization
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info' # Used for flashing message when redirected

# --- USER LOADER FUNCTION ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route("/")
def home():
    # Retrieve the 6 most recent recipes
    recent_recipes = Recipe.query.order_by(Recipe.date_posted.desc()).limit(6).all()
    # Pass the recipes to the template
    return render_template('home.html', recent_recipes=recent_recipes)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Prevent logged-in users from accessing the login page
        return redirect(url_for('dashboard')) 

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect email or password.", "danger")
            return redirect(url_for('login')) # Redirect to show the flash message

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
            picture_file = 'default_recipe.jpg' # Default image if none is uploaded

        new_recipe = Recipe(
            title=form.title.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            date_posted=datetime.utcnow(),
            user_id=current_user.id,
            category=form.category.data,  
            difficulty=form.difficulty.data,
            image_file=picture_file
        )
        db.session.add(new_recipe)
        db.session.commit()
        flash("Recipe added successfully!", "success")
        return redirect(url_for('dashboard')) 
    return render_template('add_recipe.html', form=form) 

@app.route("/recipes")
def list_recipes():
    search_query = request.args.get('query') 
    category_filter = request.args.get('category')
    difficulty_filter = request.args.get('difficulty')

    # Start the base query
    recipes = Recipe.query

    # Apply filters
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
    """
    Handles the display and submission (comments/ratings) for a recipe.
    Supports both internal database recipes and external API recipes.
    """
    
    # --- 1. Try to load the recipe from the internal database ---
    recipe = Recipe.query.get(recipe_id)
    
    is_external_recipe = False
    recipe_data = None
    
    if not recipe:
        # --- 2. If not found, assume it's an API recipe ID ---
        is_external_recipe = True
        
        details_url = f"{BASE_URL}/{recipe_id}/information"
        params = {
            'apiKey': SPOONACULAR_API_KEY,
            'includeNutrition': 'false'
        }
        
        try:
            response = requests.get(details_url, params=params)
            response.raise_for_status() 
            recipe_data = response.json()
            
        except requests.exceptions.RequestException as e:
            flash("Error retrieving the recipe idea from the API.", "danger")
            # Redirect to home or search page if API fails
            return redirect(url_for('home')) 
    
    
    # Determine which recipe object to use for the template (internal or external data)
    display_recipe = recipe if recipe else recipe_data
    
    # --- 3. Handle user ratings (only applicable to internal recipes) ---
    user_rating_score = 0
    if not is_external_recipe and current_user.is_authenticated:
        user_rating_obj = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        if user_rating_obj:
            user_rating_score = user_rating_obj.score

    # --- 4. Handle POST form submission (Comment/Rating) ---
    if request.method == 'POST':
        if not current_user.is_authenticated:
            # Security: Redirect if user tries to comment without being logged in
            flash("You must be logged in to post a comment or rating.", "warning")
            return redirect(url_for('login')) 
        
        # Comments and ratings are only allowed for internal recipes
        if is_external_recipe:
            flash("Comments and ratings are only allowed for our internal recipes.", "warning")
            return redirect(url_for('recipe_detail', recipe_id=recipe_id))
            
        comment_content = request.form.get('comment_content')
        
        if comment_content:
            new_comment = Comment(
                content=comment_content,
                user_id=current_user.id,
                recipe_id=recipe.id,
                date_posted=datetime.utcnow()
            )
            db.session.add(new_comment)
            db.session.commit()
            
            flash("Comment successfully added!", "success")
            # PRG (Post/Redirect/Get) pattern
            return redirect(url_for('recipe_detail', recipe_id=recipe.id))
        else:
            flash("Comment content cannot be empty.", "warning")


    # --- 5. Render the template: The critical change is here! ---
    if is_external_recipe:
        # If it's an API recipe, use the dedicated template
        return render_template('ai_recipe_detail.html', 
                            recipe=display_recipe, 
                            is_external=is_external_recipe)
    else:
        # Otherwise, use the standard template for internal recipes
        return render_template('recipe_detail.html', 
                            recipe=display_recipe, 
                            user_rating=user_rating_score,
                            is_external=is_external_recipe)

@app.route("/rate/<int:recipe_id>", methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    # Check if the recipe is internal before rating
    if not Recipe.query.get(recipe_id):
        flash("You cannot rate external recipes.", "warning")
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

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
    
    # Determine the user to display (current user if no ID is specified)
    user_id_to_check = current_user.id if user_id is None else user_id

    user_to_show = User.query.get_or_404(user_id_to_check)
    
    # --- FAVORITES LOADING LOGIC ---
    user_favorites = [] 
    
    # Load favorites only for the current user
    if user_id_to_check == current_user.id:
        try:
            from models import favorites # Import the association table reference
            favorite_recipe_objects = db.session.query(Recipe).join(favorites).filter(
                favorites.c.user_id == user_id_to_check
            ).all()
            user_favorites = favorite_recipe_objects
        except ImportError:
            # This is a safe fallback if models is not structured exactly as expected
            print("WARNING: Could not load favorites association table.")
            user_favorites = []
        
    # --- PUBLISHED RECIPES LOADING LOGIC ---
    user_recipes = Recipe.query.filter_by(user_id=user_to_show.id).all()
    
    return render_template(
        'profile.html', 
        user=user_to_show,
        recipes=user_recipes,
        user_favorites=user_favorites 
    )


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
        flash("Your profile has been updated!", "success")
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
    
    # Prepare the data for the template, including the image path
    image_file = url_for('static', filename='profile_pics/' + current_user.profile_picture)
    return render_template('update_profile.html', title='Edit Profile', form=form, image_file=image_file)

@app.route("/toggle_favorite/<int:recipe_id>")
@login_required
def toggle_favorite(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if the recipe is already in favorites
    if recipe in current_user.favorites_recipes:
        current_user.favorites_recipes.remove(recipe)
        flash(f"'{recipe.title}' removed from favorites.", "info")
    else:
        current_user.favorites_recipes.append(recipe)
        flash(f"'{recipe.title}' added to favorites!", "success")
    
    db.session.commit()

    # Redirect to the page the user came from, or recipe detail page as a fallback
    return redirect(request.referrer or url_for('recipe_detail', recipe_id=recipe.id)) 

@app.route("/recipe/<int:recipe_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Check if the current user is the recipe author
    if recipe.user_id != current_user.id:
        flash("You are not authorized to modify this recipe.", "danger")
        return redirect(url_for('home'))

    # Pre-populate form data
    form = RecipeForm(obj=recipe) 
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.ingredients = form.ingredients.data
        recipe.instructions = form.instructions.data
        recipe.category = form.category.data
        recipe.difficulty = form.difficulty.data  

        if form.picture.data:
            picture_file = save_recipe_picture(form.picture.data)
            recipe.image_file = picture_file

        db.session.commit()
        flash("Recipe updated successfully!", "success")
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    # GET request: form is automatically pre-filled by 'obj=recipe'
    return render_template('add_recipe.html', title='Edit Recipe', form=form)

@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Check if the current user is the recipe author
    if recipe.user_id != current_user.id:
        flash("You are not authorized to delete this recipe.", "danger")
        return redirect(url_for('home'))
    
    db.session.delete(recipe)
    db.session.commit()
    flash("Recipe deleted successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route('/ai-recipes', methods=['GET'])
def ai_recipe_search():
    # Retrieve ingredients from the form (even if the field is initially empty)
    ingredients_raw = request.args.get('ingredients', '').strip()
    recipes = None # Initialize recipe list to None
    
    # Execute search only if the user entered something
    if ingredients_raw:
        # Clean and format ingredients for the API (comma-separated)
        ingredient_list = ",".join([
            ing.strip() for ing in ingredients_raw.split(',') if ing.strip()
        ])
        
        # Check that valid ingredients exist after cleaning
        if ingredient_list:
            # Prepare API query parameters
            params = {
                'apiKey': SPOONACULAR_API_KEY,
                'ingredients': ingredient_list,
                'number': 10,       # Return up to 10 recipes
                'ranking': 1,       # Ranking: minimize missing ingredients
                'ignorePantry': True # Ignore basic pantry items (salt, pepper)
            }
            
            # Call the Spoonacular API
            try:
                response = requests.get(API_URL, params=params)
                response.raise_for_status() # Raise error for 4xx/5xx codes
                
                # Retrieve JSON data
                recipes = response.json()
                
            except requests.exceptions.RequestException as e:
                print(f"Error calling Spoonacular API: {e}")
                flash(f"Error during API search: {e}", "danger")
                recipes = [] # Set recipes to an empty list to prevent crashing
                
    # Render the template, passing the results and the initial query
    return render_template('ai_recipe_search.html', recipes=recipes, search_query=ingredients_raw)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# --- APPLICATION LAUNCH ---
# This block must be at the end of the file
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() # Uncomment this line to create the database tables on first run
        pass
    app.run(debug=True)
