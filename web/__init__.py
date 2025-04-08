from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from datetime import datetime, date
from itsdangerous import URLSafeTimedSerializer
import pymysql
from dotenv import load_dotenv
import os

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

def create_app():
    # This is for railway mysql database
    pymysql.install_as_MySQLdb()

    load_dotenv()

    app = Flask(__name__)
    
    # Apply configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("Set the SECRET_KEY environment variable.")

    # local mysql database
    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise ValueError("Set the DB_NAME environment variable.")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root@localhost/{db_name}'

    # railway mysql database (uncomment when deploying in railway, comment local above)
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'mysql+pymysql://root@localhost/{db_name}')


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

    from .models import Users, Admin, YoutubeUrl, Comments
    
    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith('admin_'):
            return Admin.query.get(int(user_id.split('_')[1]))
        return Users.query.get(int(user_id))

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

    def format_full_date(value):
        if isinstance(value, datetime):
            value = value.date() 
        if isinstance(value, date):
            return value.strftime('%B %d, %Y')
        return value
    
    app.jinja_env.filters['format_full_date'] = format_full_date

    return app
