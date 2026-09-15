"""Request signing for the QingCloud API.

Implements the query signature authentication described at
https://docsv4.qingcloud.com/user_guide/development_docs/api/rules/signature/

The string to sign is::

    HTTP_METHOD + "\\n" + URI_PATH + "\\n" + canonicalized_query

where canonicalized_query is built from all request parameters sorted by
parameter name, each name and value URL-encoded (RFC 3986, uppercase hex,
spaces as %20). The signature is the Base64 of the HMAC-SHA256 (or
HMAC-SHA1) digest of the string to sign, then URL-encoded.
"""

import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone


def _urlencode(value: str) -> str:
    """RFC 3986 percent-encoding (uppercase hex, spaces as %20)."""
    return urllib.parse.quote(str(value), safe="-_.~")


def _canonical_query(params: dict) -> str:
    """Build the canonicalized query string from sorted parameters."""
    pairs = []
    for key in sorted(params.keys()):
        pairs.append("%s=%s" % (_urlencode(key), _urlencode(params[key])))
    return "&".join(pairs)


def sign_request(
    params: dict,
    secret_access_key: str,
    method: str = "GET",
    path: str = "/iaas/",
    signature_method: str = "HmacSHA256",
) -> str:
    """Compute the request signature.

    Args:
        params: all request parameters (including common parameters).
        secret_access_key: the API secret access key.
        method: HTTP method, e.g. "GET" or "POST".
        path: the URI path, e.g. "/iaas/".
        signature_method: "HmacSHA256" or "HmacSHA1".

    Returns:
        The URL-encoded signature string.
    """
    string_to_sign = "%s\n%s\n%s" % (method, path, _canonical_query(params))
    digestmod = hashlib.sha256 if signature_method == "HmacSHA256" else hashlib.sha1
    h = hmac.new(secret_access_key.encode("utf-8"), digestmod=digestmod)
    h.update(string_to_sign.encode("utf-8"))
    signature = base64.b64encode(h.digest()).strip()
    return urllib.parse.quote_plus(signature)


def utc_timestamp() -> str:
    """Return the current UTC time in the format YYYY-MM-DDThh:mm:ssZ."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
