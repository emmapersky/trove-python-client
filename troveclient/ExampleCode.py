#Some Sample code for how Trove Client APIs work

from troveclient import TroveAPI
from oauth_provider.models import Consumer

# You need a consumer.  Make one in the db. Consumers have call back URLs, which are not overridable (a-la Twitter and Fb)  
c = Consumer.objects.all()[0]  

# Initialize the TroveAPI with the consumer's key and secret
api = TroveAPI(c.key, c.secret, ['photo'])

rt = api.get_request_token()  
# We get the request token -- returns back an 'OAuthToken'
 
url = api.get_authorization_url(rt)  
# Returns back the URL to redirect the user  (Looks like 'http://brooklyn.vlku.com:8000/multi/login?next=/oauth/authorize/%3Foauth_token%3DdtKaXn5JXRWNndTa')

# callback URL  AUTHORIZES (SAME) token and redirects to a page for you to act on token to get access token
# to promote a request token to an access token call this method

at = api.get_access_token(rt)  
# This returns back the access_token (at) as an OAuthToken.  You want to save this somewhere for reuse later
# access_token also conveniently makes this the access_token for the instantiated API

# so you can call this easily right away with no setup
results = api.get_photos()


# but if you have to initialize a fresh TroveAPI (say for another hit with the token from the DB:)
api = TroveAPI(c.key, c.secret, ['photo'], access_token=at)
results = api.get_photos()

