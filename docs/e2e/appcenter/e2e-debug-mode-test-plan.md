# AppCenter CLI E2E 测试计划：调试模式创建集群（真实 API）

## 1. 概述

### 1.1 目标

验证能否使用**调试模式**（`DeployAppVersion` 的 `debug:1` 参数）创建集群。用户提供版本 ID，使用该版本以调试模式部署集群，覆盖三种版本状态：

| 情况 | 版本状态 | 版本 ID |
| --- | --- | --- |
| 情况 1 | 已上架（active） | `appv-tvzeju2i` |
| 情况 2 | 已下架（suspended） | `appv-kxvo77jc` |
| 情况 3 | 开发中（API 不可见） | `appv-e3jvzled` |

### 1.2 范围

| 用例 | 版本 | 状态 | 调试模式 | 说明 |
| --- | --- | --- | --- | --- |
| D-01 | `appv-tvzeju2i` | 已上架 | `debug:1` | 调试模式 + 上架版本 |
| D-02 | `appv-kxvo77jc` | 已下架 | `debug:1` | 调试模式 + 下架版本 |
| D-03 | `appv-e3jvzled` | 开发中 | `debug:1` | 调试模式 + 开发中版本 |
| D-04（对照） | `appv-kxvo77jc` | 已下架 | 不传 `debug` | 非调试模式 + 下架版本（预期失败，作为对照） |

### 1.3 安全约束（重要）

- **只在测试集群上操作**：所有变更命令的目标必须是本次测试创建的集群 ID。
- **严禁修改其他集群**：账号下存在大量既有集群（含 active 调试集群 `cl-u08lcjvy`、`cl-7flkazd8` 等），一律不得作为变更目标。
- 测试集群由本测试创建，测试结束（无论成功或失败）必须删除清理。
- 只读命令（`describe-*`）可查询任意集群，但**变更命令**仅允许作用于测试集群。

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| 配置方式 | `--config .qingcloud/config`（真实凭据，已 git 排除） |
| 测试应用 | Redis Standalone |
| 应用 ID | `app-zydumbxo` |
| 账号 owner | `usr-hRAmdSn6`（普通用户账号，非应用开发者） |
| 多可用区网络 | `vxnet-kldf8dk`（VPC `rtr-52tkfywg`） |
| 多可用区部署 | region `pek3`，zones `["pek3b","pek3d"]` |
| API 地址 | `api.qingcloud.com`（默认） |

### 2.1 部署规格（参考用户提供的 API 示例）

依据用户提供的真实请求示例，节点规格如下（非最小规格，与示例一致）：

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| `instance_class` | `202` | 与示例一致 |
| `cpu` | `2` | 与示例一致 |
| `memory` | `2048` | 与示例一致（MiB） |
| `volume_size` | `20` | 与示例一致（GiB） |
| `count` | `1` | 单节点 |
| `volume_class` | `200` | 与示例一致 |

### 2.2 部署模式

采用**多可用区**部署（与示例一致）：顶层 `zone=pek3`（region），`multi_deploy_zones=["pek3b","pek3d"]`，conf 内**不带** `zone` 字段。

### 2.3 部署 conf 模板（多可用区，调试模式）

依据用户提供的示例，`env` 使用示例中的默认值，`debug:1` 通过 CLI `--debug 1` 传入：

