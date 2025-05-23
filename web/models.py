from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class UserLog(db.Model):
    __tablename__ = 'user_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False) # manually set through the route, not through the form
    users = db.Column(db.String(150), nullable=False) # manually set through the route, not through the form
    action = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class AdminLog(db.Model):
    __tablename__ = 'admin_log'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    action = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    admin = db.relationship('Admin', backref='admin_log')
    
class GetUrl(db.Model):
    __tablename__ = 'get_url'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(150))
    attempt = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

class YoutubeUrl(db.Model):
    __tablename__ = 'youtube_url'
    id = db.Column(db.Integer, primary_key=True)
    video_name = db.Column(db.String(150))
    video_id = db.Column(db.String(150))
    url = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    comments = db.relationship('Comments')
    highScoreComments = db.relationship('HighScoreComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')
    wordCloudImage = db.relationship('WordCloudImage')

class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(50000))
    sentiment = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class HighScoreComments(db.Model):
    __tablename__ = 'high_score_comments'
    id = db.Column(db.Integer, primary_key=True)
    most_positive_comment = db.Column(db.String(50000))
    most_negative_comment = db.Column(db.String(50000))
    highest_positive_score = db.Column(db.Float)
    highest_negative_score = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class FrequentWords(db.Model):
    __tablename__ = 'frequent_words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(150))
    count = db.Column(db.Integer)
    sentiment = db.Column(db.String(150))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class SentimentCounter(db.Model):
    __tablename__ = 'sentiment_counter'
    id = db.Column(db.Integer, primary_key=True)
    positive = db.Column(db.Integer)
    negative = db.Column(db.Integer)
    neutral = db.Column(db.Integer)
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class WordCloudImage(db.Model):
    __tablename__ = 'word_cloud'
    id = db.Column(db.Integer, primary_key=True)
    image_positive_data = db.Column(db.String(1000))
    image_negative_data = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    confirmed_email = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    get_url = db.relationship('GetUrl')
    youtube_url = db.relationship('YoutubeUrl')
    comments = db.relationship('Comments')
    highScoreComments = db.relationship('HighScoreComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')
    wordCloudImage = db.relationship('WordCloudImage')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'confirmed_email': self.confirmed_email,
            'created_at': self.created_at,
        }

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return f'admin_{self.id}'
