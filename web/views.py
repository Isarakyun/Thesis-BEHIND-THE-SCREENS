from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
import re
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(sys.path)  # Debug print to check the system path

# Import the vader_model functions from the parent directory
from VADER_model import fetch_youtube_comments, analyze_youtube_comments

views = Blueprint('views', __name__)

def extract_playlist_id(youtube_url):
    match = re.search(r'list=([a-zA-Z0-9_-]+)', youtube_url)
    if match:
        return match.group(1)
    return None

@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/main')
@login_required
def main():
    return render_template("main.html", user=current_user)

@views.route('/results')
@login_required
def results():
    return render_template("results.html", user=current_user)

@views.route('/settings')
@login_required
def settings():
    return render_template("accountsettings.html", user=current_user)

@views.route('/admin')
# @login_required
def admin():
    return render_template("admin.html")

@views.route('/analyze-youtube', methods=['POST'])
def analyze_youtube():
    youtube_url = request.form.get('youtube_url')
    if youtube_url:
        playlist_id = extract_playlist_id(youtube_url)
        if playlist_id:
            # Hardcoded YouTube API key - replace this with a secure method to store keys
            api_key = "AIzaSyDUyMia8oNCLvvKR3KEOBesQ6m_40U9b58"
            csv_file = 'comments_data.csv'
            output_csv_file = 'VADERs_sentiment_analysis_results.csv'

            fetch_youtube_comments(api_key, [playlist_id], csv_file)
            analyze_youtube_comments(csv_file, output_csv_file)
            
            return redirect(url_for('views.home'))
    return redirect(url_for('views.home'))

@views.route('/accountsettings')

def accountsettings():
    return render_template('accountsettings.html', user=current_user)
