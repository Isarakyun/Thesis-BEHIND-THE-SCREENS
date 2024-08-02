import os

class Config:
    SECRET_KEY = os.urandom(24)
    # GOOGLE_CLIENT_ID = '975276427788-olkmogi9n7s65kbb3tekgmqkke1kfobj.apps.googleusercontent.com'
    # GOOGLE_CLIENT_SECRET = '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'
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('180041152651-2h17nfn5kaaksiid9q7nos74prj6seu1.apps.googleusercontent.com')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('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')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/behindthescreens'
    SQLALCHEMY_TRACK_MODIFICATIONS = False