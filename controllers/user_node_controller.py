from flask import request, Response
from handlers import add_user, verify_user, create_token, authorize


def signup():
    username = request.json["username"]
    password = request.json["password"]
    if username and password:
        username_already_exists = add_user(username, password)
        if username_already_exists:
            return Response("username already exits", status=403, mimetype='application/text')
        else:
            return Response("success", status=201, mimetype='application/text')
    else:
        return Response("missing parameters", status=400, mimetype='application/text')


def signin():
    username = request.json["username"]
    password = request.json["password"]
    if username and password:
        is_verified = verify_user(username, password)
        if is_verified:
            print("token")
            token = create_token(username, password)
            return Response("{'token': "+token+"}", status=200, mimetype='application/json')
        else:
            return Response("wrong password or username", status=403, mimetype='application/text')
    else:
        return Response("missing parameters", status=400, mimetype='application/text')


@authorize
def test(authorized_username):
    print(authorized_username)
    return Response("success", status=201, mimetype='application/text')
