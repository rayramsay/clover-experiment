# Modified from https://github.com/clover/example-server/

import requests
import json
import re


class CloverResponseObject(dict):
    """Object to encapsulate response JSON."""
    def __init__(self, obj):
        for key, value in obj.items():
            self.__dict__[key] = value
        dict.__init__(self, obj)


class CloverAPI(object):
    """CloverAPI object for making API calls to Clover's server."""

    base_url = "https://apisandbox.dev.clover.com"  # Change to https://api.clover.com in production.
    path_match = re.compile("\{([a-zA-Z]*)\}")

    def __init__(self, access_token=None, merchant_id=None):
        """Makes a CloverAPI object.

        Args:
            access_token: Token to access Clover's API, appended as a URL
                          parameter, if present
            merchant_id: Replaces "{mId}" in the endpoint URL, if present
        Returns:
            A CloverAPI object
        """
        self.access_token = access_token
        self.merchant_id = merchant_id

    def get(self, endpoint, **kwargs):
        """Send a get request using Clover's API

        Extra query parameters will be formatted in the URL. For example, if
        itemId is passed in as a keyword argument and "{itemId}" is in the
        endpoint url, "{itemId}" will be replaced with the value of that
        argument. If "{itemId}" is not present, the argument will be added as a
        query parameter in the URL.

        Args:
            endpoint: Clover endpoint's url
            **kwargs: Any other parameters.
        Returns:
            A CloverResponseObject converted from the response JSON, which
            allows access to values in the JSON object. For example, if the JSON
            object is: {name: "My Merchant Name"}, to get the name from the
            corresponding CloverResponseObject, use: `response.name`
        Raises:
            requests.exceptions.HTTPError: If Clover's server returns an error
                                           code between 400 and 599.
        """
        return self._send("GET", endpoint, **kwargs)

    def post(self, endpoint, data, **kwargs):
        """Send a post request using Clover's API.

        See documentation for `get`

        Args:
            endpoint: See documentation for `get`
            data: A python object to convert to a JSON object to send
            **kwargs: See documentation for `get`
        Returns:
            See documentation for `get`
        Raises:
            See documentation for `get`
        """
        return self._send("POST", endpoint, data, **kwargs)

    def delete(self, endpoint, **kwargs):
        """Send a post request using Clover's API.

        See documentation for `get`

        Args:
            endpoint: See documentation for `get`
            data: A python object to convert to a JSON object to send
            **kwargs: See documentation for `get`
        Returns:
            See documentation for `get`
        Raises:
            See documentation for `get`
        """
        return self._send("DEL", endpoint, **kwargs)

    def _send(self, method, endpoint, data={}, **kwargs):
        # Set parameters
        parameters = kwargs
        if self.access_token:
            parameters["access_token"] = self.access_token
        if self.merchant_id:
            parameters["mId"] = self.merchant_id

        # Replace user-defined path parameters
        path_params = CloverAPI.path_match.findall(endpoint)
        for key in path_params:
            if key in parameters:
                endpoint = endpoint.replace('{%s}' % key, parameters[key])
                parameters.pop(key)
            else:
                raise KeyError("Missing path parameter: " + key)

        url = CloverAPI.base_url + endpoint

        # Send request
        if method == "POST":
            headers = {}
            headers["content-type"] = "application/json"
            response = requests.post(url, headers=headers, params=parameters,
                                     data=json.dumps(data))
        elif method == "GET":
            response = requests.get(url, params=parameters)

        elif method == "DEL":
            response = requests.delete(url, params=parameters)

        error_msg = None
        if 400 <= response.status_code < 500:
            error_msg = '%s Client Error: %s\n%s'
        elif 500 <= response.status_code < 600:
            error_msg = '%s Server Error: %s\n%s'

        if error_msg:
            raise requests.exceptions.HTTPError(
                error_msg % (response.status_code, response.reason, response.text),
                response=response
            )

        # Clover always returns JSON object in response

        return json.loads(response.content, object_hook=CloverResponseObject)
