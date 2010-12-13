#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A Trove Client API interface using OAuth
'''
__all__ = ('TroveAPI', 'TroveError',
        'get_request_token', 'get_authorization_url', 'get_access_token','get_photos', 'push_photos', '__version__')
__author__ = 'Nick Vlku <n =at= yourtrove.com>'
__status__ = "Beta"
__dependencies__ = ('python-dateutil', 'simplejson', 'urllib', 'urllib2', 'oauth')
__version__ = '0.1.1'

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
        
    def __repr__(self):
        return "<TroveError with Error Code: \"%s-%s\" and Body: \"%s\">" % (self.http_error.code, self.http_error.msg, self.http_error.read())
    

class TroveAPI():
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
    
    def get_default_oauth_params(self):
        parameters = self._default_oauth_params.copy()
        parameters['oauth_nonce'] = _generate_nonce()
        parameters['oauth_timestamp'] = str(int(time.time()))

        return parameters
    
    def __make_oauth_request(self, url, parameters=None, oauth_signature=None, token=None, signed=False, method="POST"):
        if parameters is None:
            parameters = self.get_default_oauth_params()
        if token is not None:
            parameters['oauth_token'] = token.key
        if signed:
            parameters['oauth_signature_method'] = 'HMAC-SHA1'
            oauthrequest = oauth.OAuthRequest.from_token_and_callback(self._access_token, http_url=url, parameters=parameters, http_method=method)
            signature_method = self._signature_method()
            signature = signature_method.build_signature(oauthrequest, self._Consumer, self._access_token)
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
        response = self.__make_oauth_request(REQUEST_TOKEN_URL, oauth_signature=self._Consumer.secret+"&", method="GET")
        self.response = response
        request_token = oauth.OAuthToken.from_string(response.read())
        return request_token
        
    def get_authorization_url(self, request_token, callback=None):
        parameters = { 'oauth_token': request_token.key }
        
        if callback:
            parameters['oauth_callback'] = callback

        response = self.__make_oauth_request(AUTHORIZATION_URL, parameters, oauth_signature=None, method="GET")            
        return response.geturl()
                
    def get_access_token(self, request_token):
        response = self.__make_oauth_request(ACCESS_TOKEN_URL, oauth_signature='%s&%s' % (self._Consumer.secret, request_token.secret), token=request_token, method='GET')
        self.response = response
        access_token = oauth.OAuthToken.from_string(response.read())
        self._access_token = access_token
        return access_token
        
    def get_user_info(self):
        response = self.__make_oauth_request(USER_INFO_URL, token=self._access_token, signed=True)
        return simplejson.loads(response.read())

    def get_photos(self,query=None): 
        parameters = self.get_default_oauth_params()
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
        if photos_list is None: 
            return
        
        parameters = self.get_default_oauth_params()

        json_photos_list = simplejson.dumps(photos_list, cls=JSONFactories.encoders.get_encoder_for(photos_list[0]))
                                            
        parameters['object_list'] = json_photos_list
        parameters['number_of_items'] = len(photos_list)
        parameters['content_type'] = 'photos'
        parameters['user_id'] = user_id
        response = self.__make_oauth_request(PUSH_URL, parameters, token=self._access_token, signed=True, method="POST")

        return simplejson.loads(response.read())
