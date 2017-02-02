import os
import json

from httplib2 import Http
from flask import Flask, redirect, render_template, request, session

app = Flask(__name__)

# Remember to ``source secrets.sh``!
app.secret_key = 'development'  # Required to use Flask sessions.
client_id = os.environ['APP_ID']
client_secret = os.environ['APP_SECRET']
base_url = "https://sandbox.dev.clover.com"


@app.route('/', methods=['GET'])
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
        header, content = h.request("{}/oauth/token?client_id={}&client_secret={}&code={}".format(
            base_url,
            client_id,
            client_secret,
            code))
        content = json.loads(content)
        access_token = content.get("access_token")

        # Store this in the session so we can use it later.
        session["access_token"] = access_token

        merchant_id = request.args.get("merchant_id")
        # Now we can use this access token and merchant id with the API.

        header, content = h.request("{}/v3/merchants/{}/orders".format(
            base_url,
            merchant_id),
            headers={'Authorization': 'Bearer '+session.get("access_token")})

        print session
        print header
        print content
        return render_template("base.html")

################################################################################

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int("8000"), debug=True)
