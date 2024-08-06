from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class AuditTrail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    action = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    

class YoutubeUrl(db.Model):
    __tablename__ = 'youtube_url'
    id = db.Column(db.Integer, primary_key=True)
    video_name = db.Column(db.String(150))
    url = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    comments = db.relationship('Comments')
    summarizedComments = db.relationship('SummarizedComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')
    wordCloudImage = db.relationship('WordCloudImage')

class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(50000))
    sentiment = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class SummarizedComments(db.Model):
    __tablename__ = 'summarized_comments'
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.String(50000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

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

class WordCloudImage(db.Model):
    __tablename__ = 'word_cloud'
    id = db.Column(db.Integer, primary_key=True)
    image_positive_data = db.Column(db.LargeBinary)
    image_negative_data = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    url_id = db.Column(db.Integer, db.ForeignKey('youtube_url.id'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    confirmed_email = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(1000))
    profile_pic = db.Column(db.String(150), default='default.jpg')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    youtube_url = db.relationship('YoutubeUrl')
    comments = db.relationship('Comments')
    summarizedComments = db.relationship('SummarizedComments')
    frequentWords = db.relationship('FrequentWords')
    sentimentCounter = db.relationship('SentimentCounter')
    wordCloudImage = db.relationship('WordCloudImage')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'confirmed_email': self.confirmed_email,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at,
        }

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

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
