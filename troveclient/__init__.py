#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""    A Trove Client API interface using OAuth
"""
__all__ = ('TroveAPI', 'TroveError',
        'get_request_token', 'get_authorization_url', 'get_access_token','get_photos', 'push_photos', '__version__')
__author__ = 'Nick Vlku <n =at= yourtrove.com>'
__status__ = "Beta"
__dependencies__ = ('python-dateutil', 'simplejson', 'urllib', 'urllib2', 'oauth')
__version__ = '0.1.8'

# This code is lovingly crafted in Brooklyn, NY (40°42′51″N, 73°57′12″W)
#
# Typical MIT license below:
#
# Copyright (c) 2010 Nick Vlku at YourTrove, Inc.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import urllib
import urllib2
import random
import time

import datetime
import simplejson

import oauth.oauth as oauth

from urllib2 import HTTPError
from dateutil.parser import *

from troveclient import JSONFactories
from troveclient.JSONFactories import make_nice

API_BETA_BASE = 'https://api.yourtrove.com'

VERSION_BETA_BASE = '/v1'

REQUEST_TOKEN_URL = API_BETA_BASE + VERSION_BETA_BASE + '/oauth/request_token/' # should be https
ACCESS_TOKEN_URL = API_BETA_BASE + VERSION_BETA_BASE + '/oauth/access_token/'  #should be https
AUTHORIZATION_URL = 'https://beta.yourtrove.com/oauth/authorize/'
CONTENT_ROOT_URL = API_BETA_BASE + VERSION_BETA_BASE +'/oauth/'
PUSH_URL = API_BETA_BASE + VERSION_BETA_BASE + '/oauth/push/'
USER_INFO_URL = API_BETA_BASE + VERSION_BETA_BASE +'/oauth/user/'
ADD_URLS_FOR_SERVICES_URL = API_BETA_BASE + VERSION_BETA_BASE + '/oauth/get_add_urls_for_services/'

def _generate_nonce(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])

def _generate_verifier(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])

def _oauth_version():
    """Right now always returns 1.0"""
    return '1.0'

class TroveError():
    """The :class:`~troveclient.TroveError` is returned when the client receives back an error. It contains a standard http_error object
    """
    def __init__(self, http_error, request):
        self.http_error = http_error
        self.request = request        
        
    def __repr__(self):
        return "<TroveError with Error Code: \"%s-%s\" and Body: \"%s\">" % (self.http_error.code, self.http_error.msg, self.http_error.read())
    
class RequiresAccessTokenError():
    """The :class:`~troveclient.RequiresAccessTokenError` is returned when a call is attempted that requires to be authenticated
    """
    def __init__(self):
        pass

    def __repr__(self):
        return "<RequiresAccessTokenError>"
    
class LocalError():
    """:class:`~troveclient.LocalError` is returned when a call is made with invalid or missing parameters
    """
    def __init__(self, msg):
        self.msg = msg
        
    def __repr__(self):
        return "<LocalError with msg: %s>" % (self.msg, )


class TroveAPI():
    """The base class for all Trove client actions
    
    :param consumer_key: A string of your application's Trove key
    :param consumer_secret:  A string of your application's Trove secret
    :param scope: A list of strings for scopes of the client.  Currently only 'photos' is valid.
    :param access_token: An instance of :class:`~oauth.oauth.OAuthToken' that is used to make requests on behalf of a user
    """

    DEBUG = False

    def __init__(self, consumer_key, consumer_secret, scope=[], access_token=None):
        self._Consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self._signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1
        self._access_token = access_token
        self._scope = scope
        self._urllib = urllib2
        self._initialize_user_agent()
        self._default_oauth_params = {
                  'oauth_consumer_key': self._Consumer.key,
                  'oauth_signature_method': 'PLAINTEXT',
                  'oauth_nonce':  _generate_nonce(),
                  'oauth_version': _oauth_version(),
                  'scope': ','.join(self._scope)
        } 
        
    def _initialize_user_agent(self):
        user_agent = 'Python-urllib/%s (python-trove/%s)' % \
                     (self._urllib.__version__, __version__)
        self.set_user_agent(user_agent)
                
    def set_access_token(self, access_token):
        self._access_token = access_token
        
    def set_user_agent(self, user_agent):
        self._useragent = user_agent
    
    def __get_default_oauth_params(self):
        parameters = self._default_oauth_params.copy()
        parameters['oauth_nonce'] = _generate_nonce()
        parameters['oauth_timestamp'] = str(int(time.time()))

        return parameters
    
    def __make_oauth_request(self, url, parameters=None, oauth_signature=None, token=None, signed=False, method="POST"):
        if parameters is None:
            parameters = self.__get_default_oauth_params()
        if token is not None:
            parameters['oauth_token'] = token.key
        if signed:
            parameters['oauth_signature_method'] = 'HMAC-SHA1'
            oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=url, parameters=parameters, http_method=method)
            signature_method = self._signature_method()
            signature = signature_method.build_signature(oauthrequest, self._Consumer, self._access_token)
            if self.DEBUG:
                print 'OAuth Signature:'
                print signature
            parameters['oauth_signature'] = signature
        else:
            if oauth_signature is not None:
                parameters['oauth_signature'] = oauth_signature

        try:
            if method is "POST":
                request = self._urllib.Request(url)
                request.add_header('User-agent', self._useragent)
                encoded_params = urllib.urlencode(parameters)
                if self.DEBUG:
                    print url + " : Parameters=" + parameters.__str__() + " : Encoded Parameters=" + encoded_params
                    raw_input()
                response = self._urllib.urlopen(request, encoded_params)
                return response
            else:
                encoded_params = urllib.urlencode(parameters)
                request = self._urllib.Request(url + '?' + encoded_params)  
                request.add_header('User-agent', self._useragent)
                if self.DEBUG:
                    print url + '?' + encoded_params
                    raw_input()
                response = self._urllib.urlopen(request)
                return response
            
        except HTTPError, e:
            error = TroveError(e, request)
            raise error
    
    def get_request_token(self):
        """    Returns an instance of :class:`~oauth.oauth.OAuthToken` representing a Request Token for user. 
        """    
        response = self.__make_oauth_request(REQUEST_TOKEN_URL, oauth_signature=self._Consumer.secret+"&", method="GET")
        self.response = response
        request_token = oauth.OAuthToken.from_string(response.read())
        return request_token

    def get_authorization_url(self, request_token, callback=None):
        """      Returns an authorization URL that should be passed to the end user to authorize their request token.
                
                :param request_token: An instance of :class:`~oauth.oauth.OAuthToken` that is used to authorize an access token by the user
                :param callback: A URL for the service to bounceback to.  The default is the application's callback URL specified in Trove
        """
        parameters = { 'oauth_token': request_token.key }
        
        if callback:
            parameters['oauth_callback'] = callback

        response = self.__make_oauth_request(AUTHORIZATION_URL, parameters, oauth_signature=None, method="GET")            
        return response.geturl()
                
    def get_access_token(self, request_token):
        """      Returns an instance of :class:`~oauth.oauth.OAuthToken` that is used to make requests on behalf of a user

                :param request_token: An instance of :class:`~oauth.oauth.OAuthToken` that is used to authorize an access token by the user
        """
        response = self.__make_oauth_request(ACCESS_TOKEN_URL, oauth_signature='%s&%s' % (self._Consumer.secret, request_token.secret), token=request_token, method='GET')
        self.response = response
        access_token = oauth.OAuthToken.from_string(response.read())
        self._access_token = access_token
        return access_token
        
    def get_user_info(self):
        """     Gets meta information about a User.  *This call requires an access token.*
        
                Returns a map of User Metainformation, including their name, email address and identities for scope you've initialized this client for.  
                User's will have the ability to restrict what is being sent back, so you make no assumptions.
        """

        if self._access_token is None:
            raise RequiresAccessTokenError()
        response = self.__make_oauth_request(USER_INFO_URL, token=self._access_token, signed=True)
        return simplejson.loads(response.read())

    def get_photos(self,query=None): 
        """     Retrieves a user's photos based on the Query passed in. *This call requires an access token.*
                Returns a :class:`~troveclient.Objects.Result` object that contains the results of your query
                
                :param query: An instance of :class:~`troveclient.Objects.Query~ object.  If none is passed, assumes page 1 with a count of 50.
        """
        if self._access_token is None:
            raise RequiresAccessTokenError()
        
        parameters = self.__get_default_oauth_params()
        base_url = CONTENT_ROOT_URL + 'photos/'

        if query is not None:
            query_post = simplejson.dumps(query, cls=JSONFactories.encoders.get_encoder_for(query))
            parameters['query'] = query_post
            self.response = self.__make_oauth_request(base_url, parameters, token=self._access_token, signed=True, method="POST")
        else:
            self.response = self.__make_oauth_request(base_url, parameters, token=self._access_token, signed=True, method="GET")
        
        results = simplejson.loads(self.response.read())
        nice_result = make_nice.make_it_nice(results)
        return nice_result

    def push_photos(self, user_id,  photos_list= []):
        """     Pushes a list of photos for user_id specified into Trove associated to your service. *This call requires an access token.*
                Returns a map of the status of your push.
                
                :param user_id: The user id of the user on YOUR service.
                :param photos_list: A list of :class:~`troveclient.Objects.Photo`
        """
        if self._access_token is None:
            raise RequiresAccessTokenError()
        
        if photos_list is None: 
            return
        
        parameters = self.__get_default_oauth_params()

        json_photos_list = simplejson.dumps(photos_list, cls=JSONFactories.encoders.get_encoder_for(photos_list[0]))
                                            
        parameters['object_list'] = json_photos_list
        parameters['number_of_items'] = len(photos_list)
        parameters['content_type'] = 'photos'
        parameters['user_id'] = user_id
        response = self.__make_oauth_request(PUSH_URL, parameters, token=self._access_token, signed=True, method="POST")

        return simplejson.loads(response.read())
        
    def get_services(self):
        """     Gets all the services Trove provides for the scope set for this client.  *This call requires an access token.*
                Returns a list of service names
        """        
        if self._access_token is None:
            raise RequiresAccessTokenError()

        response = self.__make_oauth_request(ADD_URLS_FOR_SERVICES_URL, token=self._access_token, signed=True)
        return simplejson.loads(response.read()).keys()    
    
    def get_url_for_service(self, service, redirect_url=None):
        """     This creates a URL that allows a user to add a service to their Trove and then immediately bounce back to your service.  If a 
                redirect_url URL is specified it uses that, otherwise it uses your application's default.  *This call requires an access token.*
                Returns a one-time use URL for the user
                
                :param service: The service name, usually from the list returned by get_services
                :param redirect_url: A redirect URL override.  The default is your application's callback.
        """        

        if self._access_token is None:
            raise RequiresAccessTokenError()

        response = self.__make_oauth_request(ADD_URLS_FOR_SERVICES_URL, token=self._access_token, signed=True)
        services = simplejson.loads(response.read())
            
        if service in services.keys():
            service_url = API_BETA_BASE + services[service]
            parameters = self.__get_default_oauth_params() 
            if redirect_url is not None:
                parameters['redirect_url'] = redirect_url

            response = self.__make_oauth_request(service_url, parameters, token=self._access_token, signed=True)
            return API_BETA_BASE + response.read()
        else: 
            raise LocalError("Could not find service name " + service)
