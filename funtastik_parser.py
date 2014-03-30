# -*- coding: utf-8 -*-
import requests

ACCESS_KEY = 'AKIAI2SXOF6YS3UOMEWA'
SECRET_ACCESS_KEY = 'KVy3qguXvVDYVkTDlO5W+G+5D4F4dGi92svuq2p'


class VkApiServer(object):
    API_VERSION = '5.16'
    API_ID = '4274771'
    API_SECRET = 'EV9LaqJCOpmDaA6afbgz'
    API_URL = 'http://api.vk.com/method/'
    # TODO: 3 запроса в секунду

    def _params(self, method_params):
        params = {
            'api_id': self.API_ID,
            'format': 'JSON',
            'v': self.API_VERSION
        }

        params.update(method_params)
        return params

    def get(self, method, method_params):
        """ return response (dict) """

        params = self._params(method_params)
        response = requests.get(self.API_URL + method, params=params)
        response_json = response.json()

        if 'response' in response_json:
            return response_json['response']

        if 'error' in response_json:
            error = response_json['error']

            raise Exception('VkApi error (%s): %s' % (
                error['error_code'],
                error['error_msg'])
            )


class Source(object):
    def __init__(self, target, count, start_from=None):
        self.target = target
        self.count = count
        self.start_from = start_from
        self.parser = VkApiServer()

    def load_images(self):
        photos = self.__get_wall_photos()
        if photos:
            links = self.__get_links(photos)
            return links

    def __get_wall_photos(self):
        data = self.parser.get('wall.get', {'domain': self.target})
        photos = []
        for item in data['items']:
            if 'attachments' in item and len(item['attachments']) == 1 and \
                            item['attachments'][0]['type'] == 'photo':
                print item['attachments'][0]['photo']
                photos.append(item['attachments'][0]['photo']['id'])
                # k = {
                #                   'owner_id': item['attachments'][0]['photo']['owner_id'],
                #                   'id': item['attachments'][0]['photo']['id'],
                #                   'access_key': item['attachments'][0]['photo']['access_key']}

        # TODO: вынести в другую функцию?
        if photos:
            params = {
                'photo_ids': ','.join([str(i) for i in photos]),
                'owner_id': data['items'][0]['owner_id'],
                'album_id': 'wall',
                'extended': 0,
                'photo_sizes': 1
            }

            return params

    def __get_links(self, photo_ids):
        photos = self.parser.get('photos.get', photo_ids)
        print photos
        links = []
        for photo in photos['items']:
            link = self.__get_biggest_image_link(photo['sizes'])
            links.append(link)
        return links

    @staticmethod
    def __get_biggest_image_link(image_sizes):
        print image_sizes
        sizes = ['w', 'z', 'y', 'x', 'm', 's']
        d = dict([(i['type'], i['src']) for i in image_sizes])
        for s in sizes:
            if s in d.keys():
                return d[s]

    def __download(self):
        pass


if __name__ == '__main__':
    s = Source('mdk', 10)
    print s.load_images()

    # for k in s.load_images():
    #
    #     if 'attachments' in k:
    #         if len(k['attachments']):
    #             print k['attachments'][0]
    #         for m in k['attachments']:
    #             pass
    # print m['photo'].keys(), '\n'