```json
{
  "version": "<version_id>",
  "cluster": {
    "name": "e2e-redis-debug-<case>",
    "description": "",
    "auto_backup_time": "-1",
    "node": {
      "instance_class": 202,
      "cpu": 2,
      "memory": 2048,
      "volume_size": 20,
      "count": 1,
      "volume_class": 200
    },
    "vxnet": "vxnet-kldf8dk"
  },
  "vpc": "rtr-52tkfywg",
  "ip": "0",
  "reserved_ip": "0",
  "env": {
    "disabled-commands": "no",
    "enable-acl": "yes",
    "port": 6379,
    "sentinel.port": 26379,
    "sentinel.down-after-milliseconds": 4000,
    "sentinel.failover-timeout": 60000,
    "sentinel.requirepass": "",
    "sentinel.tls-port": 0,
    "maxmemory_portion": 80,
    "databases": 16,
    "enable-commands": "DISABLE_ALL",
    "io-threads-do-reads": "auto",
    "io-threads": 0,
    "activerehashing": "yes",
    "save": "",
    "appendonly": "yes",
    "appendfsync": "everysec",
    "latency-monitor-threshold": 0,
    "maxclients": 65000,
    "requirepass": "",
    "maxmemory-policy": "volatile-lru",
    "maxmemory-samples": 3,
    "maxmemory-clients": "0",
    "min-replicas-max-lag": 10,
    "min-replicas-to-write": 0,
    "no-appendfsync-on-rewrite": "yes",
    "notify-keyspace-events": "",
    "repl-backlog-size": "1mb",
    "repl-backlog-ttl": 3600,
    "repl-timeout": 60,
    "slowlog-log-slower-than": -1,
    "slowlog-max-len": 128,
    "tcp-keepalive": 300,
    "timeout": 0,
    "shutdown-timeout": 10,
    "set-max-intset-entries": 512,
    "list-max-listpack-size": -2,
    "zset-max-listpack-entries": 128,
    "zset-max-listpack-value": 64,
    "hash-max-listpack-entries": 512,
    "hash-max-listpack-value": 64,
    "lua-time-limit": 5000,
    "client-output-buffer-limit-normal": "0 0 0",
    "client-output-buffer-limit-replica": "256mb 128mb 60",
    "client-output-buffer-limit-pubsub": "32mb 8mb 60",
    "tls-port": 0,
    "tls-replication": "no",
    "tls-auth-clients": "no",
    "tls-protocols": "",
    "tls-ciphers": "",
    "tls-ciphersuites": "",
    "tls-prefer-server-ciphers": "no",
    "tls-session-caching": "yes",
    "tls-session-cache-size": 20480,
    "tls-session-cache-timeout": 300,
    "tls-cert": "",
    "tls-key": "",
    "tls-ca-cert": "",
    "tls-dh-params": "",
    "node-exporter-enable": false,
    "redis-exporter-enable": false,
    "web.console.enabled": false,
    "web.console.username": "admin",
    "web.console.password": "",
    "preferred-az": ""
  }
}
```

> 说明：
> - **`debug:1`**：通过 CLI `--debug 1` 传入（`deploy-app-version` 已支持 `--debug` 整数参数，序列化为 `debug=1`，无需扩展 CLI）。
> - **`global_uuid`**：**不传**。该参数为可选（此前已实证不传也可部署成功），本测试按用户要求省略。
> - **`charge_mode`/`app_id`/`place_type`**：示例顶层含这些字段，但 CLI 未暴露且均为可选（此前生命周期测试未传即成功），本测试不传。
> - **`preferred-az`**：位于 `env` 末尾（与示例一致）。

### 2.4 背景证据（来自既有集群）

测试前对账号下 `app-zydumbxo` 的既有集群做了只读统计，用于支撑预期：

| 版本 | 状态 | 非调试集群数 | 调试集群数 | 说明 |
| --- | --- | --- | --- | --- |
| `appv-tvzeju2i` | 已上架 | 10 | 13 | 上架版本两种模式均可部署 |
| `appv-kxvo77jc` | 已下架 | 0 | 32 | **下架版本仅调试模式可部署**（含 active 的 `cl-u08lcjvy`） |
| `appv-e3jvzled` | 开发中 | 0 | 0 | **从未被部署过**，行为未知 |

## 3. 测试策略

1. **创建专用测试集群**：每个用例通过 `deploy-app-version --debug 1` 部署，记录返回的 `cluster_id` 作为后续唯一目标。
2. **异步任务轮询**：部署返回 `job_id`，轮询 `describe-clusters` 确认集群状态收敛（`active` / 失败）。
3. **调试模式验证**：`describe-clusters` 返回的 `debug` 字段（布尔值）为 `True`，即确认调试模式生效。
4. **失败用例如实记录**：若部署返回业务错误（如版本不可用），记录 `ret_code` 与 `message`，不视为 CLI 缺陷。
5. **清理**：测试结束删除所有成功创建的测试集群；若中途失败，也必须在收尾阶段尝试删除。

## 4. 测试用例

