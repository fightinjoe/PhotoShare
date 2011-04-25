from google.appengine.ext    import db
from google.appengine.ext.db import polymodel
from google.appengine.api    import users

class PhotoService( polymodel.PolyModel ):
    owner  = db.UserProperty()
    name   = db.StringProperty()
    token  = db.StringProperty()
    secret = db.StringProperty()

    @classmethod
    def keygen( params ):
        return params['owner'].user_id() + params['name']

    @classmethod
    def update_or_create( params ):
        key_name = PhotoService.keygen( params )
        service  = PhotoService.get_by_key_name( key_name )
        if service:
            service.token = params['token']
            service.put()
        else:
            service = Service( params.update({'key_name': PhotoService.keygen(params) }) )
            service.put()
