import os

from flask import Flask, flash, redirect, render_template, request, session

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

    resp = CloverAPI().get("/oauth/token",
                           client_id=client_id,
                           client_secret=client_secret,
                           code=code)

    access_token = resp.get("access_token")
    merchant_id = request.args.get("merchant_id")

    if access_token and merchant_id:
        # Store in the session so we can use them later.
        session["access_token"] = access_token
        session["merchant_id"] = merchant_id
    else:
        #TODO: Error handling.
        raise Exception("Oauth error!")


@app.route('/', methods=['GET'])
def home_page():
    if not session.get("access_token"):
        oauth_dance()

    # Create CloverAPI instance with access token and merchant id.
    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
    # Make API call.
    merchant = c.get("/v3/merchants/{mId}")

    return render_template("home.html",
                           merchant=merchant)


################################################################################
# Order-related routes
################################################################################

@app.route('/orders', methods=['GET'])
def order_list():
    '''Display orders.'''

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
    orders = c.get("/v3/merchants/{mId}/orders")
    print orders
    return redirect('/')


@app.route('/orders/create', methods=['GET'])
def new_order_form():
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
    # appear in the Orders app."

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
    resp = c.post("/v3/merchants/{mId}/orders",
                  {"state": "open",
                   "total": total,
                   "note": note})

    order_id = resp.id
    message = "Order #{} created.".format(order_id)
    flash(message)

    print resp
    return redirect('/')


@app.route('/orders/update', methods=['GET'])
def update_orders_form():
    '''Display form for updating orders.'''

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
    resp = c.get("/v3/merchants/{mId}/orders")
    # The response dict contains `href` and `elements`, the latter being the list of orders.
    orders = resp["elements"]
    print orders
    return render_template("update_orders.html",
                           orders=orders,
                           interaction="close")


@app.route('/orders/update', methods=['POST'])
def close_order():
    '''Close the selected order.'''

    # Get the values from the form.
    order_id = request.form.get("order_id")

    if order_id:
        c = CloverAPI(session.get("access_token"), session.get("merchant_id"))
        c.post("/v3/merchants/{mId}/orders/{orderId}",
               {"state": None},
               orderId=order_id)

        message = "Order #{} was closed.".format(order_id)
        flash(message)

    return redirect('/')


################################################################################

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int("8000"), debug=True)
