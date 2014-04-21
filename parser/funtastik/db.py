# -*- coding: utf-8 -*-
import pymongo
from bson.dbref import DBRef
from copy import deepcopy

from config import HOST, PORT


class MongoStorage(object):
    client = pymongo.MongoClient(HOST, PORT)
    db = client.funtastik_parser

    def add_source(self, source, source_type='vk'):
        with self.client.start_request():
            if self.db.sources.find({'domain': source}).count():
                raise AlreadyExist
            self.db.sources.insert({'domain': source, 'type': source_type,
                                    'images': [], 'latest_post_timestamp': 0})

    def delete_source(self, source):
        with self.client.start_request():
            if self.db.sources.find({'domain': source}).count():
                raise DoesNotExists
            self.db.sources.remove({'domain': source})

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
                                       {'$set': {
                                           'latest_post_timestamp':
                                        latest_post_timestamp},
                                        '$push': {'images': {'$each': [
                                            DBRef(collection='images', id=i)
                                            for i in db_images]}}})


class DoesNotExists(Exception):
    pass


class AlreadyExist(Exception):
    pass


class CollectionEmpty(Exception):
    pass
