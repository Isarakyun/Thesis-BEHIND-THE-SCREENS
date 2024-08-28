from flask import redirect, url_for
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import base64
from nltk.probability import FreqDist
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from textblob import TextBlob
from youtube_comment_downloader import YoutubeCommentDownloader
import re
from nltk.stem import WordNetLemmatizer

def extract_comments(youtube_url):
    try:
        video_id = youtube_url.split('v=')[1]
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments(video_id)
        
        # Manually filter out replies
        top_level_comments = [comment['text'] for comment in comments if 'parent' not in comment]
        
        # Regular expression to match timestamps (e.g., "00:00", "1:23", "12:34:56") anywhere in the text
        timestamp_pattern = re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b')
        
        # Filter out comments that contain timestamps or "@" symbol
        filtered_comments = [comment for comment in top_level_comments if not timestamp_pattern.search(comment) and '@' not in comment]

        return filtered_comments

    except Exception as e:
        # flash(f'Failed to extract comments: {str(e)}', category='error')
        return redirect(url_for('views.main'))

lemmatizer = WordNetLemmatizer()
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    import nltk
    nltk.download('stopwords')
    
def clean_text(text):
    # Remove special characters
    text = re.sub(r'\W', ' ', text)
    # Remove single characters
    text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
    # Remove single characters from the start
    text = re.sub(r'\^[a-zA-Z]\s+', ' ', text) 
    # Substitute multiple spaces with single space
    text = re.sub(r'\s+', ' ', text, flags=re.I)
    # Remove prefixed 'b'
    text = re.sub(r'^b\s+', '', text)
    # Remove numbers
    text = re.sub(r'\d', '', text)
    # Convert to lowercase
    text = text.lower()
    # Split into words
    words = text.split()
    # Filter out short words and stopwords
    words = [word for word in words if len(word) > 3 and word not in stop_words]
    # Lemmatize the words
    words = [lemmatizer.lemmatize(word) for word in words]
    # Join the words back together
    text = ' '.join(words)
    return text

def get_summary(joined_comments):
    sentences = sent_tokenize(joined_comments)

    stop_words = set(stopwords.words("english"))
    preprocessed_sentences = []
    for sentence in sentences:
        words = word_tokenize(sentence)
        filtered_words = [
            word for word in words if word.lower() not in stop_words]
        preprocessed_sentences.append(filtered_words)

    flat_preprocessed_words = [
        word for sentence in preprocessed_sentences for word in sentence]
    word_freq = FreqDist(flat_preprocessed_words)

    sentence_scores = {}
    for i, sentence in enumerate(preprocessed_sentences):
        for word in sentence:
            if word in word_freq:
                if i in sentence_scores:
                    sentence_scores[i] += word_freq[word]
                else:
                    sentence_scores[i] = word_freq[word]

    summary_sentences = []
    if sentence_scores:
        sorted_scores = sorted(sentence_scores.items(),
                               key=lambda x: x[1], reverse=True)
        # Select the top 3 sentences as the summary
        top_sentences = sorted_scores[:3]
        for index, _ in top_sentences:
            summary_sentences.append(sentences[index])

    # Join the summary sentences to create the final summary
    summary = ' '.join(summary_sentences)
    return summary

# def analyze_summary(text):
#     analysis = TextBlob(text)
#     sentiment_score = analysis.sentiment.polarity
#     if sentiment_score > 0.1:
#         sentiment = "Positive"
#     elif sentiment_score < -0.1:
#         sentiment = "Negative"
#     else:
#         sentiment = "Neutral"
#     return sentiment, sentiment_score

def word_cloud(words, colormap):
    stopwords = set(STOPWORDS)
    if not words:
        return None
    wordcloud = WordCloud(max_font_size=100, max_words=50, width=800, height=400, background_color='white', stopwords=stopwords, colormap=colormap).generate(words)
    img = wordcloud.to_image()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)  # Ensure the buffer is at the beginning
    return base64.b64encode(buffer.getvalue()).decode('utf-8')