from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class YoutubeUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    comments = db.relationship('Comments')

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(50000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    summarizedComments = db.relationship('SummarizedComments')
    labeledComments = db.relationship('LabeledComments')

class SummarizedComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String(50000))
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class LabeledComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sentiment = db.Column(db.String(150))
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')

class FrequentWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(150))
    count = db.Column(db.Integer)
    sentiment = db.Column(db.String(150))
    labeledComments_id = db.Column(db.Integer, db.ForeignKey('labeled_comments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class SentimentCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    positive = db.Column(db.Integer)
    negative = db.Column(db.Integer)
    neutral = db.Column(db.Integer)
    labeledComments_id = db.Column(db.Integer, db.ForeignKey('labeled_comments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    profile_pic = db.Column(db.String(150), default='default.jpg')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    youtube_url = db.relationship('YoutubeUrl')
    comments = db.relationship('Comments')
    summarizedComments = db.relationship('SummarizedComments')
    labeledComments = db.relationship('LabeledComments')
    frequentWords = db.relationship('FrequentWords')
