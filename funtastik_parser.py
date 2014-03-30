# -*- coding: utf-8 -*-
"""
This module provides functionality for grabbing photos from walls via VK API

TODO: multithreading
TODO: refactor
"""
import requests

ACCESS_KEY = 'AKIAI2SXOF6YS3UOMEWA'
SECRET_ACCESS_KEY = 'KVy3qguXvVDYVkTDlO5W+G+5D4F4dGi92svuq2p'


class VKWallLoader(object):
    """
    An easy wrapper for store VK credentials/wrap API call
    """
    API_VERSION = '5.16'
    API_ID = '4274771'
    API_SECRET = 'EV9LaqJCOpmDaA6afbgz'
    API_URL = 'http://api.vk.com/method/'

    def _params(self, method_params):
        """
        Create dict of parameters which should be passed into url
        """
        p = {'api_id': self.API_ID,
             'format': 'JSON',
             'v': self.API_VERSION}
        p.update(method_params)
        return p

    def get(self, method, method_params):
        """
        Call method with given parameters
        """
        p = self._params(method_params)
        r = requests.get(self.API_URL + method, params=p)
        if 'response' in r.json():
            return r.json()['response']
        if 'error' in r.json():
            raise Exception(r.json()['error'])
        raise Exception("Unknown Exception")


class Source(object):
    def __init__(self, target, count, start_from=None):
        self.target = target
        self.count = count
        self.start_from = start_from
        self.parser = VKWallLoader()

    def load_images(self):
        photos = self.__get_wall_photos()
        if photos:
            links = self.__get_links(photos)
            return links
        return []

    def __get_wall_photos(self):
        data = self. parser.get('wall.get', {'domain': self.target})
        photos = []
        for item in data['items']:
            if 'attachments' in item and len(item['attachments']) == 1 and \
                            item['attachments'][0]['type'] == 'photo':
                photos.append(item['attachments'][0]['photo'])
        return photos

    def __get_links(self, photos):
        links = []
        for photo in photos:
            link = self.__get_biggest_image_link(photo)
            if link is not None:
                links.append(link)
        return links

    @staticmethod
    def __get_biggest_image_link(photo_data):
        sizes = ['photo_1280', 'photo_807', 'photo_604', 'photo_130',
                 'photo_75']
        for size in sizes:
            if size in photo_data.keys():
                return photo_data[size]

    def push_results(self):
        pass

    # this method we may use if problems with photo get will be figured out
    # @staticmethod
    # def __get_biggest_image_link(image_sizes):
    #     print image_sizes
    #     sizes = ['w', 'z', 'y', 'x', 'm', 's']
    #     d = dict([(i['type'], i['src']) for i in image_sizes])
    #     for s in sizes:
    #         if s in d.keys():
    #             return d[s]


if __name__ == '__main__':
    s = Source('mdk', 15)
    for i in s.load_images():
        print i
