from flask import request
from mock import patch
import time
from tests import BaseTestCase
from redash import models
from redash.google_oauth import create_and_login_user
from redash.authentication import api_key_load_user_from_request, hmac_load_user_from_request, sign
from tests.factories import user_factory, query_factory
from redash.wsgi import app


class TestApiKeyAuthentication(BaseTestCase):
    #
    # This is a bad way to write these tests, but the way Flask works doesn't make it easy to write them properly...
    #
    def setUp(self):
        super(TestApiKeyAuthentication, self).setUp()
        self.api_key = 10
        self.query = query_factory.create(api_key=self.api_key)

    def test_no_api_key(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{0}'.format(self.query.id))
            self.assertIsNone(api_key_load_user_from_request(request))

    def test_wrong_api_key(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{0}'.format(self.query.id), query_string={'api_key': 'whatever'})
            self.assertIsNone(api_key_load_user_from_request(request))

    def test_correct_api_key(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{0}'.format(self.query.id), query_string={'api_key': self.api_key})
            self.assertIsNotNone(api_key_load_user_from_request(request))

    def test_no_query_id(self):
        with app.test_client() as c:
            rv = c.get('/api/queries', query_string={'api_key': self.api_key})
            self.assertIsNone(api_key_load_user_from_request(request))

    def test_user_api_key(self):
        user = user_factory.create(api_key="user_key")
        with app.test_client() as c:
            rv = c.get('/api/queries/', query_string={'api_key': user.api_key})
            self.assertEqual(user.id, api_key_load_user_from_request(request).id)

    def test_api_key_header(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{}'.format(self.query.id), headers={'Authorization': "Key {}".format(self.api_key)})
            self.assertIsNotNone(api_key_load_user_from_request(request))

    def test_api_key_header_with_wrong_key(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{}'.format(self.query.id), headers={'Authorization': "Key oops"})
            self.assertIsNone(api_key_load_user_from_request(request))


class TestHMACAuthentication(BaseTestCase):
    #
    # This is a bad way to write these tests, but the way Flask works doesn't make it easy to write them properly...
    #
    def setUp(self):
        super(TestHMACAuthentication, self).setUp()
        self.api_key = 10
        self.query = query_factory.create(api_key=self.api_key)
        self.path = '/api/queries/{0}'.format(self.query.id)
        self.expires = time.time() + 1800

    def signature(self, expires):
        return sign(self.query.api_key, self.path, expires)

    def test_no_signature(self):
        with app.test_client() as c:
            rv = c.get(self.path)
            self.assertIsNone(hmac_load_user_from_request(request))

    def test_wrong_signature(self):
        with app.test_client() as c:
            rv = c.get(self.path, query_string={'signature': 'whatever', 'expires': self.expires})
            self.assertIsNone(hmac_load_user_from_request(request))

    def test_correct_signature(self):
        with app.test_client() as c:
            rv = c.get('/api/queries/{0}'.format(self.query.id), query_string={'signature': self.signature(self.expires), 'expires': self.expires})
            self.assertIsNotNone(hmac_load_user_from_request(request))

    def test_no_query_id(self):
        with app.test_client() as c:
            rv = c.get('/api/queries', query_string={'api_key': self.api_key})
            self.assertIsNone(hmac_load_user_from_request(request))

    def test_user_api_key(self):
        user = user_factory.create(api_key="user_key")
        path = '/api/queries/'
        with app.test_client() as c:
            signature = sign(user.api_key, path, self.expires)
            rv = c.get(path, query_string={'signature': signature, 'expires': self.expires, 'user_id': user.id})
            self.assertEqual(user.id, hmac_load_user_from_request(request).id)

class TestCreateAndLoginUser(BaseTestCase):
    def test_logins_valid_user(self):
        user = user_factory.create(email='test@example.com')

        with patch('redash.google_oauth.login_user') as login_user_mock:
            create_and_login_user(user.name, user.email)
            login_user_mock.assert_called_once_with(user, remember=True)

    def test_creates_vaild_new_user(self):
        email = 'test@example.com'
        name = 'Test User'

        with patch('redash.google_oauth.login_user') as login_user_mock:

            create_and_login_user(name, email)

            self.assertTrue(login_user_mock.called)
            user = models.User.get(models.User.email == email)