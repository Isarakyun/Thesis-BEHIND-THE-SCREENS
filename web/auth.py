from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message
from random import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from .models import User, YoutubeUrl, Comments, SummarizedComments, FrequentWords, SentimentCounter, WordCloudImage
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .analysis import clean_text, word_cloud, get_summary, extract_comments
from flask_login import login_user, login_required, logout_user, current_user
from pytube import YouTube
from transformers import pipeline
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
from collections import Counter
import base64

auth = Blueprint('auth', __name__)

mail = Mail()
s = URLSafeTimedSerializer('SECRET_KEY')
MODEL = 'cardiffnlp/twitter-roberta-base-sentiment'
sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL)
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
stop_words = set(stopwords.words('english'))
sia = SentimentIntensityAnalyzer()

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

    return redirect(url_for('views.results', youtube_url_id=new_youtube_url.id))

@auth.route('/analyze-home', methods=['POST'])
def analyze_home():
    youtube_url = request.form.get('youtube_url')
    if youtube_url:
        playlist_id = extract_playlist_id(youtube_url)
        if playlist_id:
            # Assuming you have a function to process the URL and analyze comments
            api_key = "AIzaSyDUyMia8oNCLvvKR3KEOBesQ6m_40U9b58"
            csv_file = 'comments_data.csv'
            output_csv_file = 'VADERs_sentiment_analysis_results.csv'

            fetch_youtube_comments(api_key, [playlist_id], csv_file)
            analyze_youtube_comments(csv_file, output_csv_file)

            # Redirect to results2.html with the necessary data
            return redirect(url_for('views.results2', youtube_url=youtube_url))
    return redirect(url_for('views.home'))