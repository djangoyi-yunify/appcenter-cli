"""Definitions of the IaaS API actions exposed by the CLI.

Covers cloud servers (instances), instance groups (placement groups) and
virtual machine images. The action set is derived from the official API
documentation:

- https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/compute/instance/
- https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/compute/image/
"""

from qc_cli.actions import Action, Param

# ---------------------------------------------------------------------------
# Cloud servers (instances)
# ---------------------------------------------------------------------------

DESCRIBE_INSTANCES = Action(
    "DescribeInstances",
    description="获取云服务器列表",
    examples=[
        "iaas describe-instances",
        "iaas describe-instances --instances i-xxxx --output table",
        "iaas describe-instances --status running --status stopped",
        "iaas describe-instances --search-word demo --limit 50",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "默认返回 20 条，可用 --limit 调整（最大 100）。",
        "--status 可重复传入，如 running、stopped、pending、terminated。",
    ],
    params=[
        Param("instances", "list", False, "云服务器 ID 数组"),
        Param("image_id", "str", False, "镜像 ID"),
        Param("instance_type", "str", False, "云服务器类型"),
        Param("status", "list", False, "状态数组，如 pending、running、stopped、terminated"),
        Param("owner", "str", False, "资源所有者 ID"),
        Param("search_word", "str", False, "搜索关键字（匹配名称、描述等）"),
        Param("verbose", "int", False, "是否返回冗长信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
        Param("tags", "list", False, "标签 ID 数组"),
    ],
    table_columns=["instance_id", "instance_name", "status", "vcpus_current", "memory_current", "create_time"],
)

RUN_INSTANCES = Action(
    "RunInstances",
    description="创建云服务器",
    examples=[
        "iaas run-instances --image-id img-xxxx --instance-type small_b --count 1",
        "iaas run-instances --image-id img-xxxx --cpu 2 --memory 2048 --instance-name demo",
        "iaas run-instances --image-id img-xxxx --login-mode passwd --login-passwd 'P@ssw0rd'",
        "iaas run-instances --image-id img-xxxx --vxnets vxnet-0 --security-group sg-xxxx --dry-run",
    ],
    notes=[
        "创建云服务器，返回 job_id 与云服务器 ID 列表。",
        "可通过 --instance-type 指定类型，或通过 --cpu/--memory 指定规格。",
        "登录方式：--login-mode passwd（密码）或 keypair（密钥），需配合对应参数。",
        "破坏性/计费操作，建议先用 --dry-run 预览请求。",
    ],
    params=[
        Param("image_id", "str", True, "镜像 ID"),
        Param("instance_type", "str", False, "云服务器类型，如 small_b"),
        Param("cpu", "int", False, "CPU 核数"),
        Param("memory", "int", False, "内存大小（MB）"),
        Param("count", "int", False, "创建数量，默认 1"),
        Param("instance_name", "str", False, "云服务器名称"),
        Param("vxnets", "list", False, "私有网络 ID 数组"),
        Param("security_group", "str", False, "安全组 ID"),
        Param("login_mode", "str", False, "登录方式，passwd 或 keypair"),
        Param("login_keypair", "str", False, "登录密钥 ID（login_mode=keypair 时）"),
        Param("login_passwd", "str", False, "登录密码（login_mode=passwd 时）"),
        Param("need_newsid", "int", False, "是否重新生成 SID，1 为是"),
        Param("volumes", "list", False, "数据盘 ID 数组"),
        Param("cpu_model", "str", False, "CPU 型号"),
        Param("need_userdata", "int", False, "是否使用自定义数据，1 为是"),
        Param("userdata_type", "str", False, "自定义数据类型，plain 或 tar"),
        Param("userdata_value", "str", False, "自定义数据内容"),
        Param("userdata_path", "str", False, "自定义数据文件路径"),
        Param("instance_class", "int", False, "云服务器类型类别"),
        Param("hostname", "str", False, "主机名"),
        Param("target_user", "str", False, "目标用户 ID"),
        Param("nic_mqueue", "int", False, "网卡多队列数"),
        Param("cpu_max", "int", False, "CPU 上限"),
        Param("mem_max", "int", False, "内存上限（MB）"),
        Param("os_disk_size", "int", False, "系统盘大小（GB）"),
    ],
)

TERMINATE_INSTANCES = Action(
    "TerminateInstances",
    description="销毁云服务器（进入回收站）",
    examples=[
        "iaas terminate-instances --instances i-xxxx",
        "iaas terminate-instances --instances i-xxxx --direct-cease 1 --dry-run",
    ],
    notes=[
        "销毁后云服务器进入回收站，可恢复；如需彻底销毁请用 cease-instances。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("direct_cease", "int", False, "是否直接彻底销毁，1 为是"),
    ],
)

START_INSTANCES = Action(
    "StartInstances",
    description="启动云服务器",
    examples=["iaas start-instances --instances i-xxxx"],
    notes=["启动已停止的云服务器。"],
    params=[Param("instances", "list", True, "云服务器 ID 数组")],
)

STOP_INSTANCES = Action(
    "StopInstances",
    description="停止云服务器",
    examples=[
        "iaas stop-instances --instances i-xxxx",
        "iaas stop-instances --instances i-xxxx --force 1",
    ],
    notes=["停止云服务器；--force 1 表示强制停止。"],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("force", "int", False, "是否强制停止，1 为是"),
    ],
)

