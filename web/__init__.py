from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config  # Import the Config class

db = SQLAlchemy()
DB_NAME = "behindthescreens"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load the configuration from the Config class
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .oauth import init_oauth  # Import the init_oauth function

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, YoutubeUrl, Comments

    with app.app_context():
        db.create_all()
        init_oauth(app)  # Initialize oauth within the app context

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app