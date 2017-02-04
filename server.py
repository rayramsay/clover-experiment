import os
import json

from flask import Flask, redirect, render_template, request, session

from clover_api import CloverAPI

app = Flask(__name__)

# Remember to ``source secrets.sh``!
app.secret_key = 'development'  # Required to use Flask sessions.
client_id = os.environ['APP_ID']
client_secret = os.environ['APP_SECRET']


def oauth_dance():
    # Syntax is .args for GET, .form for POST.
    code = request.args.get('code', None)
    if not code:
        return redirect("https://www.clover.com/oauth/authorize?client_id={}".format(client_id))

    resp = CloverAPI().get('/oauth/token',
                           client_id=client_id,
                           client_secret=client_secret,
                           code=code)

    try:
        # Store token in the session so we can use it later.
        session["access_token"] = resp.access_token
        session["merchant_id"] = request.args.get("merchant_id")
    except:
        # TODO: Error catching.
        raise


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

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
    resp = c.get('/v3/merchants/{mId}/orders')
    print resp

    return redirect('/')


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
