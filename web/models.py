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
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class SummarizedComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String(50000))
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))

class LabeledComments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sentiment = db.Column(db.String(150))
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))

class FrequentWords(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(150))
    count = db.Column(db.Integer)
    sentiment = db.Column(db.String(150))
    labeledComments_id = db.Column(db.Integer, db.ForeignKey('labeled_comments.id'))

class SentimentCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    positive = db.Column(db.Integer)
    negative = db.Column(db.Integer)
    neutral = db.Column(db.Integer)
    labeledComments_id = db.Column(db.Integer, db.ForeignKey('labeled_comments.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    profile_pic = db.Column(db.String(150), default='default.jpg')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    youtube_url = db.relationship('YoutubeUrl')