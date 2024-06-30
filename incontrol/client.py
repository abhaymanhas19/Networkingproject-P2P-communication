"""
Copyright (c) 2018, 2024 Eleuterio Millan Jr
All rights reserved.

This API client library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library. If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import logging
import mock
import requests
import requests.auth


_BASE_URL = "https://api.ic.peplink.com/rest/o"
_TOKEN_URL = "https://api.ic.peplink.com/api/oauth2/token"
_logger = logging.getLogger(__name__)


class API(object):
    """
    This class provides an interface for interacting with the InControl API. It handles
    authentication using client credentials and provides methods to fetch tokens, organizations,
    groups, device information, and SIM usage data. The class encapsulates the necessary details
    to perform API requests, manage authentication tokens, and parse responses.

    Attributes:
        _client_id (str): The client ID used for authentication.
        _client_secret (str): The client secret used for authentication.
        _auth_token (str): The authentication token obtained from the API.
        _refresh_token (str): The refresh token obtained from the API for renewing the auth token.
        _req_params (dict): A dictionary of request parameters, including the access token.
        _org_id (str): The organization ID obtained during initialization.

    Methods:
        __init__: Initializes the API client with client ID and secret, retrieves tokens and sets up initial data.
        get_tokens: Retrieves access and refresh tokens from the API.
        get_organizations: Fetches a list of organizations from the API.
        get_groups: Fetches a list of groups for a specified organization.
        get_group_devices: Fetches a list of devices for a specified group.
        get_device_location: Retrieves the location of a specific device.
        get_sim_usages: Fetches SIM usage data for a specified device within a date range.
        get_sim_pools: Retrieves information about SIM pools associated with a group.
        _get_data: Internal method to perform a GET request to the API and return the data.
    """

    _client_id = None
    _client_secret = None
    _auth_token = None
    _refresh_token = None
    _req_params = {}
    _org_id = None

    @classmethod
    def get_tokens(cls, client_id, client_secret, refresh=False, refresh_token=None):
        """ Returns access token and refresh token as (Mock) object attributes
        args:
            refresh (bool): set to True if renewing a token
            refesh_token (str) : required if refresh param is True
        returns:
            mock.Mock(access_token, refresh_token)

        example:
        """

        post_data = {
            "client_id": client_id,
            "client_secret":client_secret,
        }
        if refresh:
            post_data["grant_type"] = "refresh_token"
            post_data["refresh_token"] = refresh_token
        else:
            post_data["grant_type"] = "client_credentials"

        response = {}
        try:
            response = requests.post(_TOKEN_URL, data=post_data, timeout=120)
        except Exception as e:
            _logger.error('Could not get access tokens. %s', e, exc_info=True)

        api_tokens = mock.Mock(access_token=None, refresh_token=None)
        if response and response.status_code == 200:
            api_tokens.access_token = response.json().get("access_token")
            api_tokens.refresh_token = response.json().get("refresh_token")

        return api_tokens

    def _get_data(self, endpoint_url, params=None):
        """
        A function to retrieve data from a specified endpoint URL with optional parameters.

        Args:
            self: The instance of the class.
            endpoint_url: The URL of the endpoint to retrieve data from.
            params: Optional parameters to be included in the request. Defaults to None.

        Returns:
            The retrieved data from the endpoint URL, or None if unsuccessful.
        """

        if not params:
            params = {}
        params['access_token'] = self._auth_token
        response = {}
        try:
            response = requests.get(endpoint_url, params=params, timeout=120)
        except Exception as e:
            _logger.error('Could not get data. %s', e, exc_info=True)
        status_code = getattr(response, 'status_code', None)
        if (status_code == 200
                and response.json().get("resp_code") in ('SUCCESS', 'PENDING')):
            _logger.info(f"Successfully fetched data from {endpoint_url}: {response.json()}")
            return response.json().get("data", None)
        elif status_code in (401, 403):
            # retry using new token
            try:
                tokens = self.get_tokens(self._client_id, self._client_secret)
                self._auth_token = tokens.access_token
                self._refresh_token = tokens.refresh_token
                self._req_params["access_token"] = tokens.access_token
                self.__class__._auth_token = tokens.access_token
                self.__class__._refresh_token = tokens.refresh_token
                self.__class__._req_params["access_token"] = tokens.access_token
                params['access_token'] = tokens.access_token
                response = requests.get(endpoint_url, params=params, timeout=120)
                status_code = getattr(response, 'status_code', None)
                resp_json = {}
                if status_code == 200:
                    resp_json = response.json()
                if status_code == 401:
                    msg = f'Unauthorized Refresh. using params {params}. Endpoint URL: {endpoint_url}'
                    raise Exception(msg)
                if status_code == 200 and resp_json.get("resp_code") == 'SUCCESS':
                    return response.json().get("data", None)
            except Exception as e:
                _logger.error('Could not get refresh token. %s', e, exc_info=True)
        return None

    def __init__(self, client_id, client_secret):
        """
        Initialize the API client with the provided client ID and client secret.

        Args:
            client_id: The client ID used for authentication.
            client_secret: The client secret used for authentication.

        Returns:
            None
        """

        tokens = self.get_tokens(client_id, client_secret)
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_token = tokens.access_token
        self._refresh_token = tokens.refresh_token
        self._req_params["access_token"] = tokens.access_token
        params = {"access_token": tokens.access_token}
        self.__class__._auth_token = tokens.access_token
        self.__class__._req_params["access_token"] = tokens.access_token
        self.__class__._refresh_token = tokens.refresh_token
        data = self._get_data(_BASE_URL, params=params)
        if not data:
            raise Exception("Could not initialize InControl API client")
        self._org_id = data[0].get("id")
        return None

    def get_organizations(self, params=None):
        """
        A function to get the organizations.

        Returns:
            A list of organizations or an empty list if no organizations are found.
        """
        # endpoint_vars = {
        #     "base_url": _BASE_URL
        # }
        # endpoint_url = "{base_url}".format(**endpoint_vars)

        res = self._get_data(_BASE_URL)
        return [] if res is None else res

    def get_sim_pools(self, group_id=0):
        """
        A function to get the SIM pools based on the group ID.

        Args:
            group_id: The ID of the group. Defaults to 1.

        Returns:
            A list of SIM pools or an empty list if no SIM pools are found.
        """
        endpoint_vars = {
            "base_url": _BASE_URL,
            "organization_id": self._org_id,
            "group_id": group_id
        }
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/sim_pools".format(**endpoint_vars)
        res = self._get_data(endpoint_url)
        return [] if res is None else res

    def get_sim_usages(self, usage_type, start_date=None, end_date=None, organization_id=None, group_id=0, device_id=1):
        """
        A function to get SIM usages based on the specified parameters.

        Args:
            usage_type (str): Type of usage - hourly, daily, or monthly.
            start_date (date): The start date in the format yyyy-MM-dd.
            end_date (date): The end date in the format yyyy-MM-dd.
            organization_id (str, optional): The ID of the organization. Defaults to None.
            group_id (int, optional): The ID of the group. Defaults to 1.
            device_id (int, optional): The ID of the device. Defaults to 1.

        Returns:
            A list of SIM usages data or an empty list if no data is found.
        """

        if not organization_id:
            organization_id = self._org_id

        if not end_date:
            # set to current date
            end_date = datetime.datetime.utcnow().date()

        if not start_date:
            # set to 7 days before end date
            start_date = end_date - datetime.timedelta(days=7)

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id,
            "group_id": group_id,
            "device_id": device_id,
            "usage_type": usage_type
        }
        query_params = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/d/{device_id}/sim_usages/{usage_type}"
        endpoint_url = endpoint_url.format(**path_vars)
        res = self._get_data(endpoint_url, params=query_params)
        return [] if res is None else res

    def get_devices(self, organization_id=None, **kwargs):
        """
        A function to get the devices based on the organization ID.

        Args:
            organization_id: The ID of the organization.

        Returns:
            A list of devices or an empty list if no devices are found.
        """

        if not organization_id:
            organization_id = self._org_id

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id
        }
        endpoint_url = "{base_url}/{organization_id}/d"
        endpoint_url = endpoint_url.format(**path_vars)
        res = self._get_data(endpoint_url, params=kwargs)
        return [] if res is None else res

    def get_groups(self, organization_id=None):
        """
        A function to get the groups based on the organization ID.

        Args:
            organization_id: The ID of the organization. Defaults to None.

        Returns:
            A list of groups or an empty list if no groups are found.
        """
        if not organization_id:
            organization_id = self._org_id

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id
        }

        endpoint_url = "{base_url}/{organization_id}/g"
        endpoint_url = endpoint_url.format(**path_vars)
        res = self._get_data(endpoint_url)
        return [] if res is None else res

    def get_grouped_networks(self, organization_id, group_id=0):
        """
        A function to get the grouped networks based on the organization ID and group ID.

        Args:
            organization_id: The ID of the organization.
            group_id: The ID of the group. Defaults to 0.

        Returns:
            A list of grouped networks or an empty list if no grouped networks are found.
        """
        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id,
            "group_id": group_id
        }
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/grouped_networks"
        endpoint_url = endpoint_url.format(**path_vars)
        res = self._get_data(endpoint_url)
        return [] if res is None else res


    def get_bandwidth(self, organization_id, group_id=0, period_type='hourly', start_date=None, end_date=None):
        """
        A function to get the bandwidth usage based on the organization ID, group ID, type, start date, and end date.

        Args:
            organization_id: The ID of the organization.
            group_id: The ID of the group. Defaults to 0.
            period_type: The type of bandwidth usage. Defaults to 'hourly'. ('hourly', 'daily', 'monthly')
            start_date: The start date of the bandwidth usage. Defaults to None.
            end_date: The end date of the bandwidth usage. Defaults to None.

        Returns:
            A list of bandwidth usage or an empty list if no bandwidth usage is found.
        """
        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id,
            "group_id": group_id
        }
        query_params = {
            "type": period_type,
            "start": start_date.strftime("%Y-%m-%d") if start_date else None,
            "end": end_date.strftime("%Y-%m-%d") if end_date else None
        }
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/bandwidth".format(**path_vars)
        endpoint_url = endpoint_url.format(**path_vars)
        res = self._get_data(endpoint_url, params=query_params)
        return [] if res is None else res


    def get_device_location(self, organization_id, group_id, device_id):
        """
        A function to retrieve the location of a device based on organization ID, group ID, and device ID.

        Args:
            organization_id: The ID of the organization to which the device belongs.
            group_id: The ID of the group to which the device belongs.
            device_id: The unique ID of the device.

        Returns:
            A dictionary containing the device location information (latitude, longitude, and location timestamp)
            if found, otherwise an empty dictionary.
        """

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id,
            "group_id": group_id,
            "device_id": device_id
        }
        device_fields = ["latitude", "longitude", "location_timestamp"]
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/d/{device_id}/info"
        device_loc = self._get_data(endpoint_url.format(**path_vars), params={"field": device_fields})

        return {} if device_loc is None else device_loc

    def get_group_devices(self, organization_id=None, group_id=None):
        """
        A function to get the devices of a group based on the organization ID and group ID.

        Args:
            organization_id: The ID of the organization. Defaults to None.
            group_id: The ID of the group. Defaults to None.

        Returns:
            A list of devices per group or an empty list if no devices are found.
        """
        if not organization_id:
            organization_id = self._org_id

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id
        }
        if group_id:
            group_ids = [group_id]
        else:
            # get all groups if none is specified
            group_ids = [g.get('id') for g in self.get_groups()]
        devices = []  # list of lists (list of devices per group)
        endpoint_url = "{base_url}/{organization_id}/g/{group_id}/d"
        for gid in group_ids:
            path_vars["group_id"] = gid
            g_endpoint_url = endpoint_url.format(**path_vars)
            devices.append(self._get_data(g_endpoint_url))

        return [] if devices is None else devices

    def get_bandwidth_per_device(self, organization_id=None):
        """
        A function to get the bandwidth usage per device based on the organization ID.

        Args:
            organization_id: The ID of the organization. Defaults to None.

        Returns:
            A list of bandwidth usage per device or an empty list if no bandwidth usage is found.
        """
        if not organization_id:
            organization_id = self._org_id

        path_vars = {
            "base_url": _BASE_URL,
            "organization_id": organization_id
        }
        endpoint_url = "{base_url}/{organization_id}/bandwidth_per_device"
        res = self._get_data(endpoint_url.format(**path_vars))
        return [] if res is None else res
