import urllib2
import calendar
import json
import re
import hashlib

import logging

PICTUREEXTENSIONS = ['.jpg', '.png', '.gif']

def splitsublist(sublist):
    """splits string sublist into list with individual subs"""
    return sublist.split('/')

def getDataFromUrl(url):
    """Sets up a urlrequest and returns the data"""
    try:
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Reppic Picture Link Crawler v0.1 by /u/nFresh')
        opener = urllib2.build_opener()
        data = opener.open(request)
    except (urllib2.HTTPError, urllib2.URLError) as e:
        data = None
        logging.error("Couldn't Open: " + url+ " Errorcode: " + str(e.code))
    return data


def datetimetotimestamp(dt):
    return calendar.timegm(dt.utctimetuple())


def toUtc(dt):
    return datetimetotimestamp(dt
)

def jsontodict(page):
    res = json.load(page)
    return res

def extractlinks(listings):
    """Generator that yields all seperate listings from a reddit json"""
    if listings["data"]["children"]:
        for child in listings["data"]["children"]:
            yield child
            
def linkurl(listing):
    """Returns a tuple (url,name, title, timestamp created) of a Reddit link"""
    return (listing["data"]["url"], listing["data"]["name"], listing["data"]["title"], int(listing["data"]["created_utc"]))
      
def redditjson(suburl):
    """Returns a list of all images contained in the specified subreddit"""
    url = "http://www.reddit.com" + suburl + "/.json?limit=100"
    page= getDataFromUrl(url)
    if page == None:
        return None
    try:
        pagedict= jsontodict(page)
    except ValueError:
        return None
    return [s for s in linkgen(pagedict)]
    
def linkgen(jpage):
    for child in extractlinks(jpage):
        if re.findall(r"\.[^.]*$", linkurl(child)[0])[0] in PICTUREEXTENSIONS:
            yield linkurl(child)

def make_key(iden, *a, **kw):
    """
A helper function for making memcached-usable cache keys out of
arbitrary arguments. Hashes the arguments but leaves the `iden'
human-readable
""" 
    h = hashlib.md5()
    
    def _conv(s):
        if isinstance(s, str):
            return s
        elif isinstance(s, unicode):
            return s.encode('utf-8')
        elif isinstance(s, (tuple, list)):
            return ','.join(_conv(x) for x in s)
        elif isinstance(s, dict):
            return ','.join('%s:%s' % (_conv(k), _conv(v))
                            for (k, v) in sorted(s.iteritems()))
        else:
            return str(s)
    
    iden = _conv(iden)
    h.update(iden)
    h.update(_conv(a))
    h.update(_conv(kw))
    
    return '%s(%s)' % (iden, h.hexdigest()) 