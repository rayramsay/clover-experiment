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
        raise Exception("OAuth error!")


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
    resp = c.get("/v3/merchants/{mId}/orders")

    # The response dict contains `href` and `elements`, the latter being the
    # list of orders.
    orders = resp["elements"]

    return render_template("orders.html",
                           orders=orders,
                           interaction="list")


@app.route('/orders/create', methods=['GET', 'POST'])
def create_order():
    '''Create an order.'''
    if request.method == "GET":
        return render_template("new_order.html")

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

    return redirect('/')


@app.route('/orders/ice_cream', methods=['POST'])
def order_ice_cream():
    '''Creates an order with an ice cream line item.'''

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))

    # Create order.
    resp = c.post("/v3/merchants/{mId}/orders",
                  {"state": "open",
                   "note": "ice cream"})

    # Get ID from response.
    order_id = resp.id

    # Add line item to order. Nb. At a minimum this request must include a price
    # or a reference to an inventory item.
    resp = c.post("/v3/merchants/{mId}/orders/{orderId}/line_items",
                  {"name": "ice cream",
                   "price": 100},
                  orderId=order_id)

    message = "You ordered ice cream!"
    flash(message)

    return redirect('/')


@app.route('/orders/<interaction>', methods=['GET', 'POST'])
def update_orders(interaction):
    '''Close or delete the selected orders.'''

    c = CloverAPI(session.get("access_token"), session.get("merchant_id"))

    if request.method == "GET":
            resp = c.get("/v3/merchants/{mId}/orders")

            # The response dict contains `href` and `elements`, the latter being the
            # list of orders.
            orders = resp["elements"]

            return render_template("orders.html",
                                   orders=orders,
                                   interaction=interaction)

    # POST
    # Syntax is `.getlist` because multiple checkboxes may have been checked.
    order_ids = request.form.getlist("order_id")

    for order_id in order_ids:

        if interaction == "close":
            c.post("/v3/merchants/{mId}/orders/{orderId}",
                   {"state": "closed"},  # Setting this field to null means order can only be GET by id.
                   orderId=order_id)

        elif interaction == "delete":
            c.delete("/v3/merchants/{mId}/orders/{orderId}",
                     orderId=order_id)

        message = "Order #{} {}d.".format(order_id, interaction)
        flash(message)

    return redirect('/')


################################################################################

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int("8000"), debug=True)
