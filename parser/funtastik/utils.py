# -*- coding: utf-8 -*-
import requests

from config import API_ID, API_VERSION, API_URL


class VKAPIWrapper(object):
    """
    An easy wrapper for store VK credentials/wrap API call
    """

    def _params(self, method_params):
        """
        Create dict of parameters which should be passed into url
        """
        params = {'api_id': API_ID,
                  'format': 'JSON',
                  'v': API_VERSION}
        params.update(method_params)
        return params

    def get(self, method, method_params):
        """
        Call method with given parameters
        """
        params = self._params(method_params)
        r = requests.get(API_URL + method, params=params)

        json_data = r.json()

        if 'response' in json_data:
            return json_data['response']
        if 'error' in json_data:
            raise Exception(json_data['error'])
        raise Exception("Unknown Exception")
