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
from google.appengine.api        import users, urlfetch
from google.appengine.ext        import webapp
from google.appengine.ext.webapp import util

from flickr        import Flickr
import facebook

from photo_service import Person

import helpers as h
import logging as log
import cgi
import urllib

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = h.get_user_or_redirect( self )
        if not user: return

        fb_friends = facebook.FacebookPerson.gql("WHERE owner = USER(:1)", user.nickname())

        template_values = h.template_params( self, user, **{
            'flickr_auth'       : Flickr().auth_url(),
            'facebook_auth'     : facebook.auth_url(),
            'facebook_friends'  : fb_friends
        } )

        h.render_template( self, 'services/index.html', template_values )

class TokenHandler(webapp.RequestHandler):
    # callback URL for web authentication
    def get(self):
        user = h.get_user_or_redirect( self )
        if not user: return

        service = h.param(self, 'service')
        t = None
        if service == 'flickr':
            token = Flickr().get_auth_token( h.param(self, 'frob') )
            t = Flickr.update_or_create( { 'token':token, 'owner':user } )
        elif service == 'facebook':
            token = facebook.get_auth_token( h.param(self,'code') )
            t = facebook.FacebookToken.update_or_create( { 'token':token, 'owner':user } )

        self.redirect( '/' )
        # self.response.headers['Content-Type'] = 'text/plain'
        # self.response.out.write( str(t) )

class PhotoHandler(webapp.RequestHandler):
    def get(self):
        user = h.get_user_or_redirect( self )
        if not user: return

        user_id = h.param(self,'user_id')
        service = h.param(self, 'service')
        
        person = Person.gql("WHERE id = :1 AND owner = USER(:2)", user_id, user.nickname())[0]

        template_values = h.template_params( self, user, **{ 'person' : person })

        if service == 'facebook':
            fb_photos = person.photos.filter('class =', 'FacebookPhoto')
            fb_albums = person.albums.filter('class =', 'FacebookAlbum')
            fb_token  = facebook.FacebookToken.for_user(user)
            if fb_token:
                fb_photos = fb_photos
                template_values['photos'] = fb_photos
                template_values['albums'] = fb_albums
            else:
                print "no token"
        else:
            print "no service"

        h.render_template( self, 'photos/index.html', template_values )

class DownloadHandler(webapp.RequestHandler):
    def get(self):
        user = h.get_user_or_redirect( self )
        if not user: return
        token = facebook.FacebookToken.for_user( user )

        service = h.param(self, 'service')
        type    = h.param(self, 'type')

        if service == 'facebook':
            if type == 'photos': # tagged photos
                user_id = h.param(self, 'user_id')
                facebook.import_photos( user, token, user_id )
                self.redirect("/photos?service=facebook&user_id="+user_id)
            elif type == 'people':
                facebook.import_people( user, token )
                self.redirect("/")
            elif type == 'albums':
                user_id = h.param(self, 'user_id')
                facebook.import_albums( user, token, user_id )
                self.redirect("/photos?service=facebook&user_id="+user_id)


def main():
    application = webapp.WSGIApplication([
        ('/',         MainHandler),
        ('/token',    TokenHandler),
        ('/photos',   PhotoHandler),
        ('/download', DownloadHandler)],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
