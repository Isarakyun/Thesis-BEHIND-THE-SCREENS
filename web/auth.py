from flask_dance.contrib.google import make_google_blueprint, google
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_mail import Mail, Message
from random import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from .models import User, Admin, YoutubeUrl, Comments, SummarizedComments, FrequentWords, SentimentCounter, WordCloudImage, UserLog, AdminLog, GetUrl
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .analysis import clean_text, word_cloud, get_summary, extract_comments
from flask_login import login_user, login_required, logout_user, current_user
from pytube import YouTube
from transformers import pipeline
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from collections import Counter
import base64
import logging
import re
from flask_wtf import CSRFProtect

auth = Blueprint('auth', __name__)

mail = Mail()
s = URLSafeTimedSerializer('SECRET_KEY')
MODEL = 'cardiffnlp/twitter-roberta-base-sentiment'
sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL)
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
stop_words = set(stopwords.words('english'))
sia = SentimentIntensityAnalyzer()
valid_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,7}$'

# Audit Trail Logger
def user_log(action):
    if current_user.is_authenticated:
        user_id = current_user.id
        audit_trail = UserLog(user_id=user_id, action=action)
        db.session.add(audit_trail)
        db.session.commit()

def admin_log(action):
    if current_user.is_authenticated:
        admin_id = current_user.id
        audit_trail = AdminLog(admin_id=admin_id, action=action)
        db.session.add(audit_trail)
        db.session.commit()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # print(f"Attempting login with email: {email}")

        # ADMIN LOGIN
        admin = Admin.query.filter_by(username=email).first()
        if admin:            
            if check_password_hash(admin.password, password):
                # print("Admin password correct")
                login_user(admin, remember=True)
                admin_log(f"Behind the Screens {admin.username} Logged in")
                return redirect(url_for('admin.dashboard'))

            else:
                # print("Admin password incorrect")
                flash('Incorrect password, try again.', category='error')

        # USER LOGIN
        user = User.query.filter_by(email=email).first()
        if user:
            # print(f"User found: {user.email}")
            if check_password_hash(user.password, password):
                # print("User password correct")
                login_user(user, remember=True)
                user_log(f"{user.username} Logged in")
                return redirect(url_for('views.main'))
            else:
                # print("User password incorrect")
                flash('Incorrect password, try again.', category='error')
        else:
            # print("Email does not exist")
            flash('Email does not exist.', category='error')
    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    if current_user.id == 0:
        admin_log(f"Behind the Screens {current_user.username} Logged out")
        logout_user()
    else:
        user_log(f"{current_user.username} Logged out")  # Simplify the logout action message
        logout_user()
        flash('Logged out successfully!', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirmpassword')

        existing_email = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()

        if existing_email:
            flash('Email already exists.', category='error')
        elif existing_username:
            flash('Username already exists.', category='error')
        elif not re.match(valid_email, email):
            flash('Email must be valid.', category='error')
        elif password != confirmpassword:
            flash('Passwords don\'t match.', category='error')
        elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            flash('Password must be at least 8 characters long and contain alphanumeric characters.', category='error')
        else:
            new_user = User(username=username, email=email, confirmed_email=False, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            user_log(f"User {username} has signed up")

            token = s.dumps(email, salt='email-confirm')
            msg = Message('Email Confirmation', sender='behindthescreens.thesis@gmail.com', recipients=[email])
            link = url_for('auth.confirm_email', token=token, _external=True)
            msg.html = """
                <html>
                <head>
                    <style>
                        .email-content {{
                            margin: 20px;
                            padding: 20px;
                            background-color: #e5e7eb;
                        }}
                        .email-header {{
                            font-size: 24px;
                            line-height: 32px;
                            font-weight: 600;
                            color: #881337;
                            text-align: center;
                        }}
                        .email-body {{
                            font-weight: 500;
                            font-size: 18px;
                            line-height: 28px;
                            margin-top: 8px;
                            color: #4b5563;
                        }}
                        .email-footer {{
                            margin-top: 8px;
                            font-size: 14px;
                            line-height: 20px;
                            color: #fb7185;
                        }}
                        .text-center {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-outline">
                        <div class="text-center">
                            <div class="text-center">
                            <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                            </div>
                            <div class="email-header">Welcome to Behind the Screens!</div>
                            <div class="email-body">
                                Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments. <br>
                            To verify your email, please click this <a href="{}">link</a>. We hope you enjoy using our platform!
                            </div>
                            <div class="email-footer">
                                If you didn't make this request, ignore this email. This email is automated, please do not reply.
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            """.format(link, link)
            mail.send(msg)

            return redirect(url_for('views.mail_sent'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/email-confirmation/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=600)
    except  SignatureExpired:
        return render_template("expired_url.html")
    except BadTimeSignature:
        return render_template("invalid_url.html")
    user = User.query.filter_by(email=email).first()
    user.confirmed_email = True
    db.session.commit()
    user_log(f"User {user.username} has confirmed their email")

    return render_template("email_verified.html")

@auth.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template("forgot_password.html")
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        token = s.dumps(email, salt='email-confirm')
        msg = Message('Reset Password', sender='behindthescreens.thesis@gmail.com', recipients=[email])
        link = url_for('auth.reset_password', token=token, _external=True)
        msg.html = """
            <html>
            <head>
                <style>
                    .email-content {{
                        margin: 20px;
                        padding: 20px;
                        background-color: #e5e7eb;
                    }}
                    .email-header {{
                        font-size: 24px;
                        line-height: 32px;
                        font-weight: 600;
                        color: #881337;
                        text-align: center;
                    }}
                    .email-body {{
                        font-weight: 500;
                        font-size: 18px;
                        line-height: 28px;
                        margin-top: 8px;
                        color: #4b5563;
                    }}
                    .email-footer {{
                        margin-top: 8px;
                        font-size: 14px;
                        line-height: 20px;
                        color: #fb7185;
                    }}
                    .text-center {{
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="email-outline">
                    <div class="text-center">
                        <div class="text-center">
                        <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                        </div>
                        <div class="email-header">Thank you for using Behind the Screens!</div>
                        <div class="email-body">
                            If you requested to reset your password, please click this <a href="{}">link</a>.
                        </div>
                        <div class="email-footer">
                            If you didn't make this request, ignore this email. This email is automated, please do not reply.
                        </div>
                    </div>
                </div>
            </body>
            </html>
        """.format(link, link)
        mail.send(msg)
        user_log(f"User {user.username} requested to reset their password")
        return redirect(url_for('views.mail_sent'))
    else:
        flash('Email does not exist.', category='error')
    return render_template("forgot_password.html")

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=600)
        if request.method == 'POST':
            password = request.form.get('password')
            confirmpassword = request.form.get('confirmpassword')
            user = User.query.filter_by(email=email).first()
            if password != confirmpassword:
                flash('Passwords don\'t match.', category='error')
            elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
                flash('Password must be at least 8 characters long and contain both letters and numbers.', category='error')
            else:
                user.password=generate_password_hash(password, method='sha256')
                db.session.commit()
                
                token = s.dumps(email, salt='email-confirm')
                msg = Message('Password Changed', sender='behindthescreens.thesis@gmail.com', recipients=[email])
                link = url_for('auth.home', _external=True)
                msg.html = """
                    <html>
                    <head>
                        <style>
                            .email-content {{
                                margin: 20px;
                                padding: 20px;
                                background-color: #e5e7eb;
                            }}
                            .email-header {{
                                font-size: 24px;
                                line-height: 32px;
                                font-weight: 600;
                                color: #881337;
                                text-align: center;
                            }}
                            .email-body {{
                                font-weight: 500;
                                font-size: 18px;
                                line-height: 28px;
                                margin-top: 8px;
                                color: #4b5563;
                            }}
                            .email-footer {{
                                margin-top: 8px;
                                font-size: 14px;
                                line-height: 20px;
                                color: #fb7185;
                            }}
                            .text-center {{
                                text-align: center;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="email-outline">
                            <div class="text-center">
                                <div class="text-center">
                                    <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                                </div>
                                <div class="email-header">Password Reset</div>
                                <div class="email-body">
                                    Thank you for using our platform. <br>
                                    We would like to inform you that your password has been successfully changed. <br>
                                    If you didn't make this request, please contact our <a href="{}#contact">support</a> team. 
                                </div>
                                <div class="email-footer">
                                    This email is automated, please do not reply.
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                """.format(link, link)
                mail.send(msg)
                user_log(f"User {user.username} has changed their password")
                return redirect(url_for('views.password_reset_success'))
    except  SignatureExpired:
        return render_template("expired_url.html")
    except BadTimeSignature:
        return render_template("invalid_url.html")
    
    return render_template("reset_password.html")

@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('password')
        new_password = request.form.get('newpassword')
        confirm_password = request.form.get('confirmpassword')
        if check_password_hash(current_user.password, current_password):
            if new_password == confirm_password:
                if len(new_password) < 8:
                    flash('Password must be at least 8 characters.', category='error')
                else:
                    current_user.password = generate_password_hash(new_password, method='sha256')
                    db.session.commit()
                    user_log(f"User {current_user.username} has changed their password")
                    flash('Password changed successfully!', category='success')
                    return redirect(url_for('views.settings'))
            else:
                flash('Passwords do not match.', category='error')
        else:
            flash('Incorrect password.', category='error')
    return render_template("user_settings.html")

@auth.route('/change-username', methods=['POST'])
@login_required
def change_username():
    if request.method == 'POST':
        old_username = request.form.get('old-username')
        new_username = request.form.get('username')
        existing_username = User.query.filter_by(username=new_username).first()
        if existing_username:
            flash('Username already exists.', category='error')
            return redirect(url_for('views.settings'))
        else:
            current_user.username = new_username
            db.session.commit()
            user_log(f"User '{old_username}' changed username to '{new_username}'")
            flash('Username changed successfully!', category='success')
            return redirect(url_for('views.settings'))
    return render_template("user_settings.html")

@auth.route('/resend-confirmation', methods=['POST'])
@login_required
def resend_confirmation():
    email = current_user.email
    token = s.dumps(email, salt='email-confirm')
    msg = Message('Email Confirmation', sender='behindthescreens.thesis@gmail.com', recipients=[email])
    link = url_for('auth.confirm_email', token=token, _external=True)
    msg.html = """
        <html>
        <head>
            <style>
                .email-content {{
                    margin: 20px;
                    padding: 20px;
                    background-color: #e5e7eb;
                }}
                .email-header {{
                    font-size: 24px;
                    line-height: 32px;
                    font-weight: 600;
                    color: #881337;
                    text-align: center;
                }}
                .email-body {{
                    font-weight: 500;
                    font-size: 18px;
                    line-height: 28px;
                    margin-top: 8px;
                    color: #4b5563;
                }}
                .email-footer {{
                    margin-top: 8px;
                    font-size: 14px;
                    line-height: 20px;
                    color: #fb7185;
                }}
                .text-center {{
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="email-outline">
                <div class="text-center">
                    <div class="text-center">
                    <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                    </div>
                    <div class="email-header">Welcome to Behind the Screens!</div>
                    <div class="email-body">
                        Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments. <br>
                    To verify your email, please click this <a href="{}">link</a>. We hope you enjoy using our platform!
                    </div>
                    <div class="email-footer">
                        If you didn't make this request, ignore this email. This email is automated, please do not reply.
                    </div>
                </div>
            </div>
        </body>
        </html>
    """.format(link, link)
    mail.send(msg)
    user_log(f"User {current_user.username} requested an email confirmation")
    flash('Email confirmation link has been sent. Please check your email before the link expires.', category='success')
    return redirect(url_for('views.settings'))

@auth.route('/change-email', methods=['POST'])
@login_required
def change_email():
    if request.method == 'POST':
        old_email = request.form.get('old-email')
        new_email = request.form.get('email')
        existing_email = User.query.filter_by(email=new_email).first()
        if existing_email:
            flash('Email already exists.', category='error')
            return redirect(url_for('views.settings'))
        elif not re.match(valid_email, new_email):
            flash('Email must be valid.', category='error')
            return redirect(url_for('views.settings'))
        else:
            current_user.confirmed_email = False
            current_user.email = new_email
            db.session.commit()
            user_log(f"User '{old_email}' changed email to '{new_email}'")
            flash('Please check your email to verify the changes.', category='success')

            # send mail to the new email for email confirmation/verification
            token = s.dumps(new_email, salt='email-confirm')
            msg = Message('Email Change Confirmation', sender='behindthescreens.thesis@gmail.com', recipients=[new_email])
            link = url_for('auth.change_email_confirmation', token=token, _external=True)
            msg.html = """
                <html>
                <head>
                    <style>
                        .email-content {{
                            margin: 20px;
                            padding: 20px;
                            background-color: #e5e7eb;
                        }}
                        .email-header {{
                            font-size: 24px;
                            line-height: 32px;
                            font-weight: 600;
                            color: #881337;
                            text-align: center;
                        }}
                        .email-body {{
                            font-weight: 500;
                            font-size: 18px;
                            line-height: 28px;
                            margin-top: 8px;
                            color: #4b5563;
                        }}
                        .email-footer {{
                            margin-top: 8px;
                            font-size: 14px;
                            line-height: 20px;
                            color: #fb7185;
                        }}
                        .text-center {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-outline">
                        <div class="text-center">
                            <div class="text-center">
                            <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                            </div>
                            <div class="email-header">Change of Email Address</div>
                            <div class="email-body">
                                Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments. <br>
                                You have changed your email to this one, to verify, please click this <a href="{}">link</a>. Thank you for your continued support!
                            </div>
                            <div class="email-footer">
                                If you didn't make this request, ignore this email. This email is automated, please do not reply.
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            """.format(link, link)
            mail.send(msg)

            # send mail to the old email that user changed their email
            old_email_msg = Message('Email Changed', sender='behindthescreens.thesis@gmail.com', recipients=[old_email])
            old_email_msg.html = """
                <html>
                <head>
                    <style>
                        .email-content {{
                            margin: 20px;
                            padding: 20px;
                            background-color: #e5e7eb;
                        }}
                        .email-header {{
                            font-size: 24px;
                            line-height: 32px;
                            font-weight: 600;
                            color: #881337;
                            text-align: center;
                        }}
                        .email-body {{
                            font-weight: 500;
                            font-size: 18px;
                            line-height: 28px;
                            margin-top: 8px;
                            color: #4b5563;
                        }}
                        .email-footer {{
                            margin-top: 8px;
                            font-size: 14px;
                            line-height: 20px;
                            color: #fb7185;
                        }}
                        .text-center {{
                            text-align: center;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-outline">
                        <div class="text-center">
                            <div class="text-center">
                            <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                            </div>
                            <div class="email-header">Your Email Has Been Changed</div>
                            <div class="email-body">
                                This email is no longer connected to the account in our platform. <br> If you didn't make this request, please contact our support team.
                                Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments.
                            </div>
                            <div class="email-footer">
                                If you didn't make this request, ignore this email. This email is automated, please do not reply.
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            """.format()
            mail.send(old_email_msg)

            return redirect(url_for('views.settings'))
    return render_template("user_settings.html")

@auth.route('/change-email-confirmation/<token>')
@login_required
def change_email_confirmation(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=600)
    except  SignatureExpired:
        return render_template("expired_url.html")
    except BadTimeSignature:
        return render_template("invalid_url.html")
    current_user.confirmed_email = True
    db.session.commit()
    user_log(f"User {current_user.username} confirmed change of email to {email}")
    return render_template("change_email_success.html")

@auth.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        password = request.form.get('deleteaccountpassword')
        confirm_delete = request.form.get('confirmdeleteaccountpassword')
        if check_password_hash(current_user.password, password):
            if password == confirm_delete:
                email = current_user.email
                # send mail user's email to inform them that their account has been deleted
                msg = Message('Account Deleted', sender='behindthescreens.thesis@gmail.com', recipients=[email])
                msg.html = """
                    <html>
                    <head>
                        <style>
                            .email-content {{
                                margin: 20px;
                                padding: 20px;
                                background-color: #e5e7eb;
                            }}
                            .email-header {{
                                font-size: 24px;
                                line-height: 32px;
                                font-weight: 600;
                                color: #881337;
                                text-align: center;
                            }}
                            .email-body {{
                                font-weight: 500;
                                font-size: 18px;
                                line-height: 28px;
                                margin-top: 8px;
                                color: #4b5563;
                            }}
                            .email-footer {{
                                margin-top: 8px;
                                font-size: 14px;
                                line-height: 20px;
                                color: #fb7185;
                            }}
                            .text-center {{
                                text-align: center;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="email-outline">
                            <div class="text-center">
                                <div class="text-center">
                                <img src="https://pbs.twimg.com/media/GSYY7T8XsAALUY1?format=png&name=small" height="25%" viewBox="0 0 524.67004 531.39694">
                                </div>
                                <div class="email-header">Your Account Has Been Deleted</div>
                                <div class="email-body">
                                    Thank you for using our platform. We're sad to see you go! You have successfully deleted your account. <br> A reminder that you can always sign up again if you change your mind. <br>
                                    Behind the Screens is a platform that allows you to analyze the sentiment of YouTube comments.
                                </div>
                                <div class="email-footer">
                                    Once your account has been deleted, you can no longer retrieve it. This email is automated, please do not reply.
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                """.format()
                mail.send(msg)

                user_log(f"User {current_user.username} deleted their account")
                # Delete related rows from other tables
                db.session.query(WordCloudImage).filter_by(user_id=current_user.id).delete()
                db.session.query(SentimentCounter).filter_by(user_id=current_user.id).delete()
                db.session.query(FrequentWords).filter_by(user_id=current_user.id).delete()
                db.session.query(SummarizedComments).filter_by(user_id=current_user.id).delete()
                db.session.query(Comments).filter_by(user_id=current_user.id).delete()
                db.session.query(YoutubeUrl).filter_by(user_id=current_user.id).delete()
                # Delete the user
                db.session.delete(current_user)
                db.session.commit()
                return redirect(url_for('auth.home'))
            else:
                flash('Passwords do not match.', category='error')
        else:
            flash('Incorrect password.', category='error')

    return redirect(url_for('views.settings'))

logging.basicConfig(filename='app.log', level=logging.DEBUG)

@auth.route('/analyze', methods=['GET','POST'])
@login_required
def analyze():
    if request.method == 'POST':
        try:
            # get_url table as temporary storage for the url
            url = request.form.get('url')
            if not url:
                flash('Please enter a valid YouTube URL.', category='error')
                return redirect(url_for('views.main'))
            try:
                yt = YouTube(url)
                video_name = yt.title
                video_id = yt.video_id
            except Exception as e:
                flash(f'"{url}" is not a YouTube video. Please enter a valid URL.', category='error')
                # flash(f'Failed to extract video name: {str(e)}', category='error')
                return redirect(url_for('views.main'))
            attempt = "Failed" # default is failed, it will be changed to 'success' if it commits
            new_url = GetUrl(url=url, user_id=current_user.id, attempt=attempt)
            db.session.add(new_url)
            db.session.commit()
            user_log(f"Started analysis for video '{video_name}'")

            # THE FOLLOWING CODE BLOCK WILL ONLY BE COMMITTED WHEN THE ANALYSIS IS SUCCESSFUL
            # Adding the URL to the youtube_url table, youtube_url table's id is get_url's id if successful
            new_youtube_url = YoutubeUrl(id=new_url.id, url=url, user_id=current_user.id, video_name=video_name, video_id=video_id)
            db.session.add(new_youtube_url)

            # Extracting comments from YouTube video, FOR SOME REASON REPLIES ARE STILL INCLUDED
            filtered_comments = extract_comments(url)

            # Sentiment Analysis
            label_mapping = {
                "LABEL_0": "Negative",
                "LABEL_1": "Neutral",
                "LABEL_2": "Positive"
            }

            # Sentiment Analysis for each comment
            sentiments = []
            for comment in filtered_comments:
                try:
                    sentiment = sentiment_pipeline([comment])[0]
                    sentiment['label'] = label_mapping.get(sentiment['label'], sentiment['label'])
                    sentiments.append(sentiment)
                except RuntimeError as e: # This occurs because of the length of the comment. RoBERTa can only handle a maximum of 512 tokens.
                    continue  # Skip this comment and continue with the next one
                except Exception as e:
                    flash(f'An unexpected error occurred during sentiment analysis: {str(e)}', category='error')
                    return redirect(url_for('views.main'))
            
            # for sentiment counter
            positive_count = 0
            negative_count = 0
            neutral_count = 0

            # INSERT comments to Comments and Sentiments to Comments table in the database
            comment_objects = []
            all_comments_text = " ".join(filtered_comments)

            for comment, sentiment in zip(filtered_comments, sentiments):
                new_comment = Comments(
                    comment=comment,
                    sentiment=sentiment['label'],
                    url_id=new_youtube_url.id,
                    user_id=current_user.id
                )
                db.session.add(new_comment)
                comment_objects.append(new_comment)
                
                # Counting the sentiments
                if sentiment['label'] == 'Positive':
                    positive_count += 1
                elif sentiment['label'] == 'Negative':
                    negative_count += 1
                else:
                    neutral_count += 1

            # INSERT frequent words to FrequentWords table in the database
            cleaned_comments = clean_text(all_comments_text)
            word_count = Counter(word for word in cleaned_comments.split() if word not in stop_words)
            most_common_words = word_count.most_common(5)
            frequent_words_objects = []
            for word, count in most_common_words:
                word_sentiment_scores = sia.polarity_scores(word)
                compound_score = word_sentiment_scores['compound']
                if compound_score >= 0.05:
                    word_sentiment_label = "Positive"
                elif compound_score <= -0.05:
                    word_sentiment_label = "Negative"
                else:
                    word_sentiment_label = "Neutral"
                new_frequent_word = FrequentWords(word=word, count=count, sentiment=word_sentiment_label, url_id=new_youtube_url.id, user_id=current_user.id)
                db.session.add(new_frequent_word)
                frequent_words_objects.append(new_frequent_word)

            # GENERATE and INSERT SUMMARY
            summary = get_summary(all_comments_text)

            summarized_comment = SummarizedComments(summary=summary, url_id=new_youtube_url.id, user_id=current_user.id)
            db.session.add(summarized_comment)

            # INSERT the counts to the sentiment_counter table
            sentiment_counter = SentimentCounter(
                user_id=current_user.id,
                url_id=new_youtube_url.id,
                positive=positive_count,
                negative=negative_count,
                neutral=neutral_count
            )
            db.session.add(sentiment_counter)

            # WORD CLOUD
            unlabeled_words = word_tokenize(all_comments_text)

            # Generate the positive word cloud
            positive_words = [word for word in unlabeled_words if sia.polarity_scores(word)['compound'] > 0]
            positive_text = ' '.join(positive_words)
            positive_img_str = word_cloud(positive_text, 'winter')
            
            # Generate the negative word cloud
            negative_words = [word for word in unlabeled_words if sia.polarity_scores(word)['compound'] < 0]
            negative_text = ' '.join(negative_words)
            negative_img_str = word_cloud(negative_text, 'hot')

            if positive_img_str and negative_img_str:
                # Decode the base64 strings back to binary data
                positive_img_data = base64.b64decode(positive_img_str)
                negative_img_data = base64.b64decode(negative_img_str)
                
                wordcloud_image = WordCloudImage(
                    user_id=current_user.id,
                    url_id=new_youtube_url.id,
                    image_positive_data=positive_img_data,
                    image_negative_data=negative_img_data
                )
                db.session.add(wordcloud_image)
                
            successful_analysis = GetUrl.query.filter_by(url=url).order_by(GetUrl.id.desc()).first()
            successful_analysis.attempt = "Success"
            db.session.commit()
            user_log(f"Completed analysis for video '{video_name}'")

            return redirect(url_for('views.results', youtube_url_id=new_youtube_url.id, youtube_video_id=new_youtube_url.video_id))
        except Exception as e:
            current_app.logger.error(f'Error during analysis: {str(e)}')
            flash(f'An unexpected error occurred: {str(e)}', category='error')
            return redirect(url_for('views.main'))
    return render_template("analysis_interrupted.html", user=current_user)

@auth.route('/delete-item/<int:item_id>', methods=['DELETE'])
@login_required
def delete_analysis(item_id):
    # Check if the item exists and belongs to the current user
    youtube_url = YoutubeUrl.query.filter_by(id=item_id, user_id=current_user.id).first()
    
    if youtube_url:
        try:
            # Delete related entries in other tables
            db.session.query(Comments).filter_by(url_id=youtube_url.id).delete()
            db.session.query(SummarizedComments).filter_by(url_id=youtube_url.id).delete()
            db.session.query(FrequentWords).filter_by(url_id=youtube_url.id).delete()
            db.session.query(SentimentCounter).filter_by(url_id=youtube_url.id).delete()
            db.session.query(WordCloudImage).filter_by(url_id=youtube_url.id).delete()
            db.session.delete(youtube_url)
            db.session.commit()
            
            user_log(f"User {current_user.username} deleted video analysis with ID {item_id}")
            return jsonify({'message': 'Previous analysis deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error deleting Previous Analysis: {str(e)}')
            return jsonify({'error': 'Failed to delete Previous Analysis'}), 500
    else:
        return jsonify({'error': 'Analysis not found or unauthorized'}), 404

@auth.route('/analyze2', methods=['POST'])
def analyze2():
    data = request.get_json()
    youtube_url = data.get('url2')
    
    if not youtube_url:
        return jsonify({'error': 'Please enter a valid YouTube URL.'}), 400
    
    try:
        yt = YouTube(youtube_url)
        video_name = yt.title
    except Exception as e:
        return jsonify({'error': f'Failed to extract video name: {str(e)}'}), 400
    
    # Extract comments
    filtered_comments = extract_comments(youtube_url)

    # Sentiment Analysis
    label_mapping = {
        "LABEL_0": "Negative",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positive"
    }

    # Sentiment Analysis for each comment
    sentiments = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for comment in filtered_comments:
        try:
            sentiment = sentiment_pipeline([comment])[0]
            sentiment['label'] = label_mapping.get(sentiment['label'], sentiment['label'])
            sentiments.append({'comment': comment, 'sentiment': sentiment['label']})
        except RuntimeError as e:
            continue 
        except Exception as e:
            flash(f'An unexpected error occurred during sentiment analysis: {str(e)}', category='error')
            return redirect(url_for('views.home'))
        
        # Counting the sentiments
        if sentiment['label'] == 'Positive':
            positive_count += 1
        elif sentiment['label'] == 'Negative':
            negative_count += 1
        else:
            neutral_count += 1

    all_comments_text = " ".join(filtered_comments)
    cleaned_comments = clean_text(all_comments_text)
    word_count = Counter(word for word in cleaned_comments.split() if word not in stop_words)
    most_common_words = word_count.most_common(5)
    frequent_words = []
    for word, count in most_common_words:
        word_sentiment_scores = sia.polarity_scores(word)
        compound_score = word_sentiment_scores['compound']
        if compound_score >= 0.05:
            word_sentiment_label = "Positive"
        elif compound_score <= -0.05:
            word_sentiment_label = "Negative"
        else:
            word_sentiment_label = "Neutral"
        frequent_words.append([word, count, word_sentiment_label])

    summary = get_summary(all_comments_text)

    # Generate Word Clouds
    unlabeled_words = word_tokenize(all_comments_text)
    positive_words = [word for word in unlabeled_words if sia.polarity_scores(word)['compound'] > 0]
    positive_text = ' '.join(positive_words)
    positive_img_str = word_cloud(positive_text, 'winter')
    
    negative_words = [word for word in unlabeled_words if sia.polarity_scores(word)['compound'] < 0]
    negative_text = ' '.join(negative_words)
    negative_img_str = word_cloud(negative_text, 'hot')

    response = {
        'video_name2': video_name,
        'positive_count2': positive_count,
        'negative_count2': negative_count,
        'neutral_count2': neutral_count,
        'comments2': sentiments,
        'frequent_words2': frequent_words,
        'positive_img_str2': positive_img_str,
        'negative_img_str2': negative_img_str,
    }

    return jsonify(response), 200