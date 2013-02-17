import logging
import webapp2
import jinja2
import os
import time
import datetime
import lib.models

from lib.utils import redditjson, toUtc, splitsublist
from lib.Transaction import Transaction
from google.appengine.ext import db
from google.appengine.api import memcache
from lib.cache import Cache
 
template_dir = os.path.join(os.path.dirname(__file__), r'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
SECRET = "PORNO"
DEFAULTSUBS = ['aww',  'earthporn', 'wallpapers']
CACHE = Cache()

def sanitizeString(s):
    return s.replace('\n', ' ')

jinja_env.filters['sanitizeString'] = sanitizeString

def CachedQuery(query, update=False):
    """Takes Query as string and returns a tuple(result, time_when_Cached) from Cache or DB """
    result = memcache.get(query)
    if result and not update and (time.time() - result[1]) < 300:
        return result
    else:
        result = db.GqlQuery(query)
        t = time.time() 
        memcache.set(query,(result, t))
        return (result, t)
    
## print redditjson("/r/gonewild")
    
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
    def updateSub(self, subname, lastupdate):
        """Takes a Subreddit Name and the datetime of the last update of this Subreddit and updates the pics db for this subreddit"""
        links = redditjson("/r/"+subname)
        if links == None:
            return False
        for link in links:
            if link[3] > toUtc(lastupdate):
                tlink = link[0]
                if link[0].find('i.imgur.com') != -1:
                    tlink = link[0][:-4] + 'l' + link[0][-4:]
                Transaction('pics').set( url = link[0], subreddit = subname, permalink = link[1], date = link[3], tlink = tlink, title = link[2])
        CACHE.cachedQuery('pics', _update = True)
        return True
        
class HomeHandler(Handler):
    def get(self, sublist):
        limit = self.request.get('limit')
        timestamp = self.request.get('after')
        ASCDESC = self.request.get('ascdesc')
        mode = "nothumb" if self.request.get('mode') == "" else self.request.get('mode')
        if timestamp == "":
            timestamp = 300000000000000000
        if ASCDESC == "" or "DESC":
            order = "-date"
        else:
            order = "date"
        if limit:
            limit = int(limit)
        else:
            limit = 50
        timestamp = int(timestamp)
        subs = []
        if sublist != "/":
            subs = splitsublist(sublist)
        else:
            subcookie = self.request.cookies.get('sub_selection')
            if subcookie:
                subs = splitsublist(subcookie)
            else:
                subs = DEFAULTSUBS

        query = Cache().cachedQuery('pics', subredditINININ = subs, dateSMALLER = timestamp, order = order, limit = limit)
        if len(query) > 0:
            lasttimestamp = (query[-1])['date']
            firsttimestamp = (query[0])['date']
        else:
            firsttimestamp = lasttimestamp = 300000000000000000
            
        self.render("main.html", pics = query, lasttimestamp = lasttimestamp, firsttimestamp = firsttimestamp, url = sublist, mode = mode)
        
    
            
        
        
class Addlinks(Handler):
    def get(self):
        query, _ = CachedQuery("SELECT * FROM SubReddits ORDER BY lastupdate ASC LIMIT 5")
        for q in query:
            if datetime.datetime.now() - q.lastupdate > datetime.timedelta(minutes=10):
                if self.updateSub(q.name, q.lastupdate):
                    q.lastupdate = datetime.datetime.now()
                    q.put()
                else:
                    logging.error("update Error: "+ q.name)
            else:
                return
    
    

#class PictureHandler(Handler):
#    def get(self, pic_id):
#        im = db.get(db.Key.from_path('picture', pic_id[1:])).picture
#        self.response.headers['Content-Type'] = 'image/jpeg'     ## TODO, other image types
#        self.response.out.write(im)
#        return
#    
class Addsub(Handler):
    def get(self):
        self.render("newsub.html")
    
    def post(self):
        subname = self.request.get("subname")
        nsfw = self.request.get("nsfw") == "on"
        query, _ = CachedQuery("SELECT * FROM SubReddits WHERE name='"+subname+"'")
        if not query.fetch(1):
            newsubreddit = Transaction('SubReddits').set(key_name = subname, name= subname, nsfw = nsfw)
            self.updateSub(subname, datetime.datetime(2010, 12, 31, 23, 59, 59))
            
        self.redirect("/_addsub")
        
class SubSelection(Handler):
    def get(self):
        selectcookie = self.request.cookies.get("sub_selection")
        if selectcookie:
            selected = splitsublist(self.request.cookies.get("sub_selection"))
        else:
            selected = ""
        
        query = Transaction('SubReddits').query()
        self.render("subselect.html", subquery = query, selected = selected)
    
    def post(self):
        subs = self.request.get_all('subs')
        cookiestring = ""
        for s in subs:
            cookiestring = cookiestring +"/" +  s 
        dt = datetime.datetime.now()
        dt = dt + datetime.timedelta(days = 30)
        expires = dt.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        self.response.headers.add_header('Set-Cookie', str('sub_selection='+cookiestring+";Path=/;expires="+expires))
        self.redirect("/")
        

PAGE_RE = r'(/(?:[a-zA-Z0-9]+/?)*)'
PICTURE_RE= r'(/(?:[a-zA-Z0-9_-]+/?))'
app = webapp2.WSGIApplication([
                               ('' + PAGE_RE, HomeHandler),                               
                               ('/_addlinks', Addlinks),
                          #     ('/_picture'+ PICTURE_RE + ".jpg", PictureHandler),
                               ('/_addsub', Addsub),
                               ('/_choosesubs', SubSelection),
                               ],
                              debug=True)
