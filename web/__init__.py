from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

db = SQLAlchemy()
DB_NAME = "behindthescreens"
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'commentsanalysisbehindthescreens'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root@localhost/{DB_NAME}'
    db.init_app(app)

    app.config.from_pyfile('config.cfg')
    mail.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, YoutubeUrl, Comments

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
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