### D. 调试模式创建集群

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| D-01 | 调试模式 + 已上架版本 | `deploy-app-version --zone pek3 --multi-deploy-zones pek3b --multi-deploy-zones pek3d --version-id appv-tvzeju2i --debug 1 --conf '<模板(version=appv-tvzeju2i)>'` | 退出码 0，JSON 含 `cluster_id`、`job_id`，`ret_code=0` |
| D-01b | 等待集群 active | 轮询 `describe-clusters --clusters <id>` | 状态收敛为 `active`（超时上限 15 分钟） |
| D-01c | 验证调试模式 | `describe-clusters --clusters <id>` | `debug=True`，`app_version=appv-tvzeju2i` |
| D-02 | 调试模式 + 已下架版本 | `deploy-app-version --zone pek3 --multi-deploy-zones pek3b --multi-deploy-zones pek3d --version-id appv-kxvo77jc --debug 1 --conf '<模板(version=appv-kxvo77jc)>'` | 退出码 0，JSON 含 `cluster_id`、`job_id`，`ret_code=0` |
| D-02b | 等待集群 active | 轮询 `describe-clusters --clusters <id>` | 状态收敛为 `active`（超时上限 15 分钟） |
| D-02c | 验证调试模式 | `describe-clusters --clusters <id>` | `debug=True`，`app_version=appv-kxvo77jc` |
| D-03 | 调试模式 + 开发中版本 | `deploy-app-version --zone pek3 --multi-deploy-zones pek3b --multi-deploy-zones pek3d --version-id appv-e3jvzled --debug 1 --conf '<模板(version=appv-e3jvzled)>'` | **预期失败**（开发中版本 API 不可见）；如实记录 `ret_code`/`message`；若意外成功则按 D-01b/c 验证并清理 |
| D-04 | 对照：非调试模式 + 已下架版本 | `deploy-app-version --zone pek3 --multi-deploy-zones pek3b --multi-deploy-zones pek3d --version-id appv-kxvo77jc --conf '<模板(version=appv-kxvo77jc)>'`（**不传** `--debug`） | **预期失败**（下架版本非调试模式不可部署）；如实记录 `ret_code`/`message` |
| D-05 | 清理 | 对 D-01/D-02（及 D-03 若成功）创建的集群执行 `delete-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| D-06 | 等待删除完成 | 轮询 `describe-clusters --clusters <id>` | 状态收敛为 `deleted` 或查询返回空（超时上限 10 分钟） |

> 说明：
> - D-03 与 D-04 为**预期失败**用例，若 API 返回错误则无集群产生，无需清理；若意外成功，则按成功用例流程验证并清理。
> - 每个用例的集群名使用 `e2e-redis-debug-01/02/03`，便于识别与隔离。

## 5. 执行方式

```bash
cd /workspace/qc-tools
# 按 D-01 → D-02 → D-03 → D-04 → D-05/D-06 顺序执行（每个用例依赖前一用例结果，不适合纯 pytest 参数化）
```

执行脚本将按用例组织，每个用例：
1. 执行 `deploy-app-version`，断言退出码与 `ret_code=0`（预期失败用例除外）；
2. 轮询 `describe-clusters` 直至收敛或超时；
3. 用只读命令断言 `debug=True` 与版本一致；
4. 收尾统一删除清理。

## 6. 风险与限制

- **真实资源与费用**：测试会创建真实集群（D-01/D-02 各 1 个，D-03 视结果），产生少量费用；测试结束必须删除。
- **调试模式权限**：调试模式通常为应用开发者能力，本账号为普通用户；既有证据（32 个下架版本调试集群）表明普通账号可创建，但 D-01/D-02 仍可能因权限返回错误，如实记录。
- **开发中版本不可见**：`appv-e3jvzled` 在 API 中 `total_count=0`，D-03 预期失败；若调试模式允许部署，则记录为重要发现。
- **异步任务耗时**：创建为异步任务，单步可能耗时数分钟，需设置合理轮询超时。
- **严禁误操作**：所有变更命令的目标 ID 必须来自本测试创建的集群；脚本内对目标 ID 做前缀/来源校验，防止误伤其他集群（含 active 的 `cl-u08lcjvy`）。
- **凭据安全**：`.qingcloud/config` 含真实凭据，已 git 排除，权限 600。
