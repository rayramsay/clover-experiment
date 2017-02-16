import os
import base64
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from clover_api import CloverAPI, CloverResponseObject
from mocks import mock_card, mock_order


def pay_online(access_token, merchant_id, card, pay_info):
    """Pay for an order online.
        Args:
            access_token: Token to access Clover's API
            merchant_id: Replaces "{mId}" in the endpoint URL
            card: A credit card object with the following attributes:
                number: card number
                ccv: card verification value
                exp_month: expiry month
                exp_year: expiry year
                zipcode: billing zip code
            pay_info: A payment information object with the following attributes:
                order_id
                tax_amount
                amount: amount to be paid toward this order (not necessarily the
                    order total)
                currency: e.g., "usd"
        Returns:
            A CloverAPI response object
    """

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
    card_encrypted = cipher.encrypt(prefix + card.number)

    # Base64 encode the resulting encrypted data into a string.

    card_encrypted = base64.b64encode(card_encrypted)

    # POST encrypted card data and payment info to /v2/merchant/{mId}/pay.

    payload = {
        "orderId": pay_info.order_id,
        "taxAmount": pay_info.tax_amount,
        "zip": card.zipcode,
        "expMonth": card.exp_month,
        "expYear": card.exp_year,
        "cvv": card.cvv,
        "amount": pay_info.amount,
        "currency": pay_info.currency,
        "last4": card.number[-4:],
        "first6": card.number[0:6],
        "cardEncrypted": card_encrypted
        }

    resp = c.post("/v2/merchant/{mId}/pay",
                  payload)

    return resp

################################################################################

if __name__ == "__main__":

    access_token = os.environ['STRICT_TOKEN']
    merchant_id = os.environ['STRICT_ID']
    card = CloverResponseObject(mock_card)
    info = CloverResponseObject(mock_order)

    print pay_online(access_token, merchant_id, card, info)
