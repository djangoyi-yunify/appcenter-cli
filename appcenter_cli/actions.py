"""Definitions of the AppCenter API actions exposed by the CLI.

Each action describes its name, HTTP verb, URI path, the request
parameters (name, type, required, description), plus AI-agent friendly
metadata: a human-readable description, usage examples, and notes.

The action set is derived from the official API documentation:
https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/appcenter/cloud/
"""

from qc_cli.actions import Action, Param


# ---------------------------------------------------------------------------
# App / app version
# ---------------------------------------------------------------------------

DESCRIBE_APPS = Action(
    "DescribeApps",
    description="列出应用",
    examples=[
        "appcenter describe-apps",
        "appcenter describe-apps --app app-zydumbxo",
        "appcenter describe-apps --category database --output table",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "默认返回 20 条，可用 --limit 调整（最大 100）。",
    ],
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
    description="列出应用版本",
    examples=[
        "appcenter describe-app-versions --app-ids app-zydumbxo",
        "appcenter describe-app-versions --version-ids appv-tvzeju2i",
        "appcenter describe-app-versions --app-ids app-zydumbxo --status active",
    ],
    notes=[
        "--app-ids 与 --version-ids 至少提供一个。",
        "只读命令，不会修改任何资源。",
    ],
    params=[
        Param("app_ids", "list", False, "应用 ID，可以是一个或多个"),
        Param("version_ids", "list", False, "应用版本 ID，可以是一个或多个"),
        Param("name", "str", False, "应用的名称"),
        Param("sort_key", "str", False, "结果排序的列"),
        Param("owner", "str", False, "按照用户账户过滤"),
        Param("status", "list", False, "版本状态过滤，可重复传，如 active、suspended"),
        Param("verbose", "int", False, "是否返回冗长的信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认为 0"),
        Param("limit", "int", False, "返回数据长度，默认为 20，最大 100"),
    ],
    table_columns=["version_id", "name", "status", "create_time"],
    required_any=[["app_ids", "version_ids"]],
)

DESCRIBE_APP_VERSION_ATTACHMENTS = Action(
    "DescribeAppVersionAttachments",
    description="获取应用版本配置文件",
    examples=[
        "appcenter describe-app-version-attachments --version-id appv-tvzeju2i --attachment-ids att-xxxx",
    ],
    notes=[
        "需要先通过其他途径获取 attachment ID。",
        "只读命令，不会修改任何资源。",
    ],
    params=[
        Param("content_keys", "list", False, "应用配置文件的名称，默认 config.json"),
        Param("attachment_ids", "list", True, "应用配置文件的 ID"),
        Param("version_id", "str", True, "应用版本的 ID"),
    ],
)

DEPLOY_APP_VERSION = Action(
    "DeployAppVersion",
    description="部署应用版本（创建集群）",
    examples=[
        "appcenter deploy-app-version --version-id appv-tvzeju2i --conf '{\"name\":\"demo\",\"vxnet\":\"vxnet-0\"}'",
        "appcenter deploy-app-version --version-id appv-tvzeju2i --conf '{\"name\":\"demo\",\"vxnet\":\"vxnet-0\"}' --debug 1",
        "appcenter deploy-app-version --version-id appv-tvzeju2i --conf '{\"name\":\"demo\",\"vxnet\":\"vxnet-0\"}' --multi-deploy-zones pek3b --multi-deploy-zones pek3d",
    ],
    notes=[
        "--conf 必须为 JSON 对象（不能是数组或标量）。",
        "--debug 1 创建开发测试集群，可用于测试未上架/开发中的版本。",
        "多可用区部署时，--zone 传区域（如 pek3），并用 --multi-deploy-zones 指定可用区（如 pek3b、pek3d）。",
        "创建集群是异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
    ],
    params=[
        Param("version_id", "str", True, "将要部署应用的版本 ID"),
        Param("conf", "json", True, "JSON 对象格式的集群配置，如 {\"name\":\"demo\",\"vxnet\":\"vxnet-0\"}", json_object=True),
        Param("debug", "int", False, "集群是否为开发测试集群"),
        Param("multi_deploy_zones", "list", False, "多可用区部署的可用区列表，如 pek3b、pek3d"),
    ],
    table_columns=["cluster_id", "job_id", "app_id", "app_version"],
)

# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------

