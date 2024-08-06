from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    
    # Apply configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'commentsanalysisbehindthescreens')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root@localhost/{os.getenv("DB_NAME", "behindthescreens")}'
    db.init_app(app)

    app.config.from_pyfile('config.cfg')
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .views import views
    from .auth import auth
    from .admin_routes import admin_bp

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .models import User, Admin, YoutubeUrl, Comments

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith('admin_'):
            return Admin.query.get(int(user_id.split('_')[1]))
        return User.query.get(int(user_id))

    def format_date(value):
        today = datetime.today().date()
        if isinstance(value, datetime):
            value = value.date()
        delta = today - value

        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Yesterday"
        elif delta.days < 7:
            return f"{delta.days} Days Ago"
        else:
            return value.strftime("%B %d, %Y")

    app.jinja_env.filters['format_date'] = format_date

    return app
