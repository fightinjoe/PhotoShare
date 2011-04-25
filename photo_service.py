from google.appengine.ext    import db
from google.appengine.ext.db import polymodel
from google.appengine.api    import users

class PhotoService( polymodel.PolyModel ):
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
