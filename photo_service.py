from google.appengine.ext    import db
from google.appengine.ext.db import polymodel
from google.appengine.api    import users

class Token( polymodel.PolyModel ):
    user  = db.UserProperty()
    token = db.StringProperty()

    @classmethod
    def keygen( klass, params ):
        return klass.__name__ + params['user'].user_id()

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
        token = klass.gql("WHERE user = :1", user)
        if token.count() > 0:
            return token[0]
        else:
            return None

class Person( polymodel.PolyModel ):
    id   = db.StringProperty()
    name = db.StringProperty()
    nick = db.StringProperty()
    user = db.UserProperty()

    @classmethod
    def keygen(klass, name, owner):
        return "_".join( id, name, owner.user_id() )

class Album( polymodel.PolyModel ):
    user       = db.UserProperty()
    owner      = db.ReferenceProperty(Person, collection_name='albums')
    id         = db.StringProperty()
    title      = db.StringProperty()
    desc       = db.StringProperty()
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()
    latitude   = db.FloatProperty()
    longitude  = db.FloatProperty()

    @classmethod
    def keygen( klass, type, owner, id, **misc ):
        return "_".join([ type, str(owner.id), str(id) ])
            
class Photo( polymodel.PolyModel ):
    user       = db.UserProperty()
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
        return "_".join([ type, str(owner.id), str(id) ])