from flask_dance.contrib.google import make_google_blueprint, google
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_mail import Mail, Message
from random import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from .models import User, Admin, YoutubeUrl, Comments, SummarizedComments, FrequentWords, SentimentCounter, WordCloudImage, AuditTrail
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .analysis import clean_text, word_cloud, get_summary, extract_comments, analyze_summary
from flask_login import login_user, login_required, logout_user, current_user
from pytube import YouTube
from transformers import pipeline
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from collections import Counter
import base64
import os


auth = Blueprint('auth', __name__)

# Google OAuth configuration
# google_bp = make_google_blueprint(
#     client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
#     client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
#     redirect_to='auth.google_login'
# )
# auth.register_blueprint(google_bp, url_prefix='/google')

# Initialize extensions
mail = Mail()
s = URLSafeTimedSerializer('SECRET_KEY')
MODEL = 'cardiffnlp/twitter-roberta-base-sentiment'
sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL)
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
stop_words = set(stopwords.words('english'))
sia = SentimentIntensityAnalyzer()

# Audit Trail Logger
def log_audit_trail(action):
    if current_user.is_authenticated:
        user_id = current_user.id
        audit_trail = AuditTrail(user_id=user_id, action=action)
        db.session.add(audit_trail)
        db.session.commit()


# @auth.route('/google-login')
# def google_login():
#     print("In google_login route")
#     if not google.authorized:
#         print("User not authorized, redirecting to Google login")
#         redirect_uri = url_for('google.login')
#         print("Redirect URI: ", redirect_uri)
#         return redirect(redirect_uri)
    
#     resp = google.get('/plus/v1/people/me')
#     assert resp.ok, resp.text
#     google_info = resp.json()
#     email = google_info['emails'][0]['value']
#     username = google_info['displayName']

#     user = User.query.filter_by(email=email).first()
#     if user is None:
#         user = User(username=username, email=email, confirmed_email=True)
#         db.session.add(user)
#         db.session.commit()
#     login_user(user)
#     log_audit_trail(f"User {username} logged in with Google")
#     return redirect(url_for('views.main'))

# print("Google Client ID:", os.getenv('GOOGLE_OAUTH_CLIENT_ID'))
# print("Google Client Secret:", os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Attempting login with email: {email}")

        # Check if the user is an admin
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            print(f"Admin user found: {admin.email}")
            if admin.password == password:  # Compare plaintext passwords
                # print("Admin password correct")
                login_user(admin)
                log_audit_trail("Logged in")
                return redirect(url_for('admin.dashboard'))
            else:
                # print("Admin password incorrect")
                flash('Incorrect password, try again.', category='error')

        user = User.query.filter_by(email=email).first()
        if user:
            # print(f"User found: {user.email}")
            if check_password_hash(user.password, password):
                # print("User password correct")
                login_user(user, remember=True)
                log_audit_trail("Logged in")
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
    log_audit_trail("Logged out")  # Simplify the logout action message
    logout_user()
    flash('Logged out successfully!', 'success')
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
            log_audit_trail(f"User {username} signed up")

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
    log_audit_trail(f"User {user.username} confirmed email")

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
        log_audit_trail(f"User {user.username} requested password reset")
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
                log_audit_trail(f"User {user.username} reset password")
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
                    log_audit_trail(f"User {current_user.username} changed password")
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
            log_audit_trail(f"User '{old_username}' changed username to '{new_username}'")
            flash('Username changed successfully!', category='success')
            return redirect(url_for('views.settings'))
    return render_template("user_settings.html")

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
        else:
            current_user.confirmed_email = False
            current_user.email = new_email
            db.session.commit()
            log_audit_trail(f"User '{old_email}' changed email to '{new_email}'")
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
    log_audit_trail(f"User {current_user.username} confirmed change of email to {email}")
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
                log_audit_trail(f"User {current_user.username} deleted account")
                return redirect(url_for('auth.home'))
            else:
                flash('Passwords do not match.', category='error')
        else:
            flash('Incorrect password.', category='error')

    return redirect(url_for('views.settings'))

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
    log_audit_trail(f"Started analysis for video '{video_name}'")

    # Extracting comments from YouTube video, FOR SOME REASON REPLIES ARE STILL INCLUDED
    filtered_comments = extract_comments(youtube_url)

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
    db.session.commit()
    log_audit_trail(f"Completed analysis for video '{video_name}'")

    return redirect(url_for('views.results', youtube_url_id=new_youtube_url.id))


import logging

from flask import jsonify, request

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

    positive_count = 0
    negative_count = 0
    neutral_count = 0

    comments_data = []
    for comment in filtered_comments:
        sentiment_label, sentiment_score = analyze_summary(comment)
        comments_data.append({'comment': comment, 'sentiment': sentiment_label})
        if sentiment_label == 'Positive':
            positive_count += 1
        elif sentiment_label == 'Negative':
            negative_count += 1
        else:
            neutral_count += 1

    all_comments_text = " ".join(filtered_comments)
    cleaned_comments = clean_text(all_comments_text)
    word_count = Counter(word for word in cleaned_comments.split() if word not in stop_words)
    most_common_words = word_count.most_common(5)
    frequent_words = []
    for word, count in most_common_words:
        word_sentiment_label, _ = analyze_summary(word)
        frequent_words.append([word, count, word_sentiment_label])

    summary = get_summary(all_comments_text)

    # Generate Word Clouds
    unlabeled_words = word_tokenize(all_comments_text)
    positive_words = [word for word in unlabeled_words if analyze_summary(word)[0] == 'Positive']
    positive_text = ' '.join(positive_words)
    positive_img_str = word_cloud(positive_text, 'winter')
    
    negative_words = [word for word in unlabeled_words if analyze_summary(word)[0] == 'Negative']
    negative_text = ' '.join(negative_words)
    negative_img_str = word_cloud(negative_text, 'hot')

    response = {
        'video_name2': video_name,
        'positive_count2': positive_count,
        'negative_count2': negative_count,
        'neutral_count2': neutral_count,
        'comments2': comments_data,
        'frequent_words2': frequent_words,
        'positive_img_str2': positive_img_str,
        'negative_img_str2': negative_img_str,
    }

    return jsonify(response), 200
