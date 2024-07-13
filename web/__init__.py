from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail, Message
from random import *
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

    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    
    # @auth.route('/email-verification', methods=['GET', 'POST'])
    # def email_verification():
    #     if request.method == 'GET':
    #         return 'form action="/email-verification" method="POST"><input name="email"><input type="submit"></form>'
        
    #     # email = request.form.get('email')
    #     # token = s.dumps(email, salt='email-confirm')

    #     return 'The email you entered is {}'.format(request.form['email'])
    #     # return render_template("email_verification.html")

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

    return app