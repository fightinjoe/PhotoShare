import hashlib
import logging as log
import urllib

from photo_service        import Token, Person, Photo, Album
from google.appengine.api import urlfetch
from xml.dom              import minidom
from credentials          import flickr_api_key, flickr_secret
from datetime             import datetime
from django.utils         import simplejson as json

class FlickrPerson(Person):
    service = 'flickr'

class FlickrToken(Token):
    service = 'flickr'

class FlickrAlbum(Album):
    service = 'flickr'

class FlickrPhoto(Photo):
    service = 'flickr'

# perms can be 'read', 'write', or 'delete'
def auth_url( perms="read" ):
    # http://flickr.com/services/auth/?api_key=[api_key]&perms=[perms]&api_sig=[api_sig]
    ps        = {'api_key':flickr_api_key, 'perms':perms}
    ps['sig'] = sign( ps )
    url       = "http://flickr.com/services/auth/?api_key=%(api_key)s&perms=%(perms)s&api_sig=%(sig)s" % ps
    return url

# Generates the URL for the REST-based API
def _request_url( method, params, do_sign=True ):
    # http://api.flickr.com/services/rest/?method=flickr.test.echo&name=value
    url = "http://api.flickr.com/services/rest/?"
    params.update( {"method":method, "api_key":flickr_api_key, "format":"json", "nojsoncallback":1} )
    if(do_sign):
        params.update( {'api_sig': sign(params)} )

    return url + urllib.urlencode( params )

def call( api_method, params, token=None ):
    if(token):
        params.update( {'auth_token':token.token} )

    url    = _request_url( api_method, params )
    result = urlfetch.fetch(url)

    log.info( url )
    log.info( result.content )

    if result.status_code == 200:
        return json.loads( result.content )

############## Import Methods ##############

def import_people( user, token ):
    contacts = get_contact_list( token=token )

    for c_data in contacts["contacts"]["contact"]:
        contact = {
            'user'   : user,
            'id'     : c_data['nsid'],
            'nick'   : c_data['username'],
            'name'   : c_data['realname'],
            'friend' : True if (c_data['friend'] == 1) else False,
            'family' : True if (c_data['family'] == 1) else False
        }

        person = FlickrPerson.gql("WHERE owner = :1 and id = :2", user, contact['id'])
        if person.count() == 0:
            print "Nobody named " + contact['name']
            person = FlickrPerson( owner=user, **contact )
            person.put()
        else:
            print "Somebody named " + contact['name']

def import_photos( user, token, owner_id=None, album_id=None ):
    # get the user
    person = None
    album  = None

    if album_id:
        album = FlickrAlbum.gql("WHERE id=:1", album_id)
        if album.count() > 0:
            album = album[0]
            person = album.owner
        else:
            return
    elif owner_id:
        person = FlickrPerson.gql("WHERE id=:1 AND user = :2", owner_id, user)
        if person.count() > 0:
            person = person[0]
        else:
            return

    # get tagged photos
    photos = get_photos( album.id if album else person.id, token )['photos']['photo']

    for photo in photos:
        size = None
        if 'url_o' in photo              : size = "_o"
        if not size and 'url_z' in photo : size = "_z"
        if size:
            params = {
                'user'       : user,
                'owner'      : person,
                'album'      : album,
                'id'         : photo['id'],
                'title'      : photo['title'],
                'desc'       : photo['description']['_content'],
                'square_url' : photo['url_s'],
                'thumb_url'  : photo['url_t'],
                'full_url'   : photo['url'+size],
                'taken_on'   : datetime.strptime( photo['datetaken'], "%Y-%m-%d %H:%M:%S" ),
                'width'      : int(photo['width'+size]),
                'height'     : int(photo['height'+size]),
                'latitude'   : float(photo['latitude']),
                'longitude'  : float(photo['longitude'])
            }

            key = FlickrPhoto.keygen( type="flickr", **params )
            FlickrPhoto.get_or_insert( key, **params )

############### API Methods ##################

def get_auth_token( frob ):
    auth = call( 'flickr.auth.getToken', {'frob':frob} )
    return auth['auth']['token']['_content']

def get_contact_list( opts={}, token=None ):
    return call('flickr.contacts.getList', opts, token=token)

def get_photos( person_id, token, page=1, per_page=100 ):
    params = {
        'user_id'  : person_id,
        'extras'   : 'description,date_taken,geo,url_t,url_s,url_z,url_o',
        'page'     : page,
        'per_page' : per_page
    }
    return call('flickr.people.getPhotos', params, token=token)

def sign( params ):
    # Sort your argument list into alphabetical order based on the parameter name.
    args = []
    for key in params:
        args.append( str(key) + str(params[key]) )
    args.sort()

    # concatenate the shared secret and argument name-value pairs e.g. SECRETbar2baz3foo1
    pre_sig = flickr_secret + ''.join(args)

    # calculate the md5() hash of this string
    # append this value to the argument list with the name api_sig, in hexidecimal string form
    md5 = hashlib.md5()
    md5.update( pre_sig )
    return md5.hexdigest()