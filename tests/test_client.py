import json

from appcenter_cli.client import Client
from appcenter_cli.config import Config


def test_expand_params_lists():
    client = Client(Config(access_key_id="a", secret_access_key="s", zone="pek3a"))
    expanded = client._expand_params(
        {
            "clusters": ["cl-1", "cl-2"],
            "status": ["active", "suspended"],
            "tags": ["tag-1"],
        }
    )
    assert expanded == {
        "clusters.1": "cl-1",
        "clusters.2": "cl-2",
        "status.1": "active",
        "status.2": "suspended",
        "tags.1": "tag-1",
    }


def test_expand_params_multi_deploy_zones():
    client = Client(Config(access_key_id="a", secret_access_key="s", zone="pek3"))
    expanded = client._expand_params({"multi_deploy_zones": ["pek3b", "pek3d"]})
    assert expanded == {
        "multi_deploy_zones.1": "pek3b",
        "multi_deploy_zones.2": "pek3d",
    }


def test_expand_params_status_filter():
    client = Client(Config(access_key_id="a", secret_access_key="s", zone="pek3"))
    expanded = client._expand_params({"status": ["active", "suspended"]})
    assert expanded == {
        "status.1": "active",
        "status.2": "suspended",
    }


def test_expand_params_list_of_dicts():
    client = Client(Config(access_key_id="a", secret_access_key="s", zone="pek3a"))
    expanded = client._expand_params(
        {"private_ips": [{"node_id": "cln-1", "private_ip": "10.0.0.1"}]}
    )
    assert expanded == {
        "private_ips.1.node_id": "cln-1",
        "private_ips.1.private_ip": "10.0.0.1",
    }


def test_expand_params_dict_json():
    client = Client(Config(access_key_id="a", secret_access_key="s", zone="pek3a"))
    expanded = client._expand_params({"link": {"limits": {"app-1": ["v1"]}}})
    assert json.loads(expanded["link"]) == {"limits": {"app-1": ["v1"]}}


def test_build_url_contains_common_params():
    client = Client(Config(access_key_id="AK", secret_access_key="SK", zone="pek3a"))
    url = client._build_url("DescribeClusters", {"clusters.1": "cl-1"}, "GET", "/iaas/")
    assert "action=DescribeClusters" in url
    assert "access_key_id=AK" in url
    assert "zone=pek3a" in url
    assert "signature_method=HmacSHA256" in url
    assert "signature_version=1" in url
    assert "version=1" in url
    assert "time_stamp=" in url
    assert "signature=" in url
    assert "clusters.1=cl-1" in url
