import time
from flask import request
from flask.ext.restful import abort
from funcy import project
from peewee import IntegrityError

from redash import models
from redash.wsgi import api
from redash.tasks import record_event
from redash.permissions import require_permission, require_admin_or_owner, is_admin_or_owner, \
    require_permission_or_owner
from redash.handlers.base import BaseResource, require_fields


class UserListResource(BaseResource):
    @require_permission('list_users')
    def get(self):
        return [u.to_dict() for u in models.User.select()]

    @require_permission('admin')
    def post(self):
        # TODO: send invite.
        req = request.get_json(force=True)
        require_fields(req, ('name', 'email', 'password'))

        user = models.User(name=req['name'], email=req['email'])
        user.hash_password(req['password'])
        try:
            user.save()
        except IntegrityError as e:
            if "email" in e.message:
                abort(400, message='Email already taken.')

            abort(500)

        record_event.delay({
            'user_id': self.current_user.id,
            'action': 'create',
            'timestamp': int(time.time()),
            'object_id': user.id,
            'object_type': 'user'
        })

        return user.to_dict()


class UserResource(BaseResource):
    def get(self, user_id):
        require_permission_or_owner('list_users', user_id)
        user = models.User.get_by_id(user_id)
        
        return user.to_dict(with_api_key=is_admin_or_owner(user_id))

    def post(self, user_id):
        require_admin_or_owner(user_id)
        user = models.User.get_by_id(user_id)

        req = request.get_json(True)

        params = project(req, ('email', 'name', 'password', 'old_password', 'groups'))

        if not self.current_user.has_permission('admin'):
            if 'password' in params and 'old_password' not in params:
                abort(403, message="Must provide current password to update password.")

        if not self.current_user.has_permission('admin'):
            if 'old_password' in params and not user.verify_password(params['old_password']):
                abort(403, message="Incorrect current password.")

        if 'password' in params:
            user.hash_password(params.pop('password'))
            params.pop('old_password')

        if 'groups' in params and not self.current_user.has_permission('admin'):
            abort(403, message="Must be admin to change groups membership.")

        try:
            user.update_instance(**params)
        except IntegrityError as e:
            if "email" in e.message:
                message = "Email already taken."
            else:
                message = "Error updating record"

            abort(400, message=message)

        record_event.delay({
            'user_id': self.current_user.id,
            'action': 'edit',
            'timestamp': int(time.time()),
            'object_id': user.id,
            'object_type': 'user',
            'updated_fields': params.keys()
        })

        return user.to_dict(with_api_key=is_admin_or_owner(user_id))


api.add_resource(UserListResource, '/api/users', endpoint='users')
api.add_resource(UserResource, '/api/users/<user_id>', endpoint='user')


