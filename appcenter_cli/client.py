"""Low-level HTTP client for the QingCloud API.

Handles parameter serialization (list/dict expansion into dotted keys),
request signing, and response parsing. The AppCenter actions are served
from the same /iaas/ endpoint as the rest of the QingCloud API.
"""

import json
import random
import time
import urllib.parse
import urllib.request
import uuid

from .auth import sign_request, utc_timestamp
from .config import Config


class APIError(Exception):
    """Raised when the API returns a non-zero ret_code."""

    def __init__(self, ret_code, message, action=None):
        self.ret_code = ret_code
        self.message = message
        self.action = action
        super().__init__("ret_code=%s message=%s" % (ret_code, message))


class Client:
    """A thin client for the QingCloud AppCenter API."""

    def __init__(self, config: Config):
        self.config = config

    def _expand_params(self, params: dict) -> dict:
        """Expand lists and dicts into dotted query parameters.

        A list value becomes ``key.1``, ``key.2``, ... A list of dicts
        becomes ``key.1.subkey``, ``key.2.subkey``, ... A dict value is
        JSON-encoded.
        """
        expanded: dict = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, list):
                for i, item in enumerate(value, start=1):
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            if isinstance(sub_value, (dict, list)):
                                sub_value = json.dumps(sub_value, separators=(",", ":"))
                            expanded["%s.%d.%s" % (key, i, sub_key)] = sub_value
                    else:
                        expanded["%s.%d" % (key, i)] = item
            elif isinstance(value, dict):
                expanded[key] = json.dumps(value, separators=(",", ":"))
            else:
                expanded[key] = value
        return expanded

    def _build_url(self, action: str, params: dict, verb: str, path: str) -> str:
        cfg = self.config
        request_params = dict(params)
        request_params["action"] = action
        request_params.setdefault("zone", cfg.zone)
        request_params.setdefault("req_id", uuid.uuid4().hex)
        request_params["access_key_id"] = cfg.access_key_id
        request_params["signature_method"] = "HmacSHA256"
        request_params["signature_version"] = 1
        request_params["version"] = 1
        request_params["time_stamp"] = utc_timestamp()

        signature = sign_request(
            request_params,
            cfg.secret_access_key,
            method=verb,
            path=path,
            signature_method="HmacSHA256",
        )

        # sign_request already returns a URL-encoded signature; append it
        # as-is to avoid double-encoding (which breaks API signature check).
        query = urllib.parse.urlencode(request_params)
        query += "&signature=" + signature
        return "%s://%s:%d%s?%s" % (cfg.protocol, cfg.host, cfg.port, path, query)

    def send_request(
        self,
        action: str,
        params: dict = None,
        verb: str = "GET",
        path: str = "/iaas/",
    ) -> dict:
        """Send a request to the API and return the parsed JSON response.

        Args:
            action: the API action name, e.g. "DescribeClusters".
            params: action-specific request parameters.
            verb: HTTP method, "GET" or "POST".
            path: the URI path, defaults to "/iaas/".

        Returns:
            The parsed JSON response dict.

        Raises:
            APIError: if the API returns a non-zero ret_code.
        """
        params = params or {}
        expanded = self._expand_params(params)
        url = self._build_url(action, expanded, verb, path)

        retry_time = 0
        while True:
            try:
                req = urllib.request.Request(url, method=verb)
                with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                    body = resp.read().decode("utf-8")
                data = json.loads(body) if body else {}
                ret_code = data.get("ret_code", 0)
                if ret_code in (5000, 5100) and retry_time < self.config.retry_time - 1:
                    # 5000: INTERNAL ERROR, 5100: SERVER BUSY
                    time.sleep(random.random() * (2 ** retry_time))
                    retry_time += 1
                    continue
                if ret_code != 0:
                    raise APIError(ret_code, data.get("message", ""), action)
                return data
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "ignore")
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    raise APIError(e.code, body, action)
                raise APIError(data.get("ret_code", e.code), data.get("message", body), action)
