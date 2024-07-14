from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message
from random import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from .models import User, YoutubeUrl, Comments, LabeledComments
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from pytube import YouTube
from transformers import pipeline
from youtube_comment_downloader import YoutubeCommentDownloader

auth = Blueprint('auth', __name__)
# app = Flask(__name__)
# app.config.from_pyfile('config.cfg')
mail = Mail()
s = URLSafeTimedSerializer('SECRET_KEY')
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                # flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.main'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))

@auth.route('/')
def home():
    return render_template("home.html")

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
        elif len(email) < 4:
            flash('Email must be valid.', category='error')
        elif password != confirmpassword:
            flash('Passwords don\'t match.', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters.', category='error')
        else:
            new_user = User(username=username, email=email, confirmed_email=False, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

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
        # return 'The token is expired!'
        return render_template("expired_url.html")
    except BadTimeSignature:
        # return 'The token is invalid!'
        return render_template("invalid_url.html")
    user = User.query.filter_by(email=email).first()
    user.confirmed_email = True
    db.session.commit()

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
            elif len(password) < 8:
                flash('Password must be at least 8 characters.', category='error')
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
                return redirect(url_for('views.password_reset_success'))
    except  SignatureExpired:
        # return 'The token is expired!'
        return render_template("expired_url.html")
    except BadTimeSignature:
        # return 'The token is invalid!'
        return render_template("invalid_url.html")
    
    return render_template("reset_password.html")

@auth.route('/analyze', methods=['POST'])
@login_required
def analyze():
    youtube_url = request.form.get('url')
    # Saving YouTube URL to youtube_url table in the database
    if not youtube_url:
        flash('Please enter a valid YouTube URL.', category='error')
        return redirect(url_for('views.main'))
    try:
        yt = YouTube(youtube_url)
        video_name = yt.title
    except Exception as e:
        flash(f'Failed to extract video name: {str(e)}', category='error')
        return redirect(url_for('views.main'))
    new_youtube_url = YoutubeUrl(url=youtube_url, user_id=current_user.id, video_name=video_name)
    db.session.add(new_youtube_url)
    db.session.commit()

    # Extracting comments from YouTube video
    try:
        video_id = youtube_url.split('v=')[1]
        downloader = YoutubeCommentDownloader()
        comments = [comment['text'] for comment in downloader.get_comments(video_id)]
    except Exception as e:
        flash(f'Failed to extract comments: {str(e)}', category='error')
        return redirect(url_for('views.main'))

    # Sentiment Analysis
    label_mapping = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive"
    }

    sentiments = []
    for comment in comments:
        try:
            sentiment = sentiment_pipeline([comment])[0]
            sentiment['label'] = label_mapping.get(sentiment['label'], sentiment['label'])
            sentiments.append(sentiment)
        except RuntimeError as e:
            flash(f'Sentiment analysis failed for a comment: {str(e)}', category='warning')
            continue  # Skip this comment and continue with the next one
        except Exception as e:
            flash(f'An unexpected error occurred during sentiment analysis: {str(e)}', category='error')
            return redirect(url_for('views.main'))

    # Saving comments to Comments table in the database
    comment_objects = []
    for comment in comments:
        new_comment = Comments(comment=comment, url_id=new_youtube_url.id, user_id=current_user.id)
        db.session.add(new_comment)
        comment_objects.append(new_comment)
    db.session.commit()

    # Saving sentiment analysis results to Labeled_Comments table in the database
    for comment_obj, sentiment in zip(comment_objects, sentiments):
        new_labeled_comment = LabeledComments(
            sentiment=sentiment['label'],
            comments_id=comment_obj.id,
            url_id=new_youtube_url.id,
            user_id=current_user.id
        )
        db.session.add(new_labeled_comment)
    db.session.commit()

    return redirect(url_for('views.results'))