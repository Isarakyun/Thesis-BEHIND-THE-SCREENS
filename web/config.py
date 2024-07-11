import os

class Config:
    SECRET_KEY = os.urandom(24)
    GOOGLE_CLIENT_ID = '975276427788-olkmogi9n7s65kbb3tekgmqkke1kfobj.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = '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'
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/behindthescreens'
    SQLALCHEMY_TRACK_MODIFICATIONS = False