import pymongo
from functools import wraps
from time import time

from flask import Flask, render_template, request, Response

app = Flask(__name__)

HOST = 'localhost'
PORT = 27017


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'obey' and password == 'motherfucker'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/')
@requires_auth
def dashboard():
    to = time()
    ms = MongoStorage()

    last_24 = ms.parsed(to - 86400, to)
    total = ms.parsed()
    sources = ms.get_sources()
    return render_template('dashboard.html', last_24=last_24, sources=sources,
                           total=total)


class MongoStorage(object):
    client = pymongo.MongoClient(HOST, PORT)
    db = client.funtastik_parser

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

    def parsed(self, from_=None, to=None):
        if all([from_, to]):
            criteria = {'posted': {'$gte': from_, '$lt': to}}
        else:
            criteria = {}
        return self.db.images.find({}, criteria).count()


if __name__ == '__main__':
    app.run(debug=True)
