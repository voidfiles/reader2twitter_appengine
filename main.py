#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




import wsgiref.handlers


from google.appengine.ext import webapp
from google.appengine.ext import db
import logging
import pprint
import feedparser 
from google.appengine.api import urlfetch
import urllib
import feedparser
import pprint
import re
from django.utils import simplejson 
import datetime
import time
import base64


API_KEY = "" # For use with bit.ly, or some other url shortener
SOURCE = "a social to twitter condenser" 
TWITTER_USERNAME = "" # you username on twitter 
TWITTER_PASSWORD = "" # Your password on twitter
GOOGLE_READER_USERNAME = ""# for sussing out if you posted a comment or not

def postToTwitter(tweet):
    login = TWITTER_USERNAME
    password = TWITTER_PASSWORD
    if "" == tweet:
        balh = 0 / 1 
        
    status = tweet
    payload= {'status' : status, 'source' : SOURCE}
    payload= urllib.urlencode(payload)
    base64string = base64.encodestring('%s:%s' % (login, password))[:-1]
    headers = {'Authorization': "Basic %s" % base64string}
    url = "http://twitter.com/statuses/update.xml"
    result = urlfetch.fetch(url, payload=payload, method=urlfetch.POST, headers=headers)
    return  result
class GqlEncoder(simplejson.JSONEncoder):

  """Extends JSONEncoder to add support for GQL results and properties.

  Adds support to simplejson JSONEncoders for GQL results and properties by
  overriding JSONEncoder's default method.
  """

  # TODO Improve coverage for all of App Engine's Property types.

  def default(self, obj):

    """Tests the input object, obj, to encode as JSON."""

    if hasattr(obj, '__json__'):
      return getattr(obj, '__json__')()

    elif isinstance(obj, datetime.datetime):
      output = {}
      fields = ['day', 'hour', 'microsecond', 'minute', 'month', 'second',
          'year']
      methods = ['ctime', 'isocalendar', 'isoformat', 'isoweekday',
          'timetuple']
      for field in fields:
        output[field] = getattr(obj, field)
      for method in methods:
        output[method] = getattr(obj, method)()
      output['epoch'] = time.mktime(obj.timetuple())
      return output

    elif isinstance(obj, time.struct_time):
      return list(obj)

    elif isinstance(obj, users.User):
      output = {}
      methods = ['nickname', 'email', 'auth_domain']
      for method in methods:
        output[method] = getattr(obj, method)()
      return output

    return simplejson.JSONEncoder.default(self, obj)
    
def JSONencode(input):
  return GqlEncoder().encode(input)

class Entry(db.Expando):
    data = db.TextProperty()
    
    
class MainHandler(webapp.RequestHandler):
    
    def get(self):
        self.response.out.write('Hello world!')
        
        
class SubscribeHandler(webapp.RequestHandler):

    def get(self):
        challange = self.request.get("hub.challenge")
        self.response.out.write(challange)
        
    def post(self):
        blah = pprint.pformat(self.request.body_file.read())
        d = feedparser.parse(blah)

        for entry in d.entries:
            entry_id = unicode(entry["id"])
            e = Entry.get_by_key_name(entry_id)
            if e: 
                continue 
                
            data = JSONencode(entry)
            e = Entry(key_name=entry_id, data=data)
            e.put()
            link = entry["link"]
            """
            if link.find("tskr.us") == -1:
                form_fields = {
                  "api_key": API_KEY,
                  "url": link
                }
                form_data = urllib.urlencode(form_fields)
                # Link should get shorten
                fetch_url = "http://tskr.us/api/v1/shorten";
                url = urlfetch.fetch(url,payload=form_data)
                link = "http://tskr.us/VV"
            """
            tweet = link
            try:
                if entry["author"] == GOOGLE_READER_USERNAME:
                    content = entry["content"][1]["value"]
                else:
                    content = entry["title"]
            except:
                pass
                
            content_cap = 139 - len(link)  
            
            tweet = content[0:140]
            
            self.response.out.write(tweet+"\n")
            p = re.compile( '\s\s+')

            
            
            tweet = tweet.encode('utf-8')
            tweet = tweet.replace(u'\\xe2\\x80\\x90', u'-')
            tweet = tweet.replace(u'\\xe2\\x80\\x99', "\\'")
            tweet = tweet.replace(u'\\xe2\\x98\\x85', u"")
            tweet = tweet.replace(u'\\xe2\\x80\\x98', u"'")
            tweet = tweet.replace(u'\\xe2\\x98\\x85', u"")
            tweet = tweet.replace(u'\\xe2\\x80\\x93', u"")
            tweet = tweet.replace(u'\\xe2\\x80\\x9c', u"'")
            tweet = tweet.replace(u'\\xe2\\x80\\x9d', u"'")
            tweet = tweet.replace(u'\\xe2\\x80\\x94', u"")
            tweet = tweet.replace(u'\\xe2\\x99\\xa5', u"")
            tweet = tweet.replace(u'\\xc2\\xab', u"")
            tweet = tweet.replace("\x03", "`").replace("\x04", "'")
            tweet = tweet.replace("\\'", "'")
            
            tweet = p.sub(' ', tweet)
            tweet = tweet[0:content_cap] + " " + link
            response = postToTwitter(tweet)
            self.response.out.write(tweet + "<br />\n")
            #self.response.out.write(response.content)
            
        self.response.out.write("")


def main():
    application = webapp.WSGIApplication(
        [
            ('/', MainHandler),
            ('/subscribe', SubscribeHandler),
        ],
        debug=True
    )
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
