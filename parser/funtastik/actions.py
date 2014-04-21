# -*- coding: utf-8 -*-
import requests
import json

from parsers import VKParser
from db import MongoStorage, AlreadyExist, CollectionEmpty, DoesNotExists
from config import SERVER_URL


class EmptyValueException(Exception):
    pass


class AbstractAction(object):
    def validate(self, value=None):
        raise NotImplementedError

    def act(self):
        raise NotImplementedError

    def get_db(self):
        return MongoStorage()

    def run(self, value=None):
        self.validate(value)
        return self.act()


class AddAction(AbstractAction):
    value = None

    def validate(self, value=None):
        if not value:
            raise EmptyValueException
        self.value = value
        return True

    def act(self):
        db = self.get_db()
        try:
            db.add_source(self.value)
        except AlreadyExist:
            raise AlreadyExist
        return True


class RefreshAction(AbstractAction):
    def validate(self, value=None):
        return True

    def act(self):
        added = 0
        images = []
        db = self.get_db()
        for source in db.get_sources():
            parser = VKParser(source['domain'],
                              source['latest_post_timestamp'])
            images.extend(parser.refresh())
            pushed = self._push(images)
            db.store_images(source['domain'], pushed, parser.latest_post)
            added += len(pushed)
        return "%s images has been added" % added

    def _push(self, images):
        # todo: add junk
        pushed = []
        for image in images:
            r = requests.get(SERVER_URL, params={'data':
                                                 str(json.dumps(image))})
            if r.status_code == 200:
                print r.json()
                if r.json()['status'].upper() == 'OK':
                    pushed.append(image)
                else:
                    db = self.get_db()
                    # db.junk.insert()
        return pushed


class RMAction(AbstractAction):
    value = None

    def validate(self, value=None):
        if not value:
            raise EmptyValueException
        self.value = value
        return True

    def act(self):
        db = self.get_db()
        try:
            db.delete_source(self.value)
        except DoesNotExists:
            return DoesNotExists
        return "Removed"


class ListAction(AbstractAction):

    def validate(self, value=None):
        return True

    def act(self):
        db = self.get_db()
        try:
            sources = db.get_sources()
        except CollectionEmpty:
            return "No sources has been created"
        else:
            return '\n'.join([str(source['domain']) for source in sources])