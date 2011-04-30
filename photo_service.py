from google.appengine.ext    import db
from google.appengine.ext.db import polymodel
from google.appengine.api    import users

class Token( polymodel.PolyModel ):
    owner  = db.UserProperty()
    token  = db.StringProperty()

    @classmethod
    def keygen( klass, params ):
        return klass.__name__ + params['owner'].user_id()

    @classmethod
    def update_or_create( klass, params ):
        key_name = klass.keygen( params )
        service  = klass.get_by_key_name( key_name )
        if service:
            service.token = params['token']
            service.put()
        else:
            params.update({'key_name': key_name })
            service = klass( **params )
            service.put()

        return service

    @classmethod
    def for_user( klass, user ):
        token = klass.gql("WHERE owner = USER(:1)", user.nickname())
        if token.count > 0:
            return token[0]
        else:
            return None

class Person( polymodel.PolyModel ):
    id    = db.StringProperty()
    name  = db.StringProperty()
    owner = db.UserProperty()

    @classmethod
    def keygen(klass, name, owner):
        return "_".join( id, name, owner.user_id() )

class Album( polymodel.PolyModel ):
    owner     = db.ReferenceProperty(Person, collection_name='albums')

    title     = db.StringProperty()
    desc      = db.StringProperty()
    latitude  = db.FloatProperty()
    longitude = db.FloatProperty()
            
class Photo( polymodel.PolyModel ):
    owner      = db.ReferenceProperty(Person, collection_name='photos')
    album      = db.ReferenceProperty(Album,  collection_name='photos')

    id         = db.StringProperty()
    title      = db.StringProperty( multiline=True )
    desc       = db.StringProperty()
    square_url = db.StringProperty()
    thumb_url  = db.StringProperty()
    full_url   = db.StringProperty()
    taken_on   = db.DateTimeProperty()
    width      = db.IntegerProperty()
    height     = db.IntegerProperty()
    latitude   = db.FloatProperty()
    longitude  = db.FloatProperty()

    @classmethod
    def keygen( klass, type, owner, id, **misc ):
        return "_".join([ type, owner.id, id ])