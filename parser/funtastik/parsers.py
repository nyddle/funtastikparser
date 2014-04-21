# -*- coding: utf-8 -*-
from utils import VKAPIWrapper
from config import IMAGES_TO_LOAD


class VKParser(object):

    def __init__(self, source, latest_post):
        self.source = source
        self.latest_post = latest_post
        self.api = VKAPIWrapper()

    def refresh(self):
        loaded_images = self._load_photos()
        images = self._clean_loaded(loaded_images)
        return images

    def _clean_loaded(self, images):
        data = []
        print "Loaded %s images" % len(images)
        for image in images:
            link = self._get_biggest_image_link(image)
            if link is not None:
                data.append({'href': link,
                             'source': self.source,
                             'likes': image['likes']['count'],
                             'share': image['reposts']['count'],
                             'comments': image['comments']['count']})
        return data

    @staticmethod
    def _get_biggest_image_link(photo_data):
        """
        Find biggest possible size
        """
        sizes = ['photo_1280', 'photo_807', 'photo_604', 'photo_130',
                 'photo_75']
        for size in sizes:
            if size in photo_data.keys():
                return photo_data[size]

    def _load_photos(self):
        data = self.api.get('wall.get', {'domain': self.source,
                                         'count': IMAGES_TO_LOAD})
        photos = []
        if data['items']:
            if not self.latest_post or \
                    self._check_photo_age(data['items'][0]['date']):

                photos = self._process_loaded_items(data['items'])
                self.latest_post = int(data['items'][0]['date'])
        return photos

    def _process_loaded_items(self, items):
        photos = []
        for item in items:
            if 'attachments' in item:
                if len(item['attachments']) == 1 and \
                                item['attachments'][0]['type'] == 'photo':

                    if self._check_post_age(item['date']):
                        if not self.latest_post == 0 or \
                                self._check_photo_age(item['date']):

                            photo = item['attachments'][0]['photo']
                            photo['likes'] = item['likes']
                            photo['comments'] = item['comments']
                            photo['reposts'] = item['reposts']
                            photo['posted'] = item['date']
                            photos.append(photo)
        return photos

    def _check_post_age(self, post_timestamp):
        return self._get_server_time() - int(post_timestamp) > 3600

    def _check_photo_age(self, post_timestamp):
        return int(post_timestamp) - self.latest_post > 3600

    def _get_server_time(self):
        return int(self.api.get('getServerTime', {}))
