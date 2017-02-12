'''
How do I use the Web API to pay for an order?
1. GET to /v2/merchant/{mId}/pay/key to get the encryption information you'll
need for the pay endpoint.
2. Encrypt the card information.
    2a. Prepend the card number with the prefix from GET /v2/merchant/{mId}/pay/key.
    2b. Generate an RSA public key using the modulus and exponent provided by
    GET /v2/merchant/{mId}/pay/key.
    2c. Encrypt the card number and prefix from step 1 with the public key.
    2d. Base64 encode the resulting encrypted data into a string which you will
    send to Clover in the "cardEncrypted" field.
3. POST to /v2/merchant/{mId}/pay Pass the encrypted card data and order
information to Clover in order to pay for the order.
    Note: If you are using the same credit card on the same merchant account,
    you can send the token in the paylod instead ofcardEncrypted, first6, last4,
    cvv, expMonth, expYear, and zip.
'''

import os
import requests
import base64
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

base_url = "https://apisandbox.dev.clover.com"
access_token = os.environ['OAUTH_TOKEN']
merchant_id = os.environ['MERCH_ID']

##### Mock card information #####
card_number = "1234567891011121"
cvv = "123"
exp_month = 1
exp_year = 2018
billing_zip = "94085"

#### Mock order information #####
order_id = "3NB7WKMHJMJH6"
tax_amount = 9
amount = 100
currency = "usd"

# GET to /v2/merchant/{mId}/pay/key to get the encryption information.

url = base_url + '/v2/merchant/' + merchant_id + '/pay/key'
headers = {"Authorization": "Bearer " + access_token}
resp = requests.get(url, headers=headers).json()

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

# POST to /v2/merchant/{mId}/pay Pass the encrypted card data and order info.

url = base_url + '/v2/merchant/' + merchant_id + '/pay/'
payload = {
    "orderId": order_id,
    "taxAmount": tax_amount,
    "zip": billing_zip,
    "expMonth": exp_month,
    "expYear": exp_year,
    "cvv": cvv,
    "amount": amount,
    "currency": currency,
    "last4": card_number[-4:],
    "first6": card_number[0:6],
    "cardEncrypted": card_encrypted
}

resp = requests.post(url, headers=headers, data=payload).json()

print resp
