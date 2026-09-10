import base64
import hashlib
import hmac
import urllib.parse

from appcenter_cli.auth import sign_request, utc_timestamp


def test_signature_matches_doc_example():
    """Verify against the official doc example (RunInstances)."""
    secret = "SECRETACCESSKEY"
    params = {
        "access_key_id": "QYACCESSKEYIDEXAMPLE",
        "action": "RunInstances",
        "count": 1,
        "image_id": "centos64x86a",
        "instance_name": "demo",
        "instance_type": "small_b",
        "login_mode": "passwd",
        "login_passwd": "QingCloud20130712",
        "signature_method": "HmacSHA256",
        "signature_version": 1,
        "time_stamp": "2013-08-27T14:30:10Z",
        "version": 1,
        "vxnets.1": "vxnet-0",
        "zone": "pek3a",
    }
    sig = sign_request(params, secret, method="GET", path="/iaas/")
    assert sig == "byjccvWIvAftaq%2BoublemagH3bYAlDWxxLFAzAsyslw%3D"


def test_signature_hmac_sha1():
    secret = "secret"
    params = {"action": "DescribeClusters", "zone": "pek3a"}
    sig = sign_request(params, secret, signature_method="HmacSHA1")
    string_to_sign = "GET\n/iaas/\naction=DescribeClusters&zone=pek3a"
    h = hmac.new(secret.encode(), digestmod=hashlib.sha1)
    h.update(string_to_sign.encode())
    expected = urllib.parse.quote_plus(base64.b64encode(h.digest()).strip())
    assert sig == expected


def test_utc_timestamp_format():
    ts = utc_timestamp()
    assert ts.endswith("Z")
    assert "T" in ts
