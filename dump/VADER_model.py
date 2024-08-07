import re

def extract_playlist_id(youtube_url):
    match = re.search(r'list=([a-zA-Z0-9_-]+)', youtube_url)
    if match:
        return match.group(1)
    return None

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from tqdm import tqdm
from nltk.sentiment import SentimentIntensityAnalyzer
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
import re

plt.style.use('ggplot')

import nltk

# Uncomment the lines below if you haven't downloaded NLTK resources
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')
# nltk.download('movie_reviews')
# nltk.download('treebank')
# nltk.download('sentiwordnet')
# nltk.download('omw')
# nltk.download('universal_tagset')
# nltk.download('vader_lexicon')

def extract_playlist_id(youtube_url):
    match = re.search(r'list=([a-zA-Z0-9_-]+)', youtube_url)
    if match:
        return match.group(1)
    return None

def perform_sentiment_analysis(comments):
    """
    Perform sentiment analysis on YouTube video comments.

    Parameters:
    - comments: List of strings containing YouTube comments.

    Returns:
    - results: List of dictionaries containing sentiment analysis results for each comment.
    """
    sia = SentimentIntensityAnalyzer()
    results = []
    for comment in tqdm(comments, desc="Analyzing Comments"):
        # Add a check to ensure comment is a non-null string
        if isinstance(comment, str):
            score = sia.polarity_scores(comment)
            sentiment = get_sentiment(score['compound'])
            results.append({'comment': comment, 'sentiment_score': score, 'sentiment': sentiment})
    return results

def get_sentiment(score):
    if score < -0.05:
        return 'Negative'
    elif score > 0.05:
        return 'Positive'
    else:
        return 'Neutral'

# Fetching YouTube comments
def fetch_youtube_comments(api_key, playlist_ids, csv_file):
    youtube = build('youtube', 'v3', developerKey=api_key)

    def get_all_video_ids_from_playlists(youtube, playlist_ids):
        all_videos = []  # Initialize a single list to hold all video IDs

        for playlist_id in playlist_ids:
            next_page_token = None

            # Fetch videos from the current playlist
            while True:
                playlist_request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token)
                playlist_response = playlist_request.execute()

                all_videos += [item['contentDetails']['videoId'] for item in playlist_response['items']]

                next_page_token = playlist_response.get('nextPageToken')

                if next_page_token is None:
                    break

        return all_videos

    def get_comments_for_video(youtube, video_id):
        all_comments = []
        next_page_token = None

        while True:
            comment_request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                pageToken=next_page_token,
                textFormat="plainText",
                maxResults=100
            )
            comment_response = comment_request.execute()

            for item in comment_response['items']:
                top_comment = item['snippet']['topLevelComment']['snippet']
                all_comments.append({
                    'Timestamp': top_comment['publishedAt'],
                    'Username': top_comment['authorDisplayName'],
                    'VideoID': video_id,  # Directly using video_id from function parameter
                    'Comment': top_comment['textDisplay'],
                    'Date': top_comment['updatedAt'] if 'updatedAt' in top_comment else top_comment['publishedAt']
                })

            next_page_token = comment_response.get('nextPageToken')
            if not next_page_token:
                break

        return all_comments

    video_ids = get_all_video_ids_from_playlists(youtube, playlist_ids)

    all_comments = []

    for video_id in video_ids:
        video_comments = get_comments_for_video(youtube, video_id)
        all_comments.extend(video_comments)

    comments_df = pd.DataFrame(all_comments)
    comments_df.to_csv(csv_file, index=False)

    return comments_df

# Sentiment analysis on YouTube comments
def analyze_youtube_comments(csv_file, output_csv_file):
    df = pd.read_csv(csv_file)
    youtube_comments = df['Comment'].tolist()
    results = perform_sentiment_analysis(youtube_comments)
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_csv_file, index=False)
    return output_df

# Read comments from CSV
def read_comments_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    comments = df['Comment'].tolist()
    return comments

# Initialize Flask app
app = Flask(__name__)

# Define endpoint for sentiment analysis
@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    # Extract comments from request
    data = request.json
    comments = data.get('comments', [])

    # If comments are not provided in the request, read them from the CSV file
    if not comments:
        comments = read_comments_from_csv('comments_data.csv')

    # Perform sentiment analysis on comments
    results = perform_sentiment_analysis(comments)

    return jsonify(results)

if __name__ == '__main__':
    # Run Flask app
    app.run(debug=True)