DESCRIBE_CLUSTERS = Action(
    "DescribeClusters",
    description="获取集群信息",
    examples=[
        "appcenter describe-clusters",
        "appcenter describe-clusters --clusters cl-xxxx",
        "appcenter describe-clusters --status active --output table",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "默认返回 20 条，可用 --limit 调整（最大 100）。",
        "加 --verbose 1 可查看集群的 app_version_info（含可升级版本 upgrade_policy）。",
    ],
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
    description="获取集群节点信息",
    examples=[
        "appcenter describe-cluster-nodes --cluster cl-xxxx",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
    ],
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
    description="获取集群操作日志",
    examples=[
        "appcenter describe-cluster-jobs --app app-zydumbxo",
        "appcenter describe-cluster-jobs --app app-zydumbxo --jobs j-xxxx",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "用于查询 deploy/start/stop 等异步操作的进度。",
    ],
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
    description="获取集群环境变量",
    examples=[
        "appcenter describe-cluster-env --cluster-id cl-xxxx",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
    ],
    params=[
        Param("cluster_id", "str", True, "集群 ID"),
        Param("role", "str", False, "将要获取环境变量的角色，可留空"),
    ],
)

DESCRIBE_CLUSTER_DISPLAY_TABS = Action(
    "DescribeClusterDisplayTabs",
    description="获取集群 display tabs",
    examples=[
        "appcenter describe-cluster-display-tabs --cluster cl-xxxx --display-tabs tab-xxxx",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
    ],
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("display_tabs", "str", True, "display tabs 的名称"),
    ],
)

