from flask import request, Response
from handlers import add_user


def signup():
    username = request.json["username"]
    password = request.json["password"]
    if username and password:
        username_already_exists = add_user(username, password)
        if username_already_exists:
            return Response("username already exits", status=403, mimetype='application/json')
        else:
            return Response("success", status=201, mimetype='application/json')
    else:
        return Response("missing parameters", status=400, mimetype='application/json')
