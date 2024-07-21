from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from flask_login import login_required, current_user
from flask import session
from . import db
from sqlalchemy.orm import joinedload
from .models import User, YoutubeUrl, Comments, SummarizedComments, LabeledComments, FrequentWords, SentimentCounter, WordCloudImage
import re
import sys
import os
import base64

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(sys.path)  # Debug print to check the system path

# Import the vader_model functions from the parent directory
from VADER_model import fetch_youtube_comments, analyze_youtube_comments

views = Blueprint('views', __name__)

def get_youtube_url_by_id(url_id):
    return db.session.query(YoutubeUrl).filter_by(id=url_id).first()

@views.route('/api/sentiment/<int:url_id>')
def get_sentiment_data(url_id):
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
    return render_template("main.html", user=current_user, youtube_urls=youtube_urls)

@views.route('/results')
@login_required
def results():
    user_id = current_user.id
    youtubeurl = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).first()
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).all()
    wordcloud = WordCloudImage.query.filter_by(url_id=youtubeurl.id).first()
    summarized_comments = SummarizedComments.query.filter_by(url_id=youtubeurl.id).order_by(SummarizedComments.url_id.desc()).first()
    frequent_words = FrequentWords.query.filter_by(user_id=user_id, url_id=youtubeurl.id).order_by(FrequentWords.url_id.desc()).all()
    sentiment_counter = SentimentCounter.query.filter_by(url_id=youtubeurl.id).order_by(SentimentCounter.url_id.desc()).first()
    
    comments_sentiment = db.session.query(Comments, LabeledComments).join(
        LabeledComments, Comments.id == LabeledComments.comments_id
        ).filter(
            Comments.url_id == youtubeurl.id,
            Comments.user_id == user_id,
            LabeledComments.url_id == youtubeurl.id,
            LabeledComments.user_id == user_id
        ).all()
    
    # Process the combined data if needed
    sentiment_analysis = [
        {
            'comment': comment.comment,
            'comment_id': comment.id,
            'sentiment': labeled_comment.sentiment,
            'url_id': comment.url_id,
            'user_id': comment.user_id
        }
        for comment, labeled_comment in comments_sentiment
    ]

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

    return render_template("results.html", user=current_user, youtube_url=youtubeurl, youtube_urls=youtube_urls, sentiment_analysis=sentiment_analysis, summarized_comments=summarized_comments, frequent_words=frequent_words, sentiment_counter=sentiment_counter, image_positive_data=image_positive_data_base64, image_negative_data=image_negative_data_base64)

@views.route('/sessions/<int:youtube_url_id>')
@login_required
def sessions(youtube_url_id):
    user_id = current_user.id
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).all()
    youtubeurl = get_youtube_url_by_id(youtube_url_id)
    summary = db.session.query(SummarizedComments).filter_by(url_id=youtube_url_id).first()
    count = db.session.query(SentimentCounter).filter_by(url_id=youtube_url_id).first()
    wordcloud = WordCloudImage.query.filter_by(url_id=youtube_url_id).first()

    if summary:
        summary_text = summary.summary
    else:
        summary_text = 'No summary found'

    comments_sentiment = db.session.query(Comments, LabeledComments).join(
        LabeledComments, Comments.id == LabeledComments.comments_id
        ).filter(
            Comments.url_id == youtube_url_id,
            Comments.user_id == user_id,
            LabeledComments.url_id == youtube_url_id,
            LabeledComments.user_id == user_id
        ).all()
    
    # Process the combined data if needed
    sentiment_analysis = [
        {
            'comment': comment.comment,
            'comment_id': comment.id,
            'sentiment': labeled_comment.sentiment,
            'url_id': comment.url_id,
            'user_id': comment.user_id
        }
        for comment, labeled_comment in comments_sentiment
    ]
    
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

    return render_template("previous_sessions.html", user=current_user, youtube_url=youtubeurl, youtube_urls=youtube_urls, summary=summary_text, count=count, frequent_words=frequent_words, sentiment_analysis=sentiment_analysis, image_positive_data=image_positive_data_base64, image_negative_data=image_negative_data_base64)

@views.route('/settings')
@login_required
def settings():
    return render_template("user_settings.html", user=current_user)

@views.route('/admin')
# @login_required
def admin():
    return render_template("admin.html")

# @views.route('/analyze-youtube', methods=['POST'])
# def analyze_youtube():
#     youtube_url = request.form.get('youtube_url')
#     if youtube_url:
#         playlist_id = extract_playlist_id(youtube_url)
#         if playlist_id:
#             # Hardcoded YouTube API key - replace this with a secure method to store keys
#             api_key = "AIzaSyDUyMia8oNCLvvKR3KEOBesQ6m_40U9b58"
#             csv_file = 'comments_data.csv'
#             output_csv_file = 'VADERs_sentiment_analysis_results.csv'

#             fetch_youtube_comments(api_key, [playlist_id], csv_file)
#             analyze_youtube_comments(csv_file, output_csv_file)
            
#             return redirect(url_for('views.home'))
#     return redirect(url_for('views.home'))

@views.route('/mail-sent')
def mail_sent():
    return render_template("mail_sent.html")

@views.route('password-reset-success')
def password_reset_success():
    return render_template("reset_password_success.html")

@views.route('/useragreement')
def user_agreement():
    return render_template('user_agreement.html', user=current_user)

@views.route('/about-us')
def about_us():
    return render_template('about_us.html', user=current_user)

# This route is for testing pages
@views.route('/test')
def test():
    # Assuming you have a way to get the user from the session or some other method
    user = session.get('user')  # Retrieve the user object from the session
    return render_template('test.html', user=user)