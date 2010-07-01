Trove Python Client
===================

The Trove Python Client is used to interact with Trove.   It provides a (relatively) simple API to ask a user to authorize your application/site to Trove and then pull on the user's behalf.  It provides (simple, for now) query facilities.

This library is under (very) active development -- so please keep that in mind!

Dependencies
------------
The Trove Python client has relatively few dependencies.  They are:

- [python-dateutil](http://labix.org/python-dateutil)
- [simplejson](http://code.google.com/p/simplejson/)
- urllib and urllib2
- [Leah Culver's OAuth library](http://oauth.googlecode.com/svn/code/python/oauth/)

##How does this thing work?  Is this thing on? :tap tap:

Sadly, Trove isn't on *yet* as of June 30, 2010... but we should be releasing a beta soon.  Once it's out using the API is pretty simple:

### Initializing a new Trove API

Once you receive your key and secret (and register your app/site with us) you can create a new instance of TroveAPI like so:

	from troveclient import TroveAPI
	api = TroveAPI(app_key, app_secret, ['list','of','content_types'])

Keep in mind, a Trove API instance is scoped to a USER.

### Initializing a new Trove API with an access_token you already have from a data store

	from troveclient import TroveAPI
	api = TroveAPI(app_key, app_secret, ['list','of','content_types'],access_token=access_token_from_datastore)

The list of content types are what you are asking the User to give you access to.  Currently the list can be: `photos`.  (More is coming, we promise!)

### Getting a request token

Trove uses standard OAuth 1.0a. Please see the OAuth site for more information on the details of how OAuth works.  To get a request token using the Trove API:

`request_token = api.get_request_token()`

### To get the authorization URL to forward the user to

`url = api.get_authorization_url(request_token)`

Keep in mind, the authorization URL will post the token response back to the callback you specify (if you have a web app) or a response page will render with the status in an HTML page inside a div with an id of `auth_response`

### Getting the access token from an authorized request token

`access_token = api.get_access_token(request_token)`

This access_token is what you should be storing in a data store for future accesses. 

### Ok I have an authorized client, how can I get stuff!?

Phew!  Once that's done, the currently instantiated API already is logged in for the user so you can just make requests as simple as:

`results = api.get_photos()`

### That's kind of lame?  Where are those robust query facilities you were talking about?

Oh man, we have query facilities!  There is a query object that can be populated with various fields you might be interested in.  These include:

	services:  	List of: facebook, flickr, google, smugmug -- default is all
 	tags_required:  List of tags wanted
 	date_from:  	Python datetime
 	date_to: 	Python datetime
 	force_update:	Force us to requery the service and not hit the cache


For example, to build a query for photos containing the tags "Williamsburg", "Snow" after March 4, 2007 you would do this:

	from troveclient.Objects import Query
	import datetime
	q = Query()
	q.date_from = datetime.datetime.strptime("2007-03-04 21:08:12", "%Y-%m-%d %H:%M:%S")
	q.tags_required = ['Williamsburg', 'snow']
	api.get_photos(q) # assuming api with valid access_token

- So what's coming down the pipeline?
We need your input for what you want!  Please email Developer Requests <developer-requests@yourtrove.com> for what you are interested in.  Our (incredibly long) to-do list includes:
1. More content types (video, status, friends)
2. Pagination on queries
3. Geolocation for queries
4. More services!

Please let us know if you have any questions or concerns.

Contacts
--------
* Nick Vlku <n@yourtrove.com>
* Developer Requests <developer-requests@yourtrove.com>
