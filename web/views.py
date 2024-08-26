from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import login_required, current_user
from flask import session
from . import db
from sqlalchemy.orm import joinedload, aliased
from .models import User, YoutubeUrl, Comments, SummarizedComments, FrequentWords, SentimentCounter, WordCloudImage
import sys
import os
import base64
import json

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(sys.path)  # Debug print to check the system path

views = Blueprint('views', __name__)

def get_youtube_url_by_id(url_id):
    return db.session.query(YoutubeUrl).filter_by(id=url_id).first()

@views.route('/api/sentiment/<int:url_id>$<string:video_id>')
def get_sentiment_data(url_id, video_id):
    sentiment = db.session.query(SentimentCounter).filter_by(url_id=url_id).first()
    if sentiment:
        data = {
            'positive': sentiment.positive,
            'negative': sentiment.negative,
            'neutral': sentiment.neutral
        }
    else:
        data = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
    return jsonify(data)

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/main')
@login_required
def main():
    user_id = current_user.id 
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).all()
    analysis_checker = WordCloudImage.query.filter_by(user_id=user_id).order_by(WordCloudImage.id.desc()).all()
    return render_template("main.html", user=current_user, youtube_urls=youtube_urls, analysis_checker=analysis_checker)

@views.route('/result/<int:youtube_url_id>$<string:youtube_video_id>')
@login_required
def results(youtube_url_id, youtube_video_id):
    user_id = current_user.id
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).all()
    youtubeurl = get_youtube_url_by_id(youtube_url_id)
    summary = db.session.query(SummarizedComments).filter_by(url_id=youtube_url_id).first()
    count = db.session.query(SentimentCounter).filter_by(url_id=youtube_url_id).first()
    wordcloud = WordCloudImage.query.filter_by(url_id=youtube_url_id).first()
    comments = Comments.query.filter_by(user_id=user_id, url_id=youtube_url_id).all()
    analysis_checker = WordCloudImage.query.filter_by(user_id=user_id).order_by(WordCloudImage.id.desc()).all()

    if summary:
        summary_text = summary.summary
    else:
        summary_text = 'No summary found'
    
    frequent_words = FrequentWords.query.filter_by(user_id=user_id, url_id=youtube_url_id).order_by(FrequentWords.url_id.desc()).all()
    
    # Encode positive word cloud image data in Base64
    if wordcloud and wordcloud.image_positive_data:
        image_positive_data_base64 = base64.b64encode(wordcloud.image_positive_data).decode('utf-8')
    else:
        image_positive_data_base64 = None

    # Encode negative word cloud image data in Base64
    if wordcloud and wordcloud.image_negative_data:
        image_negative_data_base64 = base64.b64encode(wordcloud.image_negative_data).decode('utf-8')
    else:
        image_negative_data_base64 = None

    return render_template("results.html", user=current_user, youtube_url=youtubeurl, youtube_urls=youtube_urls, summary=summary_text, count=count, frequent_words=frequent_words, comments=comments, image_positive_data=image_positive_data_base64, image_negative_data=image_negative_data_base64, analysis_checker=analysis_checker)

@views.route('/settings')
@login_required
def settings():
    user_id = current_user.id
    username = current_user.username
    email = current_user.email
    confirmed_email = current_user.confirmed_email
    return render_template("user_settings.html", user=current_user, username=username, email=email, user_id=user_id, confirmed_email=confirmed_email)

@views.route('/mail-sent')
def mail_sent():
    return render_template("mail_sent.html")

@views.route('password-reset-success')
def password_reset_success():
    return render_template("reset_password_success.html")

@views.route('/user-agreement')
def user_agreement():
    return render_template('user_agreement.html', user=current_user)

@views.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html', user=current_user)

@views.route('/about-us')
def about_us():
    return render_template('about_us.html', user=current_user)

@views.route('/results2')
def results2():
    youtube_url2 = request.args.get('youtube_url2')
    video_name2 = request.args.get('video_name2')
    positive_count2 = int(request.args.get('positive_count2', 0))
    negative_count2 = int(request.args.get('negative_count2', 0))
    neutral_count2 = int(request.args.get('neutral_count2', 0))
    summary2 = request.args.get('summary2', '')
    frequent_words2 = json.loads(request.args.get('frequent_words2', '[]'))
    comments2 = json.loads(request.args.get('comments2', '[]'))
    positive_img_str2 = request.args.get('positive_img_str2', '')
    negative_img_str2 = request.args.get('negative_img_str2', '')

    return render_template('results2.html', 
                           youtube_url2=youtube_url2, 
                           video_name2=video_name2,
                           positive_count2=positive_count2, 
                           negative_count2=negative_count2, 
                           neutral_count2=neutral_count2,
                           summary2=summary2,
                           frequent_words2=frequent_words2,
                           comments2=comments2,
                           positive_img_str2=positive_img_str2,
                           negative_img_str2=negative_img_str2)

@views.app_errorhandler(404)
def page_not_found(e):
    return render_template('404NotFound.html', user=current_user), 404

# This route is for testing pages
@views.route('/test')
def test():
    user = session.get('user') 
    return render_template('404NotFound.html', user=user)

