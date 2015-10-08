from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.views.generic import View

from yunity.api.ids import user_id_uri_pattern, multiple_user_id_uri_pattern
from yunity.utils import status
from yunity.utils.api import ApiBase, body_as_json
from yunity.models import Category as CategoryModel


class UserAll(ApiBase, View):
    @body_as_json(expected_keys=['email', 'password', 'display_name'])
    def post(self, request):
        """register a new user
        ---
        tags:
            - User
        parameters:
            - in: body
              name: body
              schema:
                  id: create_user
                  required:
                    - email
                    - password
                    - display_name
                  properties:
                      email:
                          type: string
                          description: email address of new user
                          example: paul@example.com
                      password:
                          type: string
                          description: Password for user. Will be validated to specific rules
                          example: PaulsStrongPasswordWhichHeNeverForgets
                      display_name:
                          type: string
                          example: Paul
                          description: The public displayed name
        responses:
            201:
                description: User created
                schema:
                  id: user_information_response
                  allOf:
                          - $ref: '#/definitions/user_information'
                          - type: object
                            required:
                              - id
                            properties:
                              id:
                                type: number
                                description: Identifier of the User
                                example: 3
        ...

        :type request: HttpRequest
        """
        category = CategoryModel.objects.get(name='user.default')
        try:
            locations = [{
                'latitude': request.body['latitude'],
                'longitude': request.body['longitude'],
            }]
        except KeyError:
            locations = []

        user = get_user_model().objects.create_user(
            email=request.body['email'],
            password=request.body['password'],
            locations=locations,
            type=category,
            display_name=request.body['display_name'],
        )

        return self.created({"id": user.id,
                      "display_name": user.display_name})


class UserMultiple(ApiBase, View):
    def get(self, request, userids):
        """get details about all given users
        ---
        tags:
            - User
        parameters:
            - in: path
              name: userids
              type: array
              collectionFormat: csv
              items:
                  type: integer

        responses:
            201:
                description: User information
                schema:
                    type: object
                    properties:
                      users:
                        type: array
                        items:
                            $ref: '#/definitions/user_information_response'
        ...

        :type request: HttpRequest
        :type userids: [int]
        """
        userids = [int(_) for _ in userids.split(",")]
        users = get_user_model().objects\
            .filter(id__in=userids)\
            .values('id', 'display_name', 'picture_url')\
            .all()
        if len(users) != len(userids):
            return self.error(reason="one or more userids do not exist")

        return self.success({"users": [dict(_) for _ in users]})

class UserSingle(ApiBase, View):
    def put(self, request, userid):
        """Modify a user: Yourself or any user you have sufficient rights for.
        Only the provided fields will be changed. To clear fields, set them explicitly as empty.
        ---
        tags:
            - User
        parameters:
            - in: path
              name: userid
              type: integer
            - in: body
              name: body
              required: true
              schema:
                  id: user_information
                  properties:
                      display_name:
                        type: string
                        example: Paul
                        description: Display name of the user

        responses:
            201:
                description: User information
                schema:
                    $ref: '#/definitions/user_information_response'
            403:
                description: You are not allowed to modify that user

        :type request: HttpRequest
        :type userid: int
        """
        raise NotImplementedError


urlpatterns = [
    url(r'^$', UserAll.as_view()),
    url(r'^{userid}/?$'.format(userid=multiple_user_id_uri_pattern), UserMultiple.as_view()),
    url(r'^{userid}/?$'.format(userid=user_id_uri_pattern), UserSingle.as_view()),
]