RESTART_INSTANCES = Action(
    "RestartInstances",
    description="重启云服务器",
    examples=["iaas restart-instances --instances i-xxxx"],
    notes=["重启云服务器。"],
    params=[Param("instances", "list", True, "云服务器 ID 数组")],
)

RESET_INSTANCES = Action(
    "ResetInstances",
    description="重置云服务器系统盘",
    examples=[
        "iaas reset-instances --instances i-xxxx --login-mode passwd --login-passwd 'P@ssw0rd'",
        "iaas reset-instances --instances i-xxxx --login-mode keypair --login-keypair kp-xxxx",
    ],
    notes=[
        "重置系统盘会清空系统盘数据，请谨慎操作。",
        "登录方式：--login-mode passwd（密码）或 keypair（密钥）。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("login_mode", "str", False, "登录方式，passwd 或 keypair"),
        Param("login_passwd", "str", False, "登录密码（login_mode=passwd 时）"),
        Param("login_keypair", "str", False, "登录密钥 ID（login_mode=keypair 时）"),
        Param("need_newsid", "int", False, "是否重新生成 SID，1 为是"),
    ],
)

RESIZE_INSTANCES = Action(
    "ResizeInstances",
    description="调整云服务器配置",
    examples=[
        "iaas resize-instances --instances i-xxxx --cpu 4 --memory 8192",
        "iaas resize-instances --instances i-xxxx --instance-type large_c",
    ],
    notes=[
        "调整 CPU/内存或实例类型，需云服务器处于 stopped 状态。",
        "可通过 --instance-type 指定类型，或通过 --cpu/--memory 指定规格。",
    ],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("instance_type", "str", False, "云服务器类型，如 large_c"),
        Param("cpu", "int", False, "CPU 核数"),
        Param("memory", "int", False, "内存大小（MB）"),
        Param("os_disk_size", "int", False, "系统盘大小（GB）"),
    ],
)

MODIFY_INSTANCE_ATTRIBUTES = Action(
    "ModifyInstanceAttributes",
    description="修改云服务器名称和描述",
    examples=[
        "iaas modify-instance-attributes --instance i-xxxx --instance-name new-name",
        "iaas modify-instance-attributes --instance i-xxxx --description 'web server'",
    ],
    notes=["修改云服务器的名称、描述等属性。"],
    params=[
        Param("instance", "str", True, "云服务器 ID"),
        Param("instance_name", "str", False, "云服务器名称"),
        Param("description", "str", False, "云服务器描述"),
        Param("nic_mqueue", "int", False, "网卡多队列数"),
    ],
)

