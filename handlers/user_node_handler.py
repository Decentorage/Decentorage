import bcrypt
import app


def add_user(username, password):
    """
    Add user to the system
    When a user sign up for the first time this function hash the password given, then add user to database
    *Parameters:*
        - *username(string)*: holds the value of the username.
        - *password(string)*: holds the value of the password.
    *Returns:*
       - boolean value one indicates if the username already exists.
    """
    if app.database:
        users = app.database["user"]
    else:
        return "database error"
    query = {"username": username}
    user = users.find_one(query)
    if user:
        return True
    # Hash a password for the first time, with a randomly-generated salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({"username": username, "password": hashed_password.decode('utf-8'), 'requests': [],
                      'active_contracts': []})
    return False
