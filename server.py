import os
import json

from httplib2 import Http
from flask import Flask, redirect, render_template, request, session

app = Flask(__name__)

# Remember to ``source secrets.sh``!
app.secret_key = 'development'  # Required to use Flask sessions.
client_id = os.environ['APP_ID']
client_secret = os.environ['APP_SECRET']
base_url = "https://sandbox.dev.clover.com"  # Change to https://api.clover.com in production.


def oauth_dance():
    # Syntax is .args for GET, .form for POST.
    code = request.args.get('code', None)
    if not code:
        return redirect("https://www.clover.com/oauth/authorize?client_id={}".format(client_id))

    else:
        # "The code value can be used to obtain an authcode by calling the
        # /oauth/token endpoint with your client_id (the ID of your app),
        # client_secret (the app secret listed on your dashboard apps page),
        # and the value of the code query parameter. The response to this
        # request will include a JSON object containing an access_token."

        h = Http()
        header, content = h.request(base_url+"/oauth/token?client_id={}&client_secret={}&code={}".format(
            client_id,
            client_secret,
            code))

        content = json.loads(content)
        access_token = content.get("access_token")

        if not access_token:
            #TODO: Some kind of error handling.
            pass

        # Store this in the session so we can use it later.
        session["access_token"] = access_token
        session["merchant_id"] = request.args.get("merchant_id")


@app.route('/', methods=['GET'])
def home_page():
    if not session.get("access_token"):
        oauth_dance()
    return render_template("home.html")


################################################################################
# Order-related routes
################################################################################

@app.route('/orders', methods=['GET'])
def order_list():
    '''Display orders.'''

    h = Http()
    header, content = h.request(base_url+"/v3/merchants/{}/orders".format(
        session.get("merchant_id")),
        headers={'Authorization': 'Bearer '+session.get("access_token")})

    return content


@app.route('/orders/create', methods=['GET'])
def order_form():
    '''Display form for creating a new order.'''
    return render_template("new_order.html")


@app.route('/orders/create', methods=['POST'])
def create_order():
    '''Create an order.'''

    # Get the values from the form.
    note = request.form.get("note")
    total = int(request.form.get("total"))

    # "Please note, this basic Order object will be treated as unfinished if the
    # Order's state is null. Before the order has first been set to "open", it
    # will only be possible to GET the individual order by its id, but it will
    # not otherwise be included in the merchant's order list, it will also not
    # appear in the Orders app.

    body = json.dumps({"state": "open", "total": total, "note": note})

    h = Http()
    header, content = h.request(base_url+"/v3/merchants/{}/orders".format(
        session.get("merchant_id")),
        method="POST",
        headers={'Authorization': 'Bearer '+session.get("access_token"), 'Content-Type': 'application/json'},
        body=body)

    #TODO: Add flash message: "Order was created." (Maybe pull in order ID from response content?)

    #print content

    return redirect('/')

################################################################################

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int("8000"), debug=True)
