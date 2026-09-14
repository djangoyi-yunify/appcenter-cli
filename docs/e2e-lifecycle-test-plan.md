# AppCenter CLI E2E 测试计划：集群生命周期管理（真实 API）

## 1. 概述

### 1.1 目标

对 `appcenter-cli` 的**集群生命周期管理**能力进行端到端（E2E）测试，使用**真实青云 API**，在**专用测试集群**上完整走一遍生命周期：**创建 → 垂直扩容 → 水平扩容 → 修改配置 → 关闭/启动 → 删除**，验证每个环节的命令入口、参数构造、请求签名、异步任务执行与状态收敛均按预期工作。

### 1.2 范围

| 生命周期阶段 | 对应命令 | 说明 |
| --- | --- | --- |
| 创建 | `deploy-app-version` | 部署 Redis Standalone 测试集群（最小规格） |
| 垂直扩容 | `resize-cluster` | 调整 CPU / 内存 |
| 水平扩容 | `add-cluster-nodes` / `delete-cluster-nodes` | 增加 / 删除节点 |
| 修改配置 | `update-cluster-env` | 修改集群环境变量 |
| 关闭/启动 | `stop-clusters` / `start-clusters` | 停止 / 启动集群 |
| 删除 | `delete-clusters` | 删除测试集群（清理） |
| 单可用区部署（附加） | `deploy-app-version` / `delete-clusters` | 额外验证单可用区部署（zone `pek3b`） |

### 1.3 安全约束（重要）

- **只在测试集群上操作**：所有变更命令的目标必须是本次测试创建的集群 ID。
- **严禁修改其他集群**：测试过程中绝不使用账号下已有的任何集群（如 `cl-7flkazd8`、`cl-0qszsfxt` 等）作为变更目标。
- 测试集群由本测试创建，测试结束（无论成功或失败）必须删除清理。
- 只读命令（`describe-*`）可查询任意集群，但**变更命令**仅允许作用于测试集群。

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| 配置方式 | `--config .qingcloud/config`（真实凭据，已 git 排除） |
| 测试应用 | Redis Standalone |
| 应用 ID | `app-zydumbxo` |
| 版本 ID | `appv-tvzeju2i` |
| 多可用区网络 | `vxnet-kldf8dk`（VPC `rtr-52tkfywg`） |
| 多可用区部署 | region `pek3`，zones `["pek3b","pek3d"]` |
| 单可用区网络 | `vxnet-mn82b92`（VPC `rtr-52tkfywg`） |
| 单可用区部署 | zone `pek3b` |
| API 地址 | `api.qingcloud.com`（默认） |

### 2.1 部署规格（取应用支持的最小值）

依据 `appv-tvzeju2i` 的 `config.json`：

| 配置项 | 最小值 | 说明 |
| --- | --- | --- |
| `instance_class` | `101` | 基础型云服务器（range 最小值） |
| `cpu` | `1` | range `[1,2,4,8,16]` 最小值 |
| `memory` | `1024` | range `[1024,2048,...]` 最小值（MiB） |
| `volume_size` | `10` | min=10（GiB） |
| `count` | `1` | range `[1,3,5,7,9]` 最小值 |

### 2.2 部署模式：多可用区 vs 单可用区

集群部署分两种模式，请求差异如下（参考真实控制台请求）。**术语**：`pek3` 是 **region**（区域），`pek3b`、`pek3d` 是 **zone**（可用区）。

| 维度 | 多可用区 | 单可用区 |
| --- | --- | --- |
| 顶层 `zone` | region，如 `pek3` | 具体 zone，如 `pek3d` |
| `multi_deploy_zones` | `["pek3b","pek3d"]`（zone 列表） | `[]` |
| conf 内部 `zone` | 无 | `"zone":"pek3d"` |
| 节点 `instance_class` | `101` | `202` |
| 节点 `volume_class` | `100` | `200` |

> 本测试采用**多可用区**部署：顶层 `zone=pek3`（region），`multi_deploy_zones=["pek3b","pek3d"]`，conf 内**不带** `zone` 字段。

### 2.3 部署 conf 模板（多可用区）

依据真实请求格式，`env` 尽量使用默认值，仅必填项显式给出：

```json
{
  "version": "appv-tvzeju2i",
  "cluster": {
    "name": "e2e-redis-lifecycle",
    "description": "",
    "auto_backup_time": "-1",
    "node": {
      "instance_class": 101,
      "cpu": 1,
      "memory": 1024,
      "volume_size": 10,
      "count": 1,
      "volume_class": 100
    },
    "vxnet": "vxnet-kldf8dk",
    "global_uuid": 0.123456789
  },
  "vpc": "rtr-52tkfywg",
  "ip": "0",
  "reserved_ip": "0",
  "env": {
    "disabled-commands": "no",
    "enable-acl": "yes"
  },
  "agreement": true
}
```

