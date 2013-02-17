from google.appengine.ext import db

class pics(db.Model):
    url = db.StringProperty(required = True)
    subreddit = db.StringProperty(required = True)
    permalink = db.StringProperty(required = True)
    tlink = db.StringProperty(required = True)
    date = db.IntegerProperty(required = True)
    title = db.TextProperty(required = True)
    
class SubReddits(db.Model):
    name = db.StringProperty(required = True)
    nsfw = db.BooleanProperty(required = True)
    lastupdate = db.DateTimeProperty(auto_now_add = True)