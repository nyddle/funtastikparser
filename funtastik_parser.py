# -*- coding: utf-8 -*-
"""
This module provides functionality for grabbing photos from walls via VK API
"""
import sys
import shelve
import argparse
import requests
from copy import deepcopy

# todo: move to separate config
ACCESS_KEY = 'AKIAI2SXOF6YS3UOMEWA'
SECRET_ACCESS_KEY = 'KVy3qguXvVDYVkTDlO5W+G+5D4F4dGi92svuq2p'
SERVER_URL = 'http://95.85.22.116:5000/addimage'


class VKAPIWrapper(object):
    """
    An easy wrapper for store VK credentials/wrap API call
    """
    # todo: move to separate config
    API_VERSION = '5.16'
    API_ID = '4274771'
    API_SECRET = 'EV9LaqJCOpmDaA6afbgz'
    API_URL = 'http://api.vk.com/method/'

    def _params(self, method_params):
        """
        Create dict of parameters which should be passed into url
        """
        params = {'api_id': self.API_ID,
                  'format': 'JSON',
                  'v': self.API_VERSION}
        params.update(method_params)
        return params

    def get(self, method, method_params):
        """
        Call method with given parameters
        """
        params = self._params(method_params)
        r = requests.get(self.API_URL + method, params=params)
        json_data = r.json()
        if 'response' in json_data:
            return json_data['response']
        if 'error' in json_data:
            raise Exception(json_data['error'])
        raise Exception("Unknown Exception")


class Source(object):
    """
    Process a data source(for now - VK only)
    """

    def __init__(self, target, count, storage, start_from=None):
        self.target = target
        self.count = count
        self.start_from = start_from
        self.parser = VKAPIWrapper()
        self.latest_post_timestamp = None
        self.storage = storage

    def refresh(self):
        images = self.load_images()
        images = self.push_results(images)
        self.store_metadata(images)

    def load_images(self):
        """
        Load images from source
        """
        photos = self.__get_wall_photos()
        data = []
        if photos:
            for photo in photos:
                print photo.keys()
                link = self.__get_biggest_image_link(photo)
                if link is not None:
                    data.append({'href': link,
                                 'source': self.target,
                                 'likes': photo['likes']['count'],
                                 'share': photo['reposts']['count'],
                                 'comments': photo['comments']['count']})
        return data

    def __get_wall_photos(self):
        """
        Receive posts from VK and fetch actual data
        """
        data = self.parser.get('wall.get', {'domain': self.target,
                                            'count': 100})
        photos = []
        server_time = int(self.parser.get('getServerTime', {}))
        if len(data['items']) > 0:
            if self.latest_post_timestamp is None or \
                    not int(data['items'][0]['date']) < self.latest_post_timestamp:

                self.latest_post_timestamp = int(data['items'][0]['date'])
                for item in data['items']:
                    if 'attachments' in item and len(item['attachments']) == 1\
                            and item['attachments'][0]['type'] == 'photo' \
                            and server_time - int(item['date']) > 3600:
                        photo = item['attachments'][0]['photo']
                        photo['likes'] = item['likes']
                        photo['comments'] = item['comments']
                        photo['reposts'] = item['reposts']
                        photos.append(photo)
        return photos

    def __get_links(self, photos):
        """
        Fetch links from  photos data
        """
        links = []
        for photo in photos:
            link = self.__get_biggest_image_link(photo)
            if link is not None:
                links.append(link)
        return links

    @staticmethod
    def __get_biggest_image_link(photo_data):
        """
        Find biggest possible size
        """
        sizes = ['photo_1280', 'photo_807', 'photo_604', 'photo_130',
                 'photo_75']
        for size in sizes:
            if size in photo_data.keys():
                return photo_data[size]

    def push_results(self, images):
        """
        Push results to server
        """
        imgs = deepcopy(images)
        for i, image in enumerate(images):
            import json
            r = requests.get(SERVER_URL, params={'data': str(json.dumps(image))})
            print '================================='
            print r.url
            print '================================='
            if r.status_code != 200:
                print 'error!', r.text
                #imgs.pop()
        return imgs

    def store_metadata(self, images):

        self.storage['sources'] = {}
        self.storage['sources'][self.target]['latest'] = self.latest_post_timestamp
        self.storage['sources'][self.target]['images'] = images + \
                                            self.storage['sources'][self.target]['images'] \
            if 'images' in self.storage[self.target] else images


if __name__ == '__main__':
    # todo: it's ugly. Refactoring needed
    # todo: rm storage
    # todo: multithreading
    # todo: commited to server for every image
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('param', nargs='?')
    args = parser.parse_args()
    storage = shelve.open('test_db.db', writeback=True)
    if args.action == 'add':
        if args.param is not None:
            if not 'sources' in storage:
                storage['sources'] = {}
            if args.param not in storage['sources']:
                if not 'sources' in storage:
                    storage['sources'] = {}
                # todo: check for spaces
                storage['sources'][args.param] = {'images': []}
                sys.stdout.write('Source added\n')
            else:
                sys.stdout.write('Source "%s" already exists. '
                                 'Run `list` to get all sources\n' % args.param)
        else:
            sys.stdout.write('You should pass source name as second parameter\n')
    elif args.action == 'list':
        if not 'sources' in storage or len(storage['sources']) == 0:
            sys.stdout.write('No sources has been added\n')
        else:
            for source_name, source_data in storage['sources'].iteritems():
                sys.stdout.write('{}, images:{}\n'.format(source_name,
                                                        len(source_data['images']))
                             )
    elif args.action == 'refresh':
        if not 'sources' in storage or len(storage['sources']) == 0:
            storage['sources'] = {}
            sys.stdout.write('You dont\'t have any source\n')
        else:
            for source_name, source_data in storage['sources'].iteritems():
                latest = source_data['latest'] if 'latest' in source_data \
                    else None
                # todo: do we really need count and start_from?
                s = Source(source_name, 50, storage)
                s.refresh()
                # try:
                #     s.refresh()
                # except Exception as e:
                #     sys.stdout.write('An error occured: %s\n' % e.message)
                # else:
                #     sys.stdout.write('Source %s has been refreshed\n' %
                #                      source_name)
