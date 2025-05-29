import os
import logging
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create declarative base for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
bcrypt = Bcrypt()
login_manager = LoginManager()

# Create the Flask app
app = Flask(__name__)

# Set secret key from environment variable
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Print the secret key to confirm it's loaded correctly
print(f"Secret Key: {app.secret_key}")

# Configure the database
#app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
# In app.py, update your database URI to include explicit parameters
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:L1v3L0ng&Prosper!@localhost:3306/freelancer_db?charset=utf8mb4&autocommit=true"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 3600,  # Longer connection recycling
    "pool_pre_ping": True,
    "pool_size": 5,        # Smaller pool to leave connections for Workbench
    "max_overflow": 10
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True  # Enable modification tracking
# In app.py, add after your SQLAlchemy configuration:
app.config["SQLALCHEMY_ECHO"] = True  # Log all SQL queries
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = True  # Auto-commit at the end of each request

# Configure file uploads
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static/uploads")

@app.before_request
def before_request():
    db.engine.dispose()

# Initialize extensions with the app
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# Configure login manager
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Create database tables within application context
with app.app_context():
    # Import models here to avoid circular imports
    from models import Freelancer, Client, Project, Task, TimeLog, Invoice, LoginSession, ProjectFile, Tag, ProjectTag

    db.create_all()
