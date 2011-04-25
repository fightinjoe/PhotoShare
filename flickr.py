import hashlib
from photo_service import PhotoService

from google.appengine.api import urlfetch
from xml.dom              import minidom

class Flickr(PhotoService):
    api_key = "774045fbbf44e95eff9cb4e3165a3ec2"
    secret  = "e0a879fe2e07f786"

    # perms can be 'read', 'write', or 'delete'
    def auth_url( self, perms="read" ):
        # http://flickr.com/services/auth/?api_key=[api_key]&perms=[perms]&api_sig=[api_sig]
        ps        = {'api':self.api_key, 'perms':perms}
        ps['sig'] = self.sign( ps )
        url       = "http://flickr.com/services/auth/?api_key=%(api)s&perms=%(perms)s&api_sig=%(sig)s" % ps
        return url

    # Generates the URL for the REST-based API
    def _request_url( self, method, params, sign=True ):
        # http://api.flickr.com/services/rest/?method=flickr.test.echo&name=value
        url = "http://api.flickr.com/services/rest/?"
        params.update( {'method':method, 'api_key':self.api_key} )
        if(sign):
            params.update( {'api_sig': self.sign(params)} )

        ps = []
        for key in params:
            ps.append( str(key) + '=' + str(params[key]) )

        return url + '&'.join(ps)

    def call( self, api_method, params, fn, auth=True ):
        if(auth):
            params.update( {'auth_token':self.token} )

        url    = self._request_url( api_method, params )
        result = urlfetch.fetch(url)

        if result.status_code == 200:
            dom = minidom.parseString(result.content)
            return fn( dom )

    def get_token_from_frob( self, frob ):
        fn = lambda d: d.getElementsByTagName("token")[0].data
        Flickr.call( 'flickr.auth.getToken', {'frob':frob, 'auth':False}, fn )

    def get_contact_list( self, filter='both', page=1, per_page=1000 ):
        def fn(d):
            out = []
            for contact in d.getElementsByTagName('contact'):
                out.append({
                    'nsid'     : contact.attributes['nsid'].value,
                    'username' : contact.attributes['username'].value,
                    'realname' : contact.attributes['realname'].value,
                    'friend'   : True if (contact.attributes['friend'].value == 1) else False,
                    'family'   : True if (contact.attributes['family'].value == 1) else False
                })
            return out
        return Flickr.call('flickr.contacts.getList', {'filter':filter,'page':page,'per_page':per_page}, fn)

    def sign( self, params ):
        # Sort your argument list into alphabetical order based on the parameter name.
        args = []
        for key in params:
            args.append( key + params[key] )
        args.sort()

        # concatenate the shared secret and argument name-value pairs e.g. SECRETbar2baz3foo1
        pre_sig = self.secret + ''.join(args)
        # print pre_sig

        # calculate the md5() hash of this string
        # append this value to the argument list with the name api_sig, in hexidecimal string form
        md5 = hashlib.md5()
        md5.update( pre_sig )
        return md5.hexdigest()