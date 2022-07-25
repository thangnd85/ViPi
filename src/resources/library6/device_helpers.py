# Copyright (C) 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import json

import google.auth.transport.requests


DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'

ERROR_MESSAGE_TEMPLATE = "Failed to register device {status}" \
                         " ({status_code}): {error_text}"""


class RegistrationError(Exception):
    def __init__(self, response, device_model_id):
        super(RegistrationError, self).__init__(
            self._format_error(response, device_model_id))

    def _format_error(self, response, device_model_id):
        """Prints a pretty error message for registration failures."""
        status_code = response.status_code
        error_text = response.text
        status = "ERROR"

        try:
            error_text = response.json()['error']['message']
            status = response.json()['error']['status']
        except ValueError:
            pass

        return ERROR_MESSAGE_TEMPLATE.format(
            status=status,
            status_code=status_code,
            error_text=error_text,
            device_model_id=device_model_id)


def register_device(
        project_id,
        credentials,
        device_model_id,
        device_id,
        nickname=None):
    """Register a new assistant device instance.

    Args:
       project_id(str): The project ID used to register device instance.
       credentials(google.oauth2.credentials.Credentials): The Google
                OAuth2 credentials of the user to associate the device
                instance with.
       device_model_id(str): The registered device model ID.
       device_id(str): The device ID of the new instance.
    """
    base_url = '/'.join([DEVICE_API_URL, 'projects', project_id, 'devices'])
    device_url = '/'.join([base_url, device_id])
    session = google.auth.transport.requests.AuthorizedSession(credentials)
    r = session.get(device_url)
    # Check if the device already is registered and if not then we try to
    # register. If any HTTP connection fails raise a RegistrationError.
    if r.status_code == 404:
        print('Registering...', end='')
        payload = {
            'id': device_id,
            'model_id': device_model_id,
            'client_type': 'SDK_LIBRARY'
        }
        if nickname:
            payload['nickname'] = nickname
        r = session.post(base_url, data=json.dumps(payload))
        if r.status_code != 200:
            raise RegistrationError(r, device_model_id)
        print('Done.\n')
    elif r.status_code != 200:
        raise RegistrationError(r, device_model_id)