DESCRIBE_INSTANCE_TYPES = Action(
    "DescribeInstanceTypes",
    description="获取支持的云服务器类型",
    examples=[
        "iaas describe-instance-types",
        "iaas describe-instance-types --instance-type small_b --output table",
    ],
    notes=["只读命令，返回可用的云服务器类型及规格。"],
    params=[
        Param("instance_type", "list", False, "云服务器类型数组"),
        Param("verbose", "int", False, "是否返回冗长信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
    ],
    table_columns=["instance_type_id", "instance_type_name", "vcpus", "memory_size", "instance_type_category"],
)

CLONE_INSTANCES = Action(
    "CloneInstances",
    description="克隆云服务器",
    examples=[
        "iaas clone-instances --instances i-xxxx",
        "iaas clone-instances --instances i-xxxx --vxnets 'i-xxxx|vxnet-0'",
    ],
    notes=[
        "克隆云服务器，需云服务器处于 stopped 状态。",
        "--vxnets 格式为 '源实例ID|目标私有网络ID'，可重复传入。",
    ],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("vxnets", "list", False, "私有网络映射数组，格式 'i-xxxx|vxnet-xxxx'"),
    ],
)

CEASE_INSTANCES = Action(
    "CeaseInstances",
    description="彻底销毁云服务器",
    examples=["iaas cease-instances --instances i-xxxx --dry-run"],
    notes=[
        "彻底销毁云服务器，不可恢复，请谨慎操作。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[Param("instances", "list", True, "云服务器 ID 数组")],
)

# ---------------------------------------------------------------------------
# Instance groups (placement groups)
# ---------------------------------------------------------------------------

CREATE_INSTANCE_GROUPS = Action(
    "CreateInstanceGroups",
    description="创建安置策略组",
    examples=[
        "iaas create-instance-groups --relation repel --instance-group-name ha-group",
        "iaas create-instance-groups --relation attract --instance-group-name same-host",
    ],
    notes=[
        "relation 取值：repel（分散，组内实例部署到不同物理节点）、attract（集中，部署到相同物理节点）。",
        "分散策略常用于高可用场景。",
    ],
    params=[
        Param("relation", "str", True, "组内实例关系，repel（分散）或 attract（集中）"),
        Param("instance_group_name", "str", False, "安置策略组名称"),
        Param("description", "str", False, "安置策略组描述"),
    ],
)

DELETE_INSTANCE_GROUPS = Action(
    "DeleteInstanceGroups",
    description="删除安置策略组",
    examples=["iaas delete-instance-groups --instance-groups ig-xxxx"],
    notes=["删除安置策略组，组内云服务器不受影响。"],
    params=[Param("instance_groups", "list", True, "安置策略组 ID 数组")],
)

JOIN_INSTANCE_GROUP = Action(
    "JoinInstanceGroup",
    description="云服务器加入安置策略组",
    examples=["iaas join-instance-group --instances i-xxxx --instance-group ig-xxxx"],
    notes=["将云服务器加入指定的安置策略组。"],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("instance_group", "str", True, "安置策略组 ID"),
    ],
)

LEAVE_INSTANCE_GROUP = Action(
    "LeaveInstanceGroup",
    description="云服务器离开安置策略组",
    examples=["iaas leave-instance-group --instances i-xxxx --instance-group ig-xxxx"],
    notes=["将云服务器从安置策略组中移除。"],
    params=[
        Param("instances", "list", True, "云服务器 ID 数组"),
        Param("instance_group", "str", True, "安置策略组 ID"),
    ],
)

