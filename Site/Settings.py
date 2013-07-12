import os

base_path = str(os.path.dirname(os.path.abspath(__file__)))

# User management & registration
confirm_registrations_by_email = False # Not fully implemented
allow_registration = True
allow_login = True

# External services
try:
    os.environ['OSF_PRODUCTION']
    use_cdn_for_client_libs = True
except KeyError:
    use_cdn_for_client_libs = False

# Application paths
cache_path = os.path.join(base_path, 'Cache')
static_path = os.path.join(base_path, 'static')
# These settings should be overridden by envvars or another method.
uploads_path = os.path.join(base_path, 'Uploads')
# uploads_path = '/var/www/openscienceframeworkorg_uploads'

try:
    os.environ['OSF_PRODUCTION']
    mongo_uri = 'mongodb://osf:osfosfosfosf0$f@localhost:20771/osf20120530'
except KeyError:
    mongo_uri = 'mongodb://osf:osf@localhost:20771/osf_test'

#TODO: Configuration should not change between deploys - this should be dynamic.
canonical_domain = 'openscienceframework.org'
cookie_domain = '.openscienceframework.org' # Beaker

try:
    os.environ['OSF_PRODUCTION']
    dev_mode = False
except KeyError:
    dev_mode = True

