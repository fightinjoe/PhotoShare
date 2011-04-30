from credentials          import facebook_app_id, facebook_api_secret
from photo_service        import PhotoService
from google.appengine.api import urlfetch
from django.utils         import simplejson as json

import urllib
import logging as log

class FacebookToken(PhotoService):
    service = 'facebook'

_domain = "http://localhost:8080"

# scope: user_photos,friends_photos,friends_videos,read_stream,offline_access
def auth_url( redirect_to="/token?service=facebook", scope='user_photos,friends_photos,friends_videos,read_stream,offline_access' ):
    # https://www.facebook.com/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=YOUR_URL&scope=
    out  = "https://www.facebook.com/dialog/oauth?"
    dict = {
        'client_id'    : facebook_app_id,
        'redirect_uri' : _domain + redirect_to,
        'scope'        : scope
    }

    out += urllib.urlencode( dict )

    return out

def call( path, params={}, callback=None ):
    url    = "https://graph.facebook.com" + path + "?" + urllib.urlencode(params)
    result = urlfetch.fetch(url)

    log.info( url )
    log.info( result.content )

    if result.status_code == 200:
        return callback( result.content ) if callback else json.loads( result.content )

def get_auth_token( code ):
    path   = "/oauth/access_token"
    params = {
        'client_id'    : facebook_app_id,
        'redirect_uri' : _domain + '/token?service=facebook',
        'client_secret': facebook_api_secret,
        'code'         : code
    }

    call( path, params, lambda c: c.split('=')[1] )

def get_friends( token ):
    path   = "/me/friends"
    params = { 'access_token' : token.token }

    return call( path, params )