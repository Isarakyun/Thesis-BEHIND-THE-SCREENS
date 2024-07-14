from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_migrate import Migrate

class YoutubeUrl(db.Model):
    __tablename__ = 'youtube_url'
    id = db.Column(db.Integer, primary_key=True)
    video_name = db.Column(db.String(150))
    url = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    comments = db.relationship('Comments')
    summarizedComments = db.relationship('SummarizedComments')
    labeledComments = db.relationship('LabeledComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')

class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(50000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    labeledComments = db.relationship('LabeledComments')

class SummarizedComments(db.Model):
    __tablename__ = 'summarized_comments'
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String(50000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class LabeledComments(db.Model):
    __tablename__ = 'labeled_comments'
    id = db.Column(db.Integer, primary_key=True)
    sentiment = db.Column(db.String(150))
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class FrequentWords(db.Model):
    __tablename__ = 'frequent_words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(150))
    count = db.Column(db.Integer)
    sentiment = db.Column(db.String(150))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class SentimentCounter(db.Model):
    __tablename__ = 'sentiment_counter'
    id = db.Column(db.Integer, primary_key=True)
    positive = db.Column(db.Integer)
    negative = db.Column(db.Integer)
    neutral = db.Column(db.Integer)
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    confirmed_email = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(150))
    profile_pic = db.Column(db.String(150), default='default.jpg')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    youtube_url = db.relationship('YoutubeUrl')
    comments = db.relationship('Comments')
    summarizedComments = db.relationship('SummarizedComments')
    labeledComments = db.relationship('LabeledComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')
