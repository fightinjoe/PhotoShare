from credentials          import facebook_app_id, facebook_api_secret
from photo_service        import Token, Photo, Album, Person
from google.appengine.api import urlfetch
from django.utils         import simplejson as json

from datetime import datetime

import urllib
import logging as log

_domain = "http://localhost:8080"

class FacebookPerson(Person):
    service = 'facebook'

class FacebookToken(Token):
    service = 'facebook'

class FacebookAlbum(Album):
    service = 'facebook'

class FacebookPhoto(Photo):
    service = 'facebook'

# scope: user_photos,friends_photos,friends_videos,read_stream,offline_access
def auth_url( redirect_to="/token?service=facebook", scope='user_photos,friends_photos,friends_videos,user_photo_video_tags,friends_photo_video_tags,read_stream,offline_access' ):
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

########## Import Methods ###########

def import_people( user, token ):
    people = get_friends( token )['data']

    for p_data in people:
        # look to see if the person exists
        person = FacebookPerson.gql("WHERE owner = :1 and id = :2", user, p_data['id'])
        if person.count() == 0:
            print "Nobody named " + p_data['name']
            person = FacebookPerson( name=p_data['name'], id=p_data['id'], owner=user )
            person.put()
        else:
            print "Somebody named " + p_data['name']

def import_albums( user, token, user_id ):
    # get the user
    person = FacebookPerson.gql("WHERE id=:1 AND owner = :2", user_id, user)
    if person.count() > 0:
        person = person[0]
    else:
        return

    # get tagged photos
    albums = get_albums( user_id, token )['data']

    # normalize the data and save each photo
    for p_data in albums:
        album = {
            'id'         : p_data['id'],
            'owner'      : person,
            'title'      : p_data['name'] if 'name' in p_data else '',
            'created_at' : datetime.strptime( p_data['created_time'], "%Y-%m-%dT%H:%M:%S+0000" ),
            'updated_at' : datetime.strptime( p_data['updated_time'], "%Y-%m-%dT%H:%M:%S+0000" )
        }

        key = FacebookAlbum.keygen( type="facebook", **album )
        FacebookAlbum.get_or_insert( key, **album )

def import_photos( user, token, user_id=None, album_id=None ):
    # get the user
    person = None
    album  = None
    if user_id:
        person = FacebookPerson.gql("WHERE id=:1 AND owner = :2", user_id, user)
        if person.count() > 0:
            person = person[0]
        else:
            return
    elif album_id:
        album = FacebookAlbum.gql("WHERE id=:1", album_id)
        if album.count() > 0:
            album = album[0]
            person = album.owner
        else:
            return

    # get tagged photos
    photos = get_photos_of( user_id, token )['data']

    # normalize the data and save each photo
    for p_data in photos:
        photo = {
            'owner'      : person,
            'id'         : p_data['id'],
            'title'      : p_data['name'] if 'name' in p_data else '',
            'square_url' : p_data['images'][-1]['source'],
            'thumb_url'  : p_data['picture'],
            'full_url'   : p_data['source'],
            'width'      : p_data['width'],
            'height'     : p_data['height'],
            'taken_on'   : datetime.strptime( p_data['created_time'], "%Y-%m-%dT%H:%M:%S+0000" )
        }

        key = FacebookPhoto.keygen( type="facebook", **photo )
        FacebookPhoto.get_or_insert( key, **photo )

########## Graph API ###########

def get_auth_token( code ):
    path   = "/oauth/access_token"
    params = {
        'client_id'    : facebook_app_id,
        'redirect_uri' : _domain + '/token?service=facebook',
        'client_secret': facebook_api_secret,
        'code'         : code
    }

    return call( path, params, lambda c: c.split('=')[1] )

def get_friends( token ):
    path   = "/me/friends"
    params = { 'access_token' : token.token }

    return call( path, params )

def get_albums( user_id, token ):
    path = "/" + user_id + "/albums"
    params = { 'access_token' : token.token }

    return call( path, params )

def get_photos_of( user_id, token ):
    path   = "/" + user_id + "/photos"
    params = { 'access_token' : token.token }

    return call( path, params )