DESCRIBE_INSTANCE_GROUPS = Action(
    "DescribeInstanceGroups",
    description="获取安置策略组信息",
    examples=[
        "iaas describe-instance-groups",
        "iaas describe-instance-groups --relation repel --output table",
    ],
    notes=["只读命令，返回安置策略组列表。"],
    params=[
        Param("instance_groups", "list", False, "安置策略组 ID 数组"),
        Param("relation", "str", False, "按关系过滤，repel 或 attract"),
        Param("tags", "list", False, "标签 ID 数组"),
        Param("owner", "str", False, "资源所有者 ID"),
        Param("verbose", "int", False, "是否返回冗长信息，1 为是"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
    ],
    table_columns=["instance_group_id", "instance_group_name", "relation", "create_time"],
)

# ---------------------------------------------------------------------------
# Virtual machine images
# ---------------------------------------------------------------------------

DESCRIBE_IMAGES = Action(
    "DescribeImages",
    description="获取镜像列表",
    examples=[
        "iaas describe-images",
        "iaas describe-images --visibility private --output table",
        "iaas describe-images --os-family centos --status available",
        "iaas describe-images --images img-xxxx",
    ],
    notes=[
        "只读命令，不会修改任何资源。",
        "--visibility 取值：public、private；--provider 取值：self、system。",
        "--os-family 取值：windows、debian、centos、ubuntu 等。",
    ],
    params=[
        Param("images", "list", False, "镜像 ID 数组"),
        Param("tags", "list", False, "标签 ID 数组"),
        Param("os_family", "str", False, "操作系统家族，如 windows、debian、centos、ubuntu"),
        Param("processor_type", "str", False, "处理器类型，64bit 或 32bit"),
        Param("status", "str", False, "状态，如 pending、available、deleted、ceased"),
        Param("visibility", "str", False, "可见性，public 或 private"),
        Param("provider", "str", False, "提供者，self 或 system"),
        Param("verbose", "int", False, "是否返回冗长信息，1 为是"),
        Param("search_word", "str", False, "搜索关键字"),
        Param("owner", "str", False, "资源所有者 ID"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
    ],
    table_columns=["image_id", "image_name", "os_family", "processor_type", "status", "visibility", "create_time"],
)

CAPTURE_INSTANCE = Action(
    "CaptureInstance",
    description="基于云服务器制作自有镜像",
    examples=[
        "iaas capture-instance --instance i-xxxx --image-name my-image",
        "iaas capture-instance --instance i-xxxx --image-name my-image --image-description 'backup'",
    ],
    notes=[
        "基于云服务器系统盘制作镜像，需云服务器处于 stopped 状态。",
        "制作镜像期间云服务器不可用，请谨慎操作。",
    ],
    params=[
        Param("instance", "str", True, "云服务器 ID"),
        Param("image_name", "str", False, "镜像名称"),
        Param("image_description", "str", False, "镜像描述"),
    ],
)

CAPTURE_IMAGE_FROM_SNAPSHOT = Action(
    "CaptureImageFromSnapshot",
    description="将指定备份导出为镜像",
    examples=[
        "iaas capture-image-from-snapshot --snapshot ss-xxxx --image-name my-image",
    ],
    notes=["基于备份（快照）制作镜像。"],
    params=[
        Param("snapshot", "str", True, "备份 ID"),
        Param("image_name", "str", False, "镜像名称"),
        Param("image_description", "str", False, "镜像描述"),
    ],
)

CLONE_IMAGES = Action(
    "CloneImages",
    description="克隆镜像",
    examples=[
        "iaas clone-images --images img-xxxx --image-name cloned-image",
    ],
    notes=["复制自有镜像，可用于跨区域复制等场景。"],
    params=[
        Param("images", "list", True, "镜像 ID 数组"),
        Param("image_name", "str", False, "新镜像名称"),
        Param("image_description", "str", False, "新镜像描述"),
    ],
)

DELETE_IMAGES = Action(
    "DeleteImages",
    description="删除自有镜像",
    examples=["iaas delete-images --images img-xxxx --dry-run"],
    notes=[
        "仅可删除 provider 为 self 的自有镜像。",
        "破坏性操作，建议先用 --dry-run 预览请求。",
    ],
    params=[Param("images", "list", True, "镜像 ID 数组")],
)

MODIFY_IMAGE_ATTRIBUTES = Action(
    "ModifyImageAttributes",
    description="修改镜像名称和描述",
    examples=[
        "iaas modify-image-attributes --image img-xxxx --image-name new-name",
        "iaas modify-image-attributes --image img-xxxx --description 'updated'",
    ],
    notes=["修改自有镜像的名称、描述等属性。"],
    params=[
        Param("image", "str", True, "镜像 ID"),
        Param("image_name", "str", False, "镜像名称"),
        Param("description", "str", False, "镜像描述"),
    ],
)

DESCRIBE_IMAGE_USERS = Action(
    "DescribeImageUsers",
    description="查询镜像共享的用户列表",
    examples=["iaas describe-image-users --image img-xxxx"],
    notes=["只读命令，返回共享了该镜像的用户列表。"],
    params=[
        Param("image", "str", True, "镜像 ID"),
        Param("offset", "int", False, "数据偏移量，默认 0"),
        Param("limit", "int", False, "返回数据长度，默认 20，最大 100"),
    ],
    table_columns=["user_id", "create_time"],
)

GRANT_IMAGE_TO_USERS = Action(
    "GrantImageToUsers",
    description="共享镜像给指定的用户",
    examples=["iaas grant-image-to-users --image img-xxxx --users usr-xxxx --users usr-yyyy"],
    notes=["将自有镜像共享给指定用户。"],
    params=[
        Param("image", "str", True, "镜像 ID"),
        Param("users", "list", True, "用户 ID 数组"),
    ],
)

REVOKE_IMAGE_FROM_USERS = Action(
    "RevokeImageFromUsers",
    description="撤销镜像共享",
    examples=["iaas revoke-image-from-users --image img-xxxx --users usr-xxxx"],
    notes=["撤销对指定用户的镜像共享。"],
    params=[
        Param("image", "str", True, "镜像 ID"),
        Param("users", "list", True, "用户 ID 数组"),
    ],
)

# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

ACTIONS = {
    # Cloud servers
    "describe-instances": DESCRIBE_INSTANCES,
    "run-instances": RUN_INSTANCES,
    "terminate-instances": TERMINATE_INSTANCES,
    "start-instances": START_INSTANCES,
    "stop-instances": STOP_INSTANCES,
    "restart-instances": RESTART_INSTANCES,
    "reset-instances": RESET_INSTANCES,
    "resize-instances": RESIZE_INSTANCES,
    "modify-instance-attributes": MODIFY_INSTANCE_ATTRIBUTES,
    "describe-instance-types": DESCRIBE_INSTANCE_TYPES,
    "clone-instances": CLONE_INSTANCES,
    "cease-instances": CEASE_INSTANCES,
    # Instance groups
    "create-instance-groups": CREATE_INSTANCE_GROUPS,
    "delete-instance-groups": DELETE_INSTANCE_GROUPS,
    "join-instance-group": JOIN_INSTANCE_GROUP,
    "leave-instance-group": LEAVE_INSTANCE_GROUP,
    "describe-instance-groups": DESCRIBE_INSTANCE_GROUPS,
    # Images
    "describe-images": DESCRIBE_IMAGES,
    "capture-instance": CAPTURE_INSTANCE,
    "capture-image-from-snapshot": CAPTURE_IMAGE_FROM_SNAPSHOT,
    "clone-images": CLONE_IMAGES,
    "delete-images": DELETE_IMAGES,
    "modify-image-attributes": MODIFY_IMAGE_ATTRIBUTES,
    "describe-image-users": DESCRIBE_IMAGE_USERS,
    "grant-image-to-users": GRANT_IMAGE_TO_USERS,
    "revoke-image-from-users": REVOKE_IMAGE_FROM_USERS,
}
