# -*- coding: utf-8 -*-
"""
This module provides functionality for grabbing photos from walls via VK API
"""
import sys
import shelve
import argparse
import requests
import json
from copy import deepcopy
import os

import pymongo
from bson.dbref import DBRef

# todo: move to separate config
ACCESS_KEY = 'AKIAI2SXOF6YS3UOMEWA'
SECRET_ACCESS_KEY = 'KVy3qguXvVDYVkTDlO5W+G+5D4F4dGi92svuq2p'
SERVER_URL = 'http://95.85.22.116:5000/addimage'
# mongo settings
HOST = 'localhost'
PORT = 27017


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


class AlreadyExist(Exception):
    pass


class CollectionEmpty(Exception):
    pass


class MongoStorage(object):
    client = pymongo.MongoClient(HOST, PORT)
    db = client.funtastik_parser

    def add_source(self, source, source_type='vk'):
        with self.client.start_request():
            if self.db.sources.find({'domain': source}).count():
                raise AlreadyExist
            self.db.sources.insert({'domain': source, 'type': source_type,
                                    'images': [], 'latest_post_timestamp': 0})

    def get_sources(self):
        sources = self.db.sources.find()
        result = []
        if sources:
            for source in sources:
                source_images = []
                for image in source['images']:
                    source_images.append(self.db.dereference(image))
                source['images'] = source_images
                result.append(source)
            return result
        raise CollectionEmpty

    def store_images(self, source, images, latest_post_timestamp):
        if len(images):
            with self.client.start_request():
                images = deepcopy(images)
                for image in images:
                    image['source'] = source
                db_images = self.db.images.insert(images)

                self.db.sources.update({'domain': source},
                                       {'$set': {'latest_post_timestamp': latest_post_timestamp}, '$push': {'images': {'$each': [DBRef(collection='sources', id=i) for i in db_images]}}})


class VKSource(object):
    """
    Process a data source(for now - VK only)
    """

    def __init__(self, target, count, start_from=None):
        self.target = target
        self.count = count
        self.start_from = start_from
        self.parser = VKAPIWrapper()
        self.latest_post_timestamp = None
        self.client = MongoStorage()

    def refresh(self):
        print 'Loading images...'
        images = self.load_images()
        print 'Push images...'
        images = self.push_results(images)
        return images

    def load_images(self):
        """
        Load images from source
        """
        photos = self.__get_wall_photos()
        data = []
        if photos:
            for photo in photos:
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
        print int(data['items'][0]['date']), self.latest_post_timestamp

        if len(data['items']) > 0:
            if self.latest_post_timestamp is None or \
                    (int(data['items'][0]['date']) - self.latest_post_timestamp) > 3600:

                self.latest_post_timestamp = int(data['items'][0]['date'])
                for item in data['items']:
                    if 'attachments' in item and len(item['attachments']) == 1 \
                            and item['attachments'][0]['type'] == 'photo' \
                            and server_time - int(item['date']) > 3600 and not (self.latest_post_timestamp is None or
                                (int(item['date']) - self.latest_post_timestamp)) > 3600:
                        photo = item['attachments'][0]['photo']
                        photo['likes'] = item['likes']
                        photo['comments'] = item['comments']
                        photo['reposts'] = item['reposts']
                        print 'Appended', str(item['attachments'][0]['photo']['id'])
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
            print 'Prepare request...'
            r = requests.get(SERVER_URL, params={'data': str(json.dumps(image))
            })
            print 'Request succeed'
            if r.status_code != 200:
                print 'error!', r.text
            else:
                print 'Pushed', str(image)
        return imgs


class Client(object):
    storage = MongoStorage()

    def add(self, source):
        try:
            self.storage.add_source(source)
        except AlreadyExist:
            sys.stdout.write('Source already in DB\n')
        else:
            sys.stdout.write('Source has been added\n')

    def get_list(self):
        try:
            sources = self.storage.get_sources()
        except CollectionEmpty:
            sys.stdout.write('You don\'t have any source\n')
        else:
            for row in [(s['domain'], len(s['images'])) for s in sources]:
                sys.stdout.write('{}, images: {}\n'.format(row[0], row[1]))

    def refresh(self):
        added = 0
        for source in self.storage.get_sources():
            # later here will be mapping with type of resources and parsers.
            # later. not now.
            parser = VKSource(source['domain'], 100)
            parser.latest_post_timestamp = source['latest_post_timestamp']
            print parser.latest_post_timestamp, type(parser.latest_post_timestamp)
            images = parser.refresh()

            self.storage.store_images(source['domain'],
                                      images, parser.latest_post_timestamp)
            added += len(images)
        sys.stdout.write('{} images has been parsed\n'.format(added))

if __name__ == '__main__':
    # todo: it's ugly. Refactoring needed
    # todo: rm(clean) storage
    # todo: mongo
    # todo: multithreading
    # todo: commited to server for every image
    # todo: exceptions
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('param', nargs='?')
    args = parser.parse_args()

    client = Client()
    if args.action == 'add':
        if args.param is not None:
            client.add(args.param)

        else:
            sys.stdout.write('You should pass source name as '
                             'second parameter\n')

    elif args.action == 'list':
        client.get_list()

    elif args.action == 'refresh':
        client.refresh()
