import os
import base64
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from clover_api import CloverAPI
from mocks import mock_card


def encrypt_card(access_token, merchant_id, card_number):

    # Create CloverAPI instance with access token and merchant id.
    c = CloverAPI(access_token, merchant_id)

    # GET encryption information from /v2/merchant/{mId}/pay/key.
    resp = c.get("/v2/merchant/{mId}/pay/key")

    prefix = str(resp["prefix"])
    modulus = long(resp["modulus"])
    exponent = long(resp["exponent"])

    # Generate an RSA public key using the modulus and exponent.
    public_key = RSA.construct((modulus, exponent))

    # Encrypt the card number and prefix with the public key.
    cipher = PKCS1_OAEP.new(public_key)
    card_encrypted = cipher.encrypt(prefix + card_number)

    # Base64 encode the resulting encrypted data into a string.
    card_encrypted = base64.b64encode(card_encrypted)

    return card_encrypted

################################################################################

if __name__ == "__main__":

    access_token = os.environ['STRICT_TOKEN']
    merchant_id = os.environ['STRICT_ID']
    card_number = mock_card["number"]
    token = None  # TODO: Fill me in!
    payload = {
        "orderId": None,  # TODO: Fill me in!
        "taxAmount": 0,
        "amount": 100,
        "currency": "usd"
        }

    if token:
        # Add the token to the payload.
        payload["token"] = token

    else:
        # Encrypt the card number; add it and the other card information to the
        # payload.
        card_encrypted = encrypt_card(access_token, merchant_id, card_number)
        payload["cardEncrypted"] = card_encrypted
        for key, item in mock_card.iteritems():
            if key != "number":
                payload[key] = item

    c = CloverAPI(access_token, merchant_id)
    resp = c.post("/v2/merchant/{mId}/pay",
                  payload)

    print resp
