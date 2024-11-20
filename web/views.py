from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from flask_login import login_required, current_user
from flask import session
from . import db
from sqlalchemy.orm import joinedload, aliased
from .models import Users, YoutubeUrl, Comments, FrequentWords, SentimentCounter, WordCloudImage, HighScoreComments
import sys
import os
import matplotlib.pyplot as plt
import io
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

# BAR CHART FOR THE PDF DOWNLOAD LOL
@views.route('/bar-chart/<int:url_id>$<string:video_id>')
def bar_chart(url_id, video_id):
    response = get_sentiment_data(url_id, video_id)
    data = response.get_json()

    labels = ['Negative', 'Positive', 'Neutral']
    values = [data['negative'], data['positive'], data['neutral']]
    colors = ['#b91c1c', '#1d4ed8', '#fbbf24']

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=colors)
    ax.set_ylabel('Number of Comments')
    ax.set_title('Number of Comments Based on Sentiment')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')

@views.route('/')
def home():
    # return render_template("home_analysis.html", created_at=None, positive_count=None, negative_count=None, neutral_count=None, comments=None, frequent_words=None, user=current_user)
    return render_template("home.html", user=current_user)

@views.route('/main')
@login_required
def main():
    user_id = current_user.id 
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.id.desc()).all()
    analysis_checker = WordCloudImage.query.filter_by(user_id=user_id).order_by(WordCloudImage.id.desc()).all()
    return render_template("main.html", user=current_user, youtube_urls=youtube_urls, analysis_checker=analysis_checker)

@views.route('/result/<int:youtube_url_id>$<string:youtube_video_id>')
@login_required
def results(youtube_url_id, youtube_video_id):
    user_id = current_user.id
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.id.desc()).all()
    youtubeurl = get_youtube_url_by_id(youtube_url_id)
    count = db.session.query(SentimentCounter).filter_by(url_id=youtube_url_id).first()
    wordcloud = WordCloudImage.query.filter_by(url_id=youtube_url_id).first()
    comments = Comments.query.filter_by(user_id=user_id, url_id=youtube_url_id).all()
    highscorecomments = HighScoreComments.query.filter_by(user_id=user_id, url_id=youtube_url_id).first()
    analysis_checker = WordCloudImage.query.filter_by(user_id=user_id).order_by(WordCloudImage.id.desc()).all()
    frequent_words = FrequentWords.query.filter_by(user_id=user_id, url_id=youtube_url_id).order_by(FrequentWords.url_id.desc()).all()

    if wordcloud and wordcloud.image_positive_data:
        image_positive_data = wordcloud.image_positive_data
    else:
        image_positive_data = None

    if wordcloud and wordcloud.image_negative_data:
        image_negative_data = wordcloud.image_negative_data
    else:
        image_negative_data = None

    return render_template("results.html", user=current_user, youtube_url=youtubeurl, youtube_urls=youtube_urls, count=count, frequent_words=frequent_words, comments=comments, image_positive_data=image_positive_data, image_negative_data=image_negative_data, analysis_checker=analysis_checker, highscorecomments=highscorecomments)

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

@views.route('/pdf-view/<int:youtube_url_id>$<string:youtube_video_id>')
@login_required
def pdf_template(youtube_url_id, youtube_video_id):
    user_id = current_user.id
    youtube_urls = YoutubeUrl.query.filter_by(user_id=user_id).order_by(YoutubeUrl.created_at.desc()).all()
    youtubeurl = get_youtube_url_by_id(youtube_url_id)
    count = db.session.query(SentimentCounter).filter_by(url_id=youtube_url_id).first()
    wordcloud = WordCloudImage.query.filter_by(url_id=youtube_url_id).first()
    comments = Comments.query.filter_by(user_id=user_id, url_id=youtube_url_id).all()
    highscorecomments = HighScoreComments.query.filter_by(user_id=user_id, url_id=youtube_url_id).first()
    analysis_checker = WordCloudImage.query.filter_by(user_id=user_id).order_by(WordCloudImage.id.desc()).all()
    frequent_words = FrequentWords.query.filter_by(user_id=user_id, url_id=youtube_url_id).order_by(FrequentWords.url_id.desc()).all()

    if wordcloud and wordcloud.image_positive_data:
        image_positive_data = wordcloud.image_positive_data
    else:
        image_positive_data = None

    if wordcloud and wordcloud.image_negative_data:
        image_negative_data = wordcloud.image_negative_data
    else:
        image_negative_data = None

    return render_template("pdf_template.html", user=current_user, youtube_url=youtubeurl, youtube_urls=youtube_urls, count=count, frequent_words=frequent_words, comments=comments, image_positive_data=image_positive_data, image_negative_data=image_negative_data, analysis_checker=analysis_checker, highscorecomments=highscorecomments)

# ERROR HANDLING PAGES
@views.app_errorhandler(404)
def page_not_found(e):
    return render_template('404NotFound.html', user=current_user), 404

@views.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500InternalServerError.html', user=current_user), 500

@views.app_errorhandler(403)
def forbidden(e):
    return render_template('403Forbidden.html', user=current_user), 403

@views.app_errorhandler(405)
def method_not_allowed(e):
    return render_template('405MethodNotAllowed.html', user=current_user), 405

@views.app_errorhandler(408)
def request_timeout(e):
    return render_template('408RequestTimeout.html', user=current_user), 408

@views.app_errorhandler(429)
def too_many_requests(e):
    return render_template('429TooManyRequests.html', user=current_user), 429

@views.app_errorhandler(400)
def bad_request(e):
    return render_template('400BadRequest.html', user=current_user), 400

@views.app_errorhandler(401)
def unauthorized(e):
    return render_template('401Unauthorized.html', user=current_user), 401

@views.app_errorhandler(501)
def not_implemented(e):
    return render_template('501NotImplemented.html', user=current_user), 501

@views.app_errorhandler(502)
def bad_gateway(e):
    return render_template('502BadGateway.html', user=current_user), 502

@views.app_errorhandler(503)
def service_unavailable(e):
    return render_template('503ServiceUnavailable.html', user=current_user), 503

@views.app_errorhandler(504)
def gateway_timeout(e):
    return render_template('504GatewayTimeout.html', user=current_user), 504

@views.app_errorhandler(505)
def http_version_not_supported(e):
    return render_template('505HTTPVersionNotSupported.html', user=current_user), 505