> 说明：
> - 多可用区：顶层 `zone=pek3`（region），`multi_deploy_zones=["pek3b","pek3d"]`，conf 内**不带** `zone` 字段。
> - `vpc` 为 vxnet 所属 VPC 路由器 ID（`vxnet-kldf8dk` → `rtr-52tkfywg`）。
> - `global_uuid` 为随机小数，用于区分同名集群。
> - `env` 中 `required=yes` 的项（`disabled-commands`、`enable-acl`）按默认值显式填写；其余不传（平台取默认值）。

### 2.4 CLI 能力说明

- **已扩展**：`deploy-app-version` 已支持 `multi_deploy_zones`（list 类型，可重复 `--multi-deploy-zones`），序列化为 `multi_deploy_zones.1/.2`，与官方 SDK 一致（提交 `b79dcad`）。
- **`zone`**：走全局 `--zone` 参数（多可用区用 region `pek3`，单可用区用具体 zone `pek3b`）。
- **`app_id`/`charge_mode`**：SDK 中 `deploy_app_version` 仅 `version_id`/`conf` 为必填，暂不补充；若真实 API 必需再行扩展。

### 2.5 单可用区部署 conf 模板

单可用区部署：顶层 `zone` 用具体 zone（`pek3b`），conf 内**带** `zone` 字段，`multi_deploy_zones=[]`（不传）。网络用 `vxnet-mn82b92`。

```json
{
  "version": "appv-tvzeju2i",
  "cluster": {
    "name": "e2e-redis-lifecycle-single",
    "description": "",
    "auto_backup_time": "-1",
    "node": {
      "instance_class": 202,
      "cpu": 1,
      "memory": 1024,
      "volume_size": 10,
      "count": 1,
      "volume_class": 200
    },
    "vxnet": "vxnet-mn82b92",
    "global_uuid": 0.987654321
  },
  "zone": "pek3b",
  "vpc": "rtr-52tkfywg",
  "ip": "0",
  "reserved_ip": "0",
  "env": {
    "disabled-commands": "no",
    "enable-acl": "yes"
  },
  "agreement": true
}
```

> 说明：单可用区节点规格参考真实示例（`instance_class=202`、`volume_class=200`）；`vpc` 沿用 `rtr-52tkfywg`（`vxnet-mn82b92` 所属 VPC，见测试环境表）。

## 3. 测试策略

1. **创建专用测试集群**：通过 `deploy-app-version` 创建，记录返回的 `cluster_id` 作为后续所有变更命令的唯一目标。
2. **异步任务轮询**：每个变更命令返回 `job_id`，通过 `describe-cluster-jobs` 轮询任务状态（`pending → working → successful/failed`），并轮询 `describe-clusters` 确认集群状态收敛（`active` / `stopped` / `deleted`）。
3. **顺序执行**：生命周期各阶段严格按顺序执行，前一阶段成功后才进入下一阶段。
4. **状态断言**：每个阶段结束后，用只读命令验证实际状态/配置与预期一致。
5. **清理**：测试结束删除测试集群；若中途失败，也必须在收尾阶段尝试删除。

## 4. 测试用例清单

### G. 创建集群

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| G-01 | 部署最小规格集群（多可用区） | `deploy-app-version --zone pek3 --multi-deploy-zones pek3b --multi-deploy-zones pek3d --version-id appv-tvzeju2i --conf '<模板>'` | 退出码 0，JSON 含 `cluster_id`、`job_id`，`ret_code=0` |
| G-02 | 等待集群 active | 轮询 `describe-clusters --clusters <id>` | 集群状态收敛为 `active`（超时上限 15 分钟） |
| G-03 | 验证最小规格 | `describe-clusters --clusters <id>`（verbose） | `cpu=1`、`memory=1024`、`volume_size=10`、`node_count=1` |

### H. 垂直扩容

> 单角色应用需显式传 `--node-role ""`（空字符串角色），否则返回 `InternalError`（5000）。

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| H-01 | 增加 CPU | `resize-cluster --cluster <id> --node-role "" --cpu 2` | 退出码 0，返回 `job_id`，`ret_code=0` |
| H-02 | 等待任务完成 | 轮询 `describe-cluster-jobs` | job 状态 `successful` |
| H-03 | 验证 CPU | `describe-clusters --clusters <id>` | `cpu=2` |
| H-04 | 增加内存 | `resize-cluster --cluster <id> --node-role "" --memory 2048` | 退出码 0，返回 `job_id`，`ret_code=0` |
| H-05 | 等待任务完成 | 轮询 `describe-cluster-jobs` | job 状态 `successful` |
| H-06 | 验证内存 | `describe-clusters --clusters <id>` | `memory=2048` |

