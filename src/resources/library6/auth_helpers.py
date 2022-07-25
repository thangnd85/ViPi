# Copyright (C) 2017 Google Inc.
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

import datetime
import threading

import google.auth.transport.requests

EXPIRY_DELTA = datetime.timedelta(seconds=1)


class CredentialsRefresher(object):
    """Helper class that periodically refreshes a set of credentials.

    Args:
        credentials(google.oauth2.credentials.Credentials): OAuth2 credentials.
        callback(callable): A function to return the refreshed credentials.
        expiry_delta(datetime.timedelta): A time delta relative to the expiry
            at which point the credentials should be refreshed (default: 1s).
    """

    def __init__(self, credentials, callback, expiry_delta=EXPIRY_DELTA):
        self._credentials = credentials
        self._callback = callback
        self._expiry_delta = expiry_delta
        self._timer = None
        # force initial credentials refresh
        http_request = google.auth.transport.requests.Request()
        self._credentials.refresh(http_request)
        self._callback(self._credentials)

    def start(self):
        self._handle_refresh_timer()

    def stop(self):
        self._timer.cancel()

    def _time_till_expiry(self):
        return self._credentials.expiry - datetime.datetime.utcnow()

    def _should_refresh_token(self):
        credentials_not_refreshed = not self._credentials.expiry
        if not self._credentials.valid or credentials_not_refreshed:
            return True
        is_expiring = self._time_till_expiry() <= self._expiry_delta
        return is_expiring

    def _handle_refresh_timer(self):
        if self._timer and not self._timer.is_alive():
            return

        if self._should_refresh_token():
            http_request = google.auth.transport.requests.Request()
            self._credentials.refresh(http_request)
        self._callback(self._credentials)
        refresh_timer_delay = (self._time_till_expiry().total_seconds()
                               - self._expiry_delta.seconds)
        self._timer = threading.Timer(refresh_timer_delay,
                                      self._handle_refresh_timer)
        self._timer.start()
