# models.py
from datetime import datetime
from database import db  # Import the database instance from database.py
from flask_login import UserMixin


# Model for the association table between User and Recipe
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
)

# Model for users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_picture = db.Column(db.String(20), nullable=False, default='default.jpg')
    # Relationship with the Recipe table
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    favorites_recipes = db.relationship('Recipe', secondary=favorites, lazy='dynamic',
        backref=db.backref('users_favorited', lazy=True))

# Model for recipes
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False) 
    instructions = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=True) # Ex: "sweet", "savory", "vegetarian"
    difficulty = db.Column(db.String(50), nullable=True) # Ex: "easy", "medium", "difficult"
    image_file = db.Column(db.String(20), nullable=False, default='default_recipe.jpg')
    # Relationships with the Rating and Comment tables
    ratings = db.relationship('Rating', backref='recipe', lazy=True)
    comments = db.relationship('Comment', backref='recipe', lazy=True)
    
    # The __repr__ method must have the same indentation as other attributes
    def __repr__(self):
        return f"Recipe('{self.title}', '{self.date_posted}')"
    #  Method to calculate the average rating
    @property
    def average_rating(self):
        # Check if there are any ratings
        if self.ratings:
            # Calculate the sum of scores and divide by the total number of ratings
            return sum(rating.score for rating in self.ratings) / len(self.ratings)
        return 0

# Model for comments
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    # Relationship to link the comment to its author
    author = db.relationship('User', backref='comments', lazy=True) 

# Model for ratings (1 to 5 stars system)
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False) # the score, from 1 to 5
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)