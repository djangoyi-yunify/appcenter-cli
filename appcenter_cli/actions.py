"""Definitions of the AppCenter API actions exposed by the CLI.

Each action describes its name, HTTP verb, URI path, and the request
parameters (name, type, required, description). Parameter types:

- str: single string value
- int: single integer value
- list: repeated parameter, serialized as ``name.1``, ``name.2``, ...
- list_dict: list of dicts, serialized as ``name.1.subkey``, ...
- json: a JSON-encoded string value

The action set is derived from the official API documentation:
https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/appcenter/cloud/
"""


class Param:
    def __init__(self, name, ptype="str", required=False, description=""):
        self.name = name
        self.ptype = ptype
        self.required = required
        self.description = description


class Action:
    def __init__(self, name, verb="GET", path="/iaas/", params=None, table_columns=None):
        self.name = name
        self.verb = verb
        self.path = path
        self.params = params or []
        self.table_columns = table_columns or []

    def param_names(self):
        return [p.name for p in self.params]

    def required_params(self):
        return [p.name for p in self.params if p.required]


# ---------------------------------------------------------------------------
# App / app version
# ---------------------------------------------------------------------------

DESCRIBE_APPS = Action(
    "DescribeApps",
    params=[
        Param("app", "str", False, "应用 ID"),
        Param("app_name", "str", False, "应用名称"),
        Param("category", "str", False, "类别，如 database、bigdata、container、shield"),
        Param("tags", "list", False, "标签数组"),
        Param("app_type", "str", False, "应用类型，如 web、image、cluster、license、sass"),
        Param("verbose", "int", False, "是否返回冗长的信息，1 为是"),
        Param("search_word", "str", False, "关键字（匹配应用名称，描述，摘要）"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
        Param("sort_key", "str", False, "结果排序的列"),
        Param("reverse", "int", False, "是否逆序，1 为逆序，0 为正序"),
    ],
    table_columns=["app_id", "app_name", "app_type", "status", "create_time"],
)

DESCRIBE_APP_VERSIONS = Action(
    "DescribeAppVersions",
    params=[
        Param("app_ids", "list", False, "应用 ID，可以是一个或多个"),
        Param("version_ids", "list", False, "应用版本 ID，可以是一个或多个"),
        Param("name", "str", False, "应用的名称"),
        Param("sort_key", "str", False, "结果排序的列"),
        Param("owner", "str", False, "按照用户账户过滤"),
        Param("verbose", "int", False, "是否返回冗长的信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认为 0"),
        Param("limit", "int", False, "返回数据长度，默认为 20，最大 100"),
    ],
    table_columns=["version_id", "name", "status", "create_time"],
)

DESCRIBE_APP_VERSION_ATTACHMENTS = Action(
    "DescribeAppVersionAttachments",
    params=[
        Param("content_keys", "list", False, "应用配置文件的名称，默认 config.json"),
        Param("attachment_ids", "list", True, "应用配置文件的 ID"),
        Param("version_id", "str", True, "应用版本的 ID"),
    ],
)

DEPLOY_APP_VERSION = Action(
    "DeployAppVersion",
    params=[
        Param("version_id", "str", True, "将要部署应用的版本 ID"),
        Param("conf", "json", True, "集群的配置信息（转义并去除空格的 JSON 格式）"),
        Param("debug", "int", False, "集群是否为开发测试集群"),
    ],
    table_columns=["cluster_id", "job_id", "app_id", "app_version"],
)

# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------

DESCRIBE_CLUSTERS = Action(
    "DescribeClusters",
    params=[
        Param("clusters", "list", False, "集群 ID，一个或多个"),
        Param("apps", "list", False, "集群所属的应用 ID，一个或多个"),
        Param("scope", "str", False, "集群的类型，可选 app、cfgmgmt，默认为 app"),
        Param("app_versions", "list", False, "集群所属的应用版本 ID，一个或多个"),
        Param("cluster_name", "str", False, "集群的名称"),
        Param("link", "str", False, "集群的外部依赖"),
        Param("external_cluster_id", "str", False, "集群依赖集群 ID"),
        Param("status", "list", False, "集群状态: active、suspended、deleted、ceased"),
        Param("vxnet", "str", False, "网络 ID"),
        Param("auto_scale_step", "str", False, "自动伸缩选项配置: volume_size、count"),
        Param("tags", "list", False, "按照标签 ID 过滤"),
        Param("owner", "str", False, "按照用户账户过滤"),
        Param("verbose", "int", False, "是否返回冗长的信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认为 0"),
        Param("limit", "int", False, "返回数据长度，默认为 20，最大 100"),
        Param("reverse", "int", False, "是否逆序，1 为逆序，0 为正序"),
    ],
    table_columns=["cluster_id", "name", "status", "app_id", "app_version", "node_count", "create_time"],
)

DESCRIBE_CLUSTER_NODES = Action(
    "DescribeClusterNodes",
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("cluster_nodes", "list", False, "集群节点 ID"),
        Param("role", "str", False, "集群节点角色"),
        Param("verbose", "int", False, "是否返回冗长的信息，目前只支持 0"),
        Param("offset", "int", False, "数据偏移量，默认为 0"),
        Param("limit", "int", False, "返回数据长度，默认为 20，最大 100"),
    ],
    table_columns=["node_id", "name", "role", "status", "private_ip", "create_time"],
)

