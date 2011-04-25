import os

from google.appengine.api        import users
from google.appengine.ext.webapp import template

def get_user_or_redirect( request ):
    user = users.get_current_user()
    if not user:
        request.redirect( users.create_login_url(request.request.uri) )
        return False
    else:
        return user

def template_params( request, user, **extra ):
    out = {
        'login_url' : users.create_login_url( request.request.uri ),
        'logout_url': users.create_logout_url( request.request.uri ),
        'user'      : user
    }
    out.update( extra )
    return out

def render_template( request, temp_file, params ):
    path = os.path.join(os.path.dirname(__file__), 'templates', temp_file)
    request.response.out.write(template.render(path, params))

def param( request, key ):
    return request.request.get(key)