START_CLUSTERS = Action(
    "StartClusters",
    description="启动集群",
    examples=[
        "appcenter start-clusters --clusters cl-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "仅对已停止的集群有效。",
    ],
    params=[Param("clusters", "list", True, "将要启动的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

STOP_CLUSTERS = Action(
    "StopClusters",
    description="停止集群",
    examples=[
        "appcenter stop-clusters --clusters cl-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "停止后集群不再产生计算费用（存储仍计费）。",
    ],
    params=[Param("clusters", "list", True, "将要停止的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

RESTART_CLUSTER_SERVICE = Action(
    "RestartClusterService",
    description="重启集群服务",
    examples=[
        "appcenter restart-cluster-service --cluster cl-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
    ],
    params=[
        Param("cluster", "str", True, "将要重启服务的集群 ID"),
        Param("role", "str", False, "重启的集群角色"),
    ],
    table_columns=["job_id", "cluster_id"],
)

DELETE_CLUSTERS = Action(
    "DeleteClusters",
    description="删除集群",
    examples=[
        "appcenter delete-clusters --clusters cl-xxxx",
        "appcenter delete-clusters --clusters cl-xxxx --direct-cease 1",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "默认删除后进入回收站，可用 --direct-cease 1 直接彻底销毁。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[
        Param("clusters", "list", True, "一个或多个集群 ID"),
        Param("direct_cease", "int", False, "是否直接彻底销毁集群，1 为是，默认为 0"),
    ],
    table_columns=["job_id", "cluster_id"],
)

CEASE_CLUSTERS = Action(
    "CeaseClusters",
    description="销毁集群",
    examples=[
        "appcenter cease-clusters --clusters cl-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "彻底销毁，不可恢复。破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[Param("clusters", "list", True, "将要销毁的集群 ID")],
    table_columns=["job_id", "cluster_id"],
)

RECOVER_CLUSTERS = Action(
    "RecoverClusters",
    description="恢复集群",
    examples=[
        "appcenter recover-clusters --clusters cl-xxxx --zone pek3",
    ],
    notes=[
        "从回收站恢复已删除的集群。",
        "--zone 为必填参数（区域 ID，注意需要小写）。",
    ],
    params=[
        Param("clusters", "list", True, "待恢复的集群 ID"),
        Param("zone", "str", True, "区域 ID，注意需要小写"),
    ],
    table_columns=["job_id", "cluster_id"],
)

RESIZE_CLUSTER = Action(
    "ResizeCluster",
    description="调整集群节点规格",
    examples=[
        "appcenter resize-cluster --cluster cl-xxxx --cpu 2 --memory 2048",
        "appcenter resize-cluster --cluster cl-xxxx --storage-size 20",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "--memory 单位 MB，--storage-size 单位 GB。",
    ],
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("memory", "int", False, "节点将要增加或减小到的内存，单位 MB"),
        Param("cpu", "int", False, "节点将要增加或减小到的 cpu 数量"),
        Param("gpu", "int", False, "节点将要增加或减小到的 gpu 数量"),
        Param("storage_size", "int", False, "节点将要增加到的存储大小，单位 GB"),
        Param("instance_class", "int", False, "节点将要调整到的实例类型"),
        Param("node_role", "str", False, "节点的角色，如应用未配置节点角色，可留空"),
    ],
    table_columns=["job_id", "cluster_id"],
)

CHANGE_CLUSTER_VXNET = Action(
    "ChangeClusterVxnet",
    description="切换集群私网",
    examples=[
        "appcenter change-cluster-vxnet --cluster cl-xxxx --vxnet vxnet-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "--private-ips 为 JSON 数组，如 '[{\"node_id\":\"cln-1\",\"private_ip\":\"10.0.0.1\"}]'。",
    ],
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
    description="更新集群环境变量",
    examples=[
        "appcenter update-cluster-env --cluster cl-xxxx --env '{\"key\":\"value\"}'",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "--env 必须为 JSON 对象。",
    ],
    params=[
        Param("cluster", "str", True, "集群 ID"),
        Param("role", "str", False, "将要修改的角色，如集群未配置角色，可留空"),
        Param("env", "json", True, "JSON 对象格式的环境变量，例如 {\"key\": \"value\"}", json_object=True),
    ],
    table_columns=["job_id", "cluster_id"],
)

UPGRADE_CLUSTERS = Action(
    "UpgradeClusters",
    description="升级集群版本",
    examples=[
        "appcenter upgrade-clusters --app-version appv-tvzeju2i --clusters cl-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "目标版本必须出现在集群的 upgrade_policy 中（可用 describe-clusters --verbose 1 查看）。",
        "升级到已上架版本要求集群健康（healthy）；升级到开发版本要求集群先停止。",
    ],
    params=[
        Param("app_version", "str", True, "将要升级到的应用版本 ID"),
        Param("clusters", "list", True, "将要升级的集群 ID，一个或多个"),
    ],
    table_columns=["job_id", "cluster_ids"],
)

# ---------------------------------------------------------------------------
# Cluster nodes
# ---------------------------------------------------------------------------

ADD_CLUSTER_NODES = Action(
    "AddClusterNodes",
    description="增加集群节点",
    examples=[
        "appcenter add-cluster-nodes --cluster cl-xxxx --node-count 2",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
    ],
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
    description="删除集群节点",
    examples=[
        "appcenter delete-cluster-nodes --cluster cl-xxxx --nodes cln-1 --nodes cln-2",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[
        Param("cluster", "str", True, "集群的 ID"),
        Param("nodes", "list", True, "将要删除的集群节点的 ID"),
        Param("force", "int", False, "是否强制删除，1 表示强制删除，0 表示否，默认为 0"),
    ],
    table_columns=["job_id", "cluster_id"],
)

ASSOCIATE_EIP_TO_CLUSTER_NODE = Action(
    "AssociateEipToClusterNode",
    description="绑定公网 IP 到节点",
    examples=[
        "appcenter associate-eip-to-cluster-node --eip eip-xxxx --cluster-node cln-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
    ],
    params=[
        Param("eip", "str", True, "公网 IP 的 ID"),
        Param("cluster_node", "str", True, "集群节点 ID"),
    ],
    table_columns=["job_id", "cluster_id"],
)

DISSOCIATE_EIP_FROM_CLUSTER_NODE = Action(
    "DissociateEipFromClusterNode",
    description="解绑节点公网 IP",
    examples=[
        "appcenter dissociate-eip-from-cluster-node --eips eip-xxxx",
    ],
    notes=[
        "异步操作，返回 job_id，可用 describe-cluster-jobs 查询进度。",
    ],
    params=[Param("eips", "list", True, "将要解绑的公网 IP 的 ID")],
    table_columns=["job_id", "cluster_id"],
)

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

GET_CLUSTER_MONITOR = Action(
    "GetClusterMonitor",
    description="获取集群监控数据",
    examples=[
        "appcenter get-cluster-monitor --resource cln-xxxx --step 5m --start-time 2026-09-10T00:00:00Z --end-time 2026-09-10T01:00:00Z --meters cpu --meters memory",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "--step 可选 1m、5m、15m、30m、1h、2h、1d。",
        "时间为 UTC，格式 YYYY-MM-DDTHH:MM:SSZ。",
    ],
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
    "upgrade-clusters": UPGRADE_CLUSTERS,
    "add-cluster-nodes": ADD_CLUSTER_NODES,
    "delete-cluster-nodes": DELETE_CLUSTER_NODES,
    "associate-eip-to-cluster-node": ASSOCIATE_EIP_TO_CLUSTER_NODE,
    "dissociate-eip-from-cluster-node": DISSOCIATE_EIP_FROM_CLUSTER_NODE,
    "get-cluster-monitor": GET_CLUSTER_MONITOR,
}