DESCRIBE_CLUSTER_JOBS = Action(
    "DescribeClusterJobs",
    params=[
        Param("app", "str", True, "应用 ID"),
        Param("jobs", "list", False, "操作日志 ID"),
        Param("status", "list", False, "日志状态: pending、working、failed、successful"),
        Param("verbose", "int", False, "是否返回冗长的信息，目前只支持 0"),
        Param("offset", "int", False, "数据偏移量，默认为 0"),
        Param("limit", "int", False, "返回数据长度，默认为 20，最大 100"),
    ],
    table_columns=["job_id", "action", "status", "create_time", "resource_id"],
)

DESCRIBE_CLUSTER_ENV = Action(
    "DescribeClusterEnvironment",
    params=[
        Param("cluster_id", "str", True, "集群 ID"),
        Param("role", "str", False, "将要获取环境变量的角色，可留空"),
    ],
)

DESCRIBE_CLUSTER_DISPLAY_TABS = Action(
    "DescribeClusterDisplayTabs",
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("display_tabs", "str", True, "display tabs 的名称"),
    ],
)

START_CLUSTERS = Action(
    "StartClusters",
    params=[Param("clusters", "list", True, "将要启动的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

STOP_CLUSTERS = Action(
    "StopClusters",
    params=[Param("clusters", "list", True, "将要停止的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

RESTART_CLUSTER_SERVICE = Action(
    "RestartClusterService",
    params=[
        Param("cluster", "str", True, "将要重启服务的集群 ID"),
        Param("role", "str", False, "重启的集群角色"),
    ],
    table_columns=["job_id", "cluster_id"],
)

DELETE_CLUSTERS = Action(
    "DeleteClusters",
    params=[
        Param("clusters", "list", True, "一个或多个集群 ID"),
        Param("direct_cease", "int", False, "是否直接彻底销毁集群，1 为是，默认为 0"),
    ],
    table_columns=["job_id", "cluster_id"],
)

CEASE_CLUSTERS = Action(
    "CeaseClusters",
    params=[Param("clusters", "list", True, "将要销毁的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

RECOVER_CLUSTERS = Action(
    "RecoverClusters",
    params=[
        Param("clusters", "list", True, "待恢复的集群 ID"),
        Param("zone", "str", True, "区域 ID，注意需要小写"),
    ],
    table_columns=["job_id", "cluster_id"],
)

RESIZE_CLUSTER = Action(
    "ResizeCluster",
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("memory", "int", False, "节点将要增加或减小到的内存，单位 MB"),
        Param("cpu", "int", False, "节点将要增加或减小到的 cpu 数量"),
        Param("gpu", "int", False, "节点将要增加或减小到的 gpu 数量"),
        Param("storage", "int", False, "节点将要增加到的存储大小，单位 GB"),
        Param("node_role", "str", False, "节点的角色，如应用未配置节点角色，可留空"),
    ],
    table_columns=["job_id", "cluster_id"],
)

CHANGE_CLUSTER_VXNET = Action(
    "ChangeClusterVxnet",
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("vxnet", "str", True, "集群即将加入的网络的 ID"),
        Param("roles", "list", False, "集群的角色"),
        Param("private_ips", "list_dict", False, "节点对应的私有 IP，格式 [{node_id, private_ip}]"),
    ],
    table_columns=["job_id", "cluster_id"],
)

UPDATE_CLUSTER_ENV = Action(
    "UpdateClusterEnvironment",
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("role", "str", False, "将要修改的角色，如集群未配置角色，可留空"),
        Param("env", "json", True, "JSON 格式的环境变量，例如 {\"key\": \"value\"}"),
    ],
    table_columns=["job_id", "cluster_id"],
)

# ---------------------------------------------------------------------------
# Cluster nodes
# ---------------------------------------------------------------------------

ADD_CLUSTER_NODES = Action(
    "AddClusterNodes",
    params=[
        Param("cluster", "str", True, "增加节点的集群 ID"),
        Param("node_count", "int", True, "增加的节点数量"),
        Param("node_role", "str", False, "增加的节点的角色，如无角色，可不传递此项"),
        Param("resource_conf", "json", False, "JSON 格式的节点配置，保持默认配置，此项留空即可"),
        Param("private_ips", "json", False, "JSON 格式的节点私有 ip 地址"),
        Param("node_name", "str", False, "节点的名称"),
    ],
    table_columns=["job_id", "cluster_id"],
)

DELETE_CLUSTER_NODES = Action(
    "DeleteClusterNodes",
    params=[
        Param("cluster", "str", True, "集群的 ID"),
        Param("nodes", "list", True, "将要删除的集群节点的 ID"),
        Param("force", "int", False, "是否强制删除，1 表示强制删除，0 表示否，默认为 0"),
    ],
    table_columns=["job_id", "cluster_id"],
)

ASSOCIATE_EIP_TO_CLUSTER_NODE = Action(
    "AssociateEipToClusterNode",
    params=[
        Param("eip", "str", True, "公网 IP 的 ID"),
        Param("cluster_node", "str", True, "集群节点 ID"),
    ],
    table_columns=["job_id", "cluster_id"],
)

DISSOCIATE_EIP_FROM_CLUSTER_NODE = Action(
    "DissociateEipFromClusterNode",
    params=[Param("eips", "list", True, "将要解绑的公网 IP 的 ID")],
    table_columns=["job_id", "cluster_id"],
)

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

GET_CLUSTER_MONITOR = Action(
    "GetClusterMonitor",
    params=[
        Param("version_id", "str", False, "集群应用版本 ID"),
        Param("app_id", "str", False, "集群应用 ID"),
        Param("resource", "str", True, "集群节点 ID"),
        Param("role", "str", False, "节点角色"),
        Param("step", "str", True, "监控数据时间间隔，例如 1m、5m、15m、30m、1h、2h、1d"),
        Param("start_time", "str", True, "监控数据的开始 UTC 时间，格式 2011-07-11T11:07:00Z"),
        Param("end_time", "str", True, "监控数据的结束 UTC 时间，格式 2011-07-11T11:07:00Z"),
        Param("meters", "list", True, "监控指标，例如 cpu、memory、disk 等"),
    ],
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ACTIONS = {
    "describe-apps": DESCRIBE_APPS,
    "describe-app-versions": DESCRIBE_APP_VERSIONS,
    "describe-app-version-attachments": DESCRIBE_APP_VERSION_ATTACHMENTS,
    "deploy-app-version": DEPLOY_APP_VERSION,
    "describe-clusters": DESCRIBE_CLUSTERS,
    "describe-cluster-nodes": DESCRIBE_CLUSTER_NODES,
    "describe-cluster-jobs": DESCRIBE_CLUSTER_JOBS,
    "describe-cluster-env": DESCRIBE_CLUSTER_ENV,
    "describe-cluster-display-tabs": DESCRIBE_CLUSTER_DISPLAY_TABS,
    "start-clusters": START_CLUSTERS,
    "stop-clusters": STOP_CLUSTERS,
    "restart-cluster-service": RESTART_CLUSTER_SERVICE,
    "delete-clusters": DELETE_CLUSTERS,
    "cease-clusters": CEASE_CLUSTERS,
    "recover-clusters": RECOVER_CLUSTERS,
    "resize-cluster": RESIZE_CLUSTER,
    "change-cluster-vxnet": CHANGE_CLUSTER_VXNET,
    "update-cluster-env": UPDATE_CLUSTER_ENV,
    "add-cluster-nodes": ADD_CLUSTER_NODES,
    "delete-cluster-nodes": DELETE_CLUSTER_NODES,
    "associate-eip-to-cluster-node": ASSOCIATE_EIP_TO_CLUSTER_NODE,
    "dissociate-eip-from-cluster-node": DISSOCIATE_EIP_FROM_CLUSTER_NODE,
    "get-cluster-monitor": GET_CLUSTER_MONITOR,
}
