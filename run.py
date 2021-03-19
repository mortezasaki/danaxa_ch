from flask import Flask
from flask import escape
from flask import flash
from flask import abort
from functools import wraps
import heapq # heap used for qriority queue
from datetime import datetime
from flask import request

app = Flask(__name__)
app.secret_key = r"nQB}$c2j6YuNtRJ3)v(@fb[K_bt&kHpm%C:y.vSpPfNE,<feHM2H3k;[)rwmsP6Z"
# We can also use flask-login to handle authentication..
# Additionally, we can use Redis-server to store priority.
# Instead of using the name, we can use the IP address or the API key.
# Using Time for saving first request.
# The time becomes zero again when the interval between the first request 
# and the current request exceeds the expiration time.

# List of all users with a priority of them
users = {
    'Morteza' : {'Priority' : 5, 'Time' : None, 'Used' : 0},
    'Reza' : {'Priority' : 3, 'Time' : None, 'Used' : 0},
    'Ali' : {'Priority' : 7, 'Time' : None, 'Used' : 0},
    'Anonymous' : {'Priority' : 1, 'Time' : None, 'Used' : 0}, # The user is anonymous if he does not authenticate.
}

auth = {} # For storing user authentication information

def expiry_check(user_time : datetime, expiry_date : int = 60) -> bool:
    """Check if the first user request has expired.

    Args:
        user_time (datetime): [user first request time]
        expiry_date (int): [The rate limit will expire after 60 seconds]

    Returns:
        [bool]: [True if time is expired.]
    """
    return (datetime.now() - user_time).total_seconds() > expiry_date

# I'm using Decorator to restrict users per request.
# When a user sends more than the request intended for him,
# the program returns error 429, which means it's over the limit.
def rate_limit(f):
    @wraps(f)
    def func(*args, **kwargs):
        user = auth.get('Name', 'Anonymous')

        if user in users.keys():
            if users[user]['Time'] is None or expiry_check(users[user]['Time']):
                # Reset user priority after 60 seconds
                users[user]['Time'] = datetime.now()
                users[user]['Used'] = 0
            # if the user be in users list that not used all requests,
            users[user]['Used']+= 1 # Increase req used
            # if it still has priority
            if users[user]['Used'] <= users[user]['Priority']: 
                return f(*args, **kwargs) # The user has the privilege to execute the service
        
        
        # If the user doesn't have privilege,
        # it's assumed that the user used all the requests before the expiry date
        # return the status 429 to the user
        waiting_time = 60 - (datetime.now() - users[user]['Time']).total_seconds()
        description = '''This user has exceeded an allotted request count.
            Try again after %s seconds.''' % waiting_time
        abort(429, description = description)

    return func



@app.route("/")
def root():
    return('''Hi. This is the solution to Danaxa challenge #1.<br>
        First, login with /login?user=username<br>
        Second, send a request with /limited?x=msg'''
        )

@app.route("/limited")
@rate_limit
def limited_f():
    # Escape user input to prevent XSS attack
    x = escape(request.args.get('x'))
    user_name = auth.get('Name', 'Anonymous')
    valid_req_count = users[user_name]['Priority'] - users[user_name]['Used']
    return '''User name: %s<br>
        Your message is: %s<br>
        You can send %s more requests.''' %(user_name, x, valid_req_count)


@app.route("/login")
def login():
    user = request.args.get('user')
    if user is not None and user in users.keys():
        auth['Name'] = user
        user = escape(user)
        return 'Login as %s' % user
    else:
        auth['Name'] = 'Anonymous'
        return 'Log in anonymously.'

if __name__ == '__main__':
    app.run()
