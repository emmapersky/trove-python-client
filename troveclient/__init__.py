#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A Trove Client API interface using OAuth
'''
from troveclient.JSONFactories import make_nice
__version__ = '0.0.0.0.2'
__all__ = ('TroveAPI', 'TroveError',
        'get_request_token', 'get_authorization_url', 'get_access_token','get_photos', '__version__')
__author__ = 'Nick Vlku <n@yourtrove.com>'

__dependencies__ = ('python-dateutil', 'simplejson', 'urllib', 'urllib2', 'oauth')

# Copyright (c) 2010 YourTrove, Inc 
# Nick Vlku <n@yourtrove.com>
#
# This code is lovingly crafted in Brooklyn, NY (40°42′51″N, 73°57′12″W)
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import urllib, urllib2, random, datetime, time, simplejson
import oauth.oauth as oauth

from urllib2 import HTTPError
from dateutil.parser import *

from troveclient import JSONFactories

API_BETA_BASE = 'http://beta.yourtrove.com'

REQUEST_TOKEN_URL = API_BETA_BASE + '/oauth/request_token/' # should be https
ACCESS_TOKEN_URL = API_BETA_BASE + '/oauth/access_token/'  #should be https
AUTHORIZATION_URL = API_BETA_BASE + '/oauth/authorize/'
SIGNIN_URL = API_BETA_BASE + '/oauth/authenticate/'
CONTENT_ROOT_URL = API_BETA_BASE + '/oauth/'
PUSH_URL = API_BETA_BASE + '/oauth/push/'
USER_INFO_URL = API_BETA_BASE + '/oauth/user/'


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
    def __init__(self, http_error, request):
        self.http_error = http_error
        self.request = request

class TroveAPI():
    DEBUG = False

    def __init__(self, consumer_key, consumer_secret, scope=[], access_token=None, default_params=None):
        self._Consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self._signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1
        self._access_token = access_token
        self._scope = scope
        self._urllib = urllib2
        self._initialize_user_agent()
        self._default_params = default_params
        
    def _initialize_user_agent(self):
        user_agent = 'Python-urllib/%s (python-trove/%s)' % \
                     (self._urllib.__version__, __version__)
        self.set_user_agent(user_agent)
                
    def set_access_token(self, access_token):
        self._access_token = access_token
        
    def set_user_agent(self, user_agent):
        self._useragent = user_agent

    def set_default_params(self, default_params):
        self._default_params = default_params

    def get_request_token(self):
        parameters =  {
                       'oauth_consumer_key': self._Consumer.key,
                       'oauth_signature_method': 'PLAINTEXT',
                       'oauth_signature': '%s&' % self._Consumer.secret,
                       'oauth_timestamp': str(int(time.time())),
                       'oauth_nonce':  _generate_nonce(),
                       'oauth_version': _oauth_version(),
                       'scope': ','.join(self._scope)
                       }
        
        encoded_params = urllib.urlencode(parameters)
        request = self._urllib.Request(REQUEST_TOKEN_URL + '?' + encoded_params)
        request.add_header('User-agent', self._useragent)
                
        if self.DEBUG:
            print REQUEST_TOKEN_URL + '?' + encoded_params
            raw_input()
            
        try:
            response = self._urllib.urlopen(request)
            self.response = response
            request_token = oauth.OAuthToken.from_string(response.read())
            return request_token
        except HTTPError, e:
            error = TroveError(e, request)
            raise error
        
    def get_authorization_url(self, request_token, callback=None):
        parameters = { 'oauth_token': request_token.key }
        
        if callback:
            parameters['oauth_callback'] = callback
            
        encoded_params = urllib.urlencode(parameters)

        request = self._urllib.Request(AUTHORIZATION_URL + '?' + encoded_params)
        request.add_header('User-agent', self._useragent)

        if self.DEBUG:
            print AUTHORIZATION_URL + '?' + encoded_params
            raw_input()

        try:
            response = self._urllib.urlopen(request)
            return response.geturl()
        
        except HTTPError, e:
            error = TroveError(e, request)
            raise error
        
        
    def get_access_token(self, request_token):
        parameters = {
                      'oauth_consumer_key': self._Consumer.key,
                      'oauth_token': request_token.key,
                      'oauth_signature_method': 'PLAINTEXT',
                      'oauth_signature': '%s&%s' % (self._Consumer.secret, request_token.secret),
                      'oauth_timestamp': str(int(time.time())),
                      'oauth_nonce':  _generate_nonce(),
                      'oauth_version': _oauth_version(),
                      'scope': ','.join(self._scope)
                      } 
        
        encoded_params = urllib.urlencode(parameters)
        request = self._urllib.Request(ACCESS_TOKEN_URL + '?' + encoded_params)
        request.add_header('User-agent', self._useragent)

        if self.DEBUG:
            print ACCESS_TOKEN_URL + '?' + encoded_params
            raw_input()
        
        try:
            response = self._urllib.urlopen(request)
            self.response = response
            access_token = oauth.OAuthToken.from_string(response.read())
            self._access_token = access_token
            return access_token
        except HTTPError, e:
            error = TroveError(e, request)            
            raise error
        
    def get_user_info(self):
        parameters = {
                      'oauth_consumer_key': self._Consumer.key,
                      'oauth_token': self._access_token.key,
                      'oauth_signature_method': 'HMAC-SHA1',
                      'oauth_timestamp': str(int(time.time())),
                      'oauth_nonce': _generate_nonce(),
                      'oauth_version': _oauth_version()
                      }

        oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=USER_INFO_URL, parameters=parameters, http_method="POST")
        signature_method = self._signature_method()
        signature = signature_method.build_signature(oauthrequest, self._Consumer, self._access_token)
        parameters['oauth_signature'] = signature
        
        encoded_params = urllib.urlencode(parameters)
 
        request = self._urllib.Request(USER_INFO_URL)
        
        request.add_header('User-agent', self._useragent)
        
        response = self._urllib.urlopen(request, encoded_params)

        return simplejson.loads(response.read())

    def push_photos(self, user_id,  photos_list= []):
        if photos_list is None: 
            return
        
        parameters = {
                      'oauth_consumer_key': self._Consumer.key,
                      'oauth_token': self._access_token.key,
                      'oauth_signature_method': 'HMAC-SHA1',
                      'oauth_timestamp': str(int(time.time())),
                      'oauth_nonce': _generate_nonce(),
                      'oauth_version': _oauth_version()
                      }

        json_photos_list = simplejson.dumps(photos_list, cls=JSONFactories.encoders.get_encoder_for(photos_list[0]))
                                            
        parameters['object_list'] = json_photos_list
        parameters['number_of_items'] = len(photos_list)
        parameters['content_type'] = 'photos'
        parameters['user_id'] = user_id

        oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=PUSH_URL, parameters=parameters, http_method="POST")
        
        signature_method = self._signature_method()
        signature = signature_method.build_signature(oauthrequest, self._Consumer, self._access_token)
        parameters['oauth_signature'] = signature
        encoded_params = urllib.urlencode(parameters)
        request = self._urllib.Request(PUSH_URL)
        
        request.add_header('User-agent', self._useragent)
        
        response = self._urllib.urlopen(request, encoded_params)

        return simplejson.loads(response.read())

    def get_photos(self,query=None): 
        parameters = {
                      'oauth_consumer_key': self._Consumer.key,
                      'oauth_token': self._access_token.key,
                      'oauth_signature_method': 'HMAC-SHA1',
                      'oauth_timestamp': str(int(time.time())),
                      'oauth_nonce': _generate_nonce(),
                      'oauth_version': _oauth_version()
                      }
        base_url = CONTENT_ROOT_URL + 'photos/'
        if query is not None:
            query_post = simplejson.dumps(query, cls=JSONFactories.encoders.get_encoder_for(query))
            parameters['query'] = query_post
            oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=base_url, parameters=parameters, http_method="POST")
        else:
            oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=base_url, parameters=parameters)
        
        
        signature_method = self._signature_method()
        signature = signature_method.build_signature(oauthrequest, self._Consumer, self._access_token)
        parameters['oauth_signature'] = signature

        encoded_params = urllib.urlencode(parameters)

        if query is not None:
            request = self._urllib.Request(base_url)
            encoded_params = urllib.urlencode(parameters)            
        else:
            encoded_params = urllib.urlencode(parameters)
            request = self._urllib.Request(base_url + '?' + encoded_params)
            
        request.add_header('User-agent', self._useragent)
        
        if self.DEBUG:
            if query is None:
                print CONTENT_ROOT_URL + 'photos/?' + encoded_params
            else:
                print CONTENT_ROOT_URL + 'photo' 
                print 'POST: ' + encoded_params
            raw_input()
        
            
        try:
            if query is not None:
                response = self._urllib.urlopen(request, encoded_params)
            else:
                response = self._urllib.urlopen(request)
            self.response = response
            results = simplejson.loads(response.read())
            nice_result = make_nice.make_it_nice(results)
            return nice_result
                
        except HTTPError, e:
            error = TroveError(e, request)
            
            raise error