### I. 水平扩容

> 节点数必须为奇数（range `[1,3,5,7,9]`），因此扩容从 1 个节点增加到 3 个，再缩回 1 个。

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| I-01 | 增加节点 | `add-cluster-nodes --cluster <id> --node-count 2` | 退出码 0，返回 `job_id`，`ret_code=0` |
| I-02 | 等待任务完成 | 轮询 `describe-cluster-jobs` | job 状态 `successful` |
| I-03 | 验证节点数 | `describe-clusters --clusters <id>` | `node_count=3`（奇数） |
| I-04 | 获取节点 ID | `describe-cluster-nodes --cluster <id>` | 记录新增节点 `node_id`（2 个） |
| I-05 | 删除新增节点 | `delete-cluster-nodes --cluster <id> --nodes <node_id1> --nodes <node_id2>` | 退出码 0，返回 `job_id`，`ret_code=0`（删除 2 个新增节点，3→1） |
| I-06 | 等待任务完成 | 轮询 `describe-cluster-jobs` | job 状态 `successful` |
| I-07 | 验证节点数 | `describe-clusters --clusters <id>` | `node_count=1`（奇数） |

### J. 修改配置

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| J-01 | 修改环境变量 | `update-cluster-env --cluster <id> --env '{"maxmemory-policy":"allkeys-lru"}'` | 退出码 0，返回 `job_id`，`ret_code=0` |
| J-02 | 等待任务完成 | 轮询 `describe-cluster-jobs` | job 状态 `successful` |
| J-03 | 验证配置生效 | `describe-cluster-env --cluster-id <id>` | `maxmemory-policy` 值为 `allkeys-lru` |

### K. 关闭/启动

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| K-01 | 停止集群 | `stop-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| K-02 | 等待停止完成 | 轮询 `describe-clusters --clusters <id>` | 集群状态收敛为 `stopped`（超时上限 10 分钟） |
| K-03 | 启动集群 | `start-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| K-04 | 等待启动完成 | 轮询 `describe-clusters --clusters <id>` | 集群状态收敛为 `active`（超时上限 10 分钟） |

### L. 删除集群（清理）

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| L-01 | 删除测试集群 | `delete-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| L-02 | 等待删除完成 | 轮询 `describe-clusters --clusters <id>` | 集群状态收敛为 `deleted` 或查询返回空（超时上限 10 分钟） |

### M. 单可用区部署（附加验证）

> 主生命周期（G-L）使用多可用区集群；本组额外验证**单可用区**部署（zone `pek3b`，vxnet `vxnet-mn82b92`），创建后验证规格并删除清理。

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| M-01 | 部署单可用区集群 | `deploy-app-version --zone pek3b --version-id appv-tvzeju2i --conf '<单可用区模板>'` | 退出码 0，JSON 含 `cluster_id`、`job_id`，`ret_code=0` |
| M-02 | 等待集群 active | 轮询 `describe-clusters --clusters <id>` | 集群状态收敛为 `active`（超时上限 15 分钟） |
| M-03 | 验证最小规格 | `describe-clusters --clusters <id>`（verbose） | `cpu=1`、`memory=1024`、`volume_size=10`、`node_count=1` |
| M-04 | 删除单可用区集群 | `delete-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| M-05 | 等待删除完成 | 轮询 `describe-clusters --clusters <id>` | 状态收敛为 `deleted` 或查询返回空（超时上限 10 分钟） |

## 5. 执行方式

```bash
cd /workspace/appcenter-cli
# 手动按 G → L → M 顺序执行（每个阶段依赖前一阶段结果，不适合纯 pytest 参数化）
```

执行脚本将按阶段组织，每个阶段：
1. 执行变更命令，断言退出码与 `ret_code=0`；
2. 轮询 job / 集群状态直至收敛或超时；
3. 用只读命令断言最终状态。

## 6. 风险与限制

- **真实资源与费用**：测试会创建真实集群（最小规格，多可用区 + 单可用区各一个），产生少量费用；测试结束必须删除。
- **异步任务耗时**：创建/扩容/启停均为异步任务，单步可能耗时数分钟，需设置合理轮询超时。
- **应用能力限制**：若 Redis Standalone 不支持某项操作（如水平扩容），API 会返回业务错误，测试将如实记录并跳过该阶段，不视为 CLI 缺陷。
- **严禁误操作**：所有变更命令的目标 ID 必须来自本测试创建的集群；脚本内对目标 ID 做前缀/来源校验，防止误伤其他集群。
- **凭据安全**：`.qingcloud/config` 含真实凭据，已 git 排除，权限 600。
