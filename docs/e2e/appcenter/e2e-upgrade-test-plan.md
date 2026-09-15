# AppCenter CLI E2E 测试计划：版本升级（真实 API）

## 1. 概述

### 1.1 目标

验证青云 AppCenter 的**版本升级**规则，使用真实青云 API 在专用测试集群上执行升级操作：

1. **规则 1**：每个版本都有一个配置字段（`cluster.json.mustache` 中的 `upgrade_policy`），指明哪些低版本能够升级到当前版本；
2. **规则 2**：以**普通模式**创建的低版本集群，只能升级到**已上架**版本（且该高版本配置符合规则 1）；
3. **规则 3**：以**调试模式**创建的低版本集群，能升级到**任何符合规则 1** 的高版本，无论高版本是已上架、已下架还是开发中。

### 1.2 范围

| 用例 | 低版本（创建模式） | 目标高版本 | 高版本状态 | 预期 |
| --- | --- | --- | --- | --- |
| U-01 | `appv-r89epe6m`（5.0.11，普通模式） | `appv-tvzeju2i`（7.2.14） | 已上架 | ✅ 成功 |
| U-02 | `appv-r89epe6m`（5.0.11，普通模式） | `appv-kxvo77jc`（7.2.11） | 已下架 | ❌ 失败（规则2） |
| U-03 | `appv-r89epe6m`（5.0.11，普通模式） | `appv-e3jvzled`（7.0.4） | 开发中 | ❌ 失败（规则2） |
| U-04 | `appv-2mer62ui`（7.2.7，调试模式） | `appv-tvzeju2i`（7.2.14） | 已上架 | ✅ 成功 |
| U-05 | `appv-2mer62ui`（7.2.7，调试模式） | `appv-kxvo77jc`（7.2.11） | 已下架 | ✅ 成功 |
| U-06 | `appv-r89epe6m`（5.0.11，调试模式） | `appv-e3jvzled`（7.0.4） | 开发中 | ✅ 成功 |

> **U-06 低版本说明**：规则 3 的开发中版本升级用例无法用 `appv-2mer62ui`（7.2.7）作为低版本——7.2.7 高于 7.0.4，属降级，不符合规则 1。开发中版本 `appv-e3jvzled` 配置与 `appv-vmg56wlp`（7.0.4）相同，其 `upgrade_policy` 含 `appv-r89epe6m`（5.0.11），故 U-06 用 5.0.11 作为低版本（调试模式创建）。

### 1.3 安全约束（重要）

- **只在测试集群上操作**：所有变更命令的目标必须是本次测试创建的集群 ID。
- **严禁修改其他集群**：账号下存在大量既有集群（含 active 的 `cl-u08lcjvy` 等），一律不得作为变更目标。
- 测试集群由本测试创建，测试结束（无论成功或失败）必须删除清理。
- 只读命令（`describe-*`）可查询任意集群，但**变更命令**仅允许作用于测试集群。

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| 配置方式 | `--config .qingcloud/config`（真实凭据，已 git 排除） |
| 测试应用 | Redis Standalone |
| 应用 ID | `app-zydumbxo` |
| 账号 owner | `usr-hRAmdSn6` |
| 多可用区网络 | `vxnet-kldf8dk`（VPC `rtr-52tkfywg`） |
| 多可用区部署 | region `pek3`，zones `["pek3b","pek3d"]` |
| API 地址 | `api.qingcloud.com`（默认） |

### 2.1 版本与升级关系（规则 1，来自各版本 `upgrade_policy`）

仅选用 **pek3 可部署、非 kylin/arm** 的版本：

| 版本 | 版本号 | 状态 | `upgrade_policy`（可升级到它的低版本） |
| --- | --- | --- | --- |
| `appv-tvzeju2i` | 7.2.14 | 已上架 | `pbn7ic5e`、`kxvo77jc`、`2mer62ui`、`2nnq72bm`、`uwuxvd2p`、`n0b7h67g`、`a0a319jr`、**`r89epe6m`**、`e97gz6wz` 等 |
| `appv-kxvo77jc` | 7.2.11 | 已下架 | `2mer62ui`、`2nnq72bm`、`uwuxvd2p`、`n0b7h67g`、`a0a319jr`、**`r89epe6m`**、`e97gz6wz` 等 |
| `appv-2mer62ui` | 7.2.7 | 已下架 | `uwuxvd2p`、`n0b7h67g`、`a0a319jr`、**`r89epe6m`**、`e97gz6wz` 等 |
| `appv-e3jvzled` | 7.0.4 | 开发中 | 配置同 `appv-vmg56wlp`：`a0a319jr`、**`r89epe6m`**、`e97gz6wz` 等 |
| `appv-r89epe6m` | 5.0.11 | 已上架 | 基础版本（无升级来源） |

> 说明：`appv-e3jvzled`（开发中）API 不可见，其配置与 `appv-vmg56wlp`（7.0.4，已下架）相同（用户确认），故其 `upgrade_policy` 参考 `appv-vmg56wlp` 的配置。

### 2.2 升级 API（UpgradeClusters）

依据青云 API 文档（[升级集群](https://docs.yuxingcloud.com/user_guide/development_docs/api/api_list/appcenter/cluster/upgrade_clusters/)）：

| 项 | 值 |
| --- | --- |
| Action | `UpgradeClusters` |
| Method / Path | GET `/iaas` |
| 请求参数 | `app_version`（目标版本 ID，必填）、`clusters`（集群 ID 数组） |
| 返回 | `cluster_ids`、`resize_info`、`job_id`、`ret_code` |

> **CLI 扩展**：当前 CLI 无 `upgrade-clusters` 命令，需在 `actions.py` 新增 `UPGRADE_CLUSTERS` action（参数 `app_version`、`clusters`），与 SDK/API 一致。

### 2.3 部署 conf 模板（多可用区）

低版本集群创建沿用调试模式测试的 conf 模板（多可用区，`instance_class=202`、`cpu=2`、`memory=2048`、`volume_size=20`、`count=1`、`volume_class=200`，不传 `global_uuid`）：

```json
{
  "version": "<低版本_id>",
  "cluster": {
    "name": "e2e-redis-upgrade-<case>",
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
  "env": { "disabled-commands": "no", "enable-acl": "yes" }
}
```

> 说明：`env` 使用最小必填项（此前生命周期测试已实证可行）；`debug` 通过 CLI `--debug 1` 传入（仅调试模式用例）。

## 3. 测试策略

1. **创建低版本集群**：每个用例先创建低版本集群（普通模式或调试模式），记录 `cluster_id`。
2. **等待集群 active**：轮询 `describe-clusters` 至 `active`。
3. **执行升级**：调用 `UpgradeClusters`（`--app-version <目标> --clusters <id>`），断言退出码与 `ret_code`。
4. **异步任务轮询**：升级返回 `job_id`，轮询 `describe-cluster-jobs` 与 `describe-clusters` 确认收敛。
5. **验证版本**：升级成功后 `describe-clusters` 的 `app_version` 变为目标版本。
6. **失败用例如实记录**：预期失败用例记录 `ret_code`/`message`，不视为 CLI 缺陷。
7. **清理**：测试结束删除所有成功创建的测试集群。

## 4. 测试用例

### U. 版本升级

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| U-01 | 普通模式 + 升级到已上架版本 | ① 普通模式创建 `appv-r89epe6m`（5.0.11）集群；② 等待 active；③ `upgrade-clusters --app-version appv-tvzeju2i --clusters <id>` | ③ 退出码 0，`ret_code=0`，返回 `job_id`；轮询后 `app_version=appv-tvzeju2i` |
| U-02 | 普通模式 + 升级到已下架版本 | ① 普通模式创建 `appv-r89epe6m`（5.0.11）集群；② 等待 active；③ `upgrade-clusters --app-version appv-kxvo77jc --clusters <id>` | ③ **预期失败**（规则2：普通模式只能升级到已上架版本）；如实记录 `ret_code`/`message` |
| U-03 | 普通模式 + 升级到开发中版本 | ① 普通模式创建 `appv-r89epe6m`（5.0.11）集群；② 等待 active；③ `upgrade-clusters --app-version appv-e3jvzled --clusters <id>` | ③ **预期失败**（规则2）；如实记录 `ret_code`/`message` |
| U-04 | 调试模式 + 升级到已上架版本 | ① 调试模式创建 `appv-2mer62ui`（7.2.7）集群；② 等待 active；③ `upgrade-clusters --app-version appv-tvzeju2i --clusters <id>` | ③ 退出码 0，`ret_code=0`，返回 `job_id`；轮询后 `app_version=appv-tvzeju2i` |
| U-05 | 调试模式 + 升级到已下架版本 | ① 调试模式创建 `appv-2mer62ui`（7.2.7）集群；② 等待 active；③ `upgrade-clusters --app-version appv-kxvo77jc --clusters <id>` | ③ 退出码 0，`ret_code=0`，返回 `job_id`；轮询后 `app_version=appv-kxvo77jc` |
| U-06 | 调试模式 + 升级到开发中版本 | ① 调试模式创建 `appv-r89epe6m`（5.0.11）集群；② 等待 active；③ `upgrade-clusters --app-version appv-e3jvzled --clusters <id>` | ③ 退出码 0，`ret_code=0`，返回 `job_id`；轮询后 `app_version=appv-e3jvzled` |
| U-07 | 清理 | 对 U-01~U-06 创建的集群执行 `delete-clusters --clusters <id>` | 退出码 0，返回 `job_id`，`ret_code=0` |
| U-08 | 等待删除完成 | 轮询 `describe-clusters --clusters <id>` | 状态收敛为 `deleted` 或查询返回空（超时上限 10 分钟） |

> 说明：
> - U-01/U-02/U-03 共用同一低版本 `appv-r89epe6m`（5.0.11），可创建 1 个普通模式集群依次尝试 3 个目标（先成功升级到上架版本，再对**新集群**尝试下架/开发中目标）；也可各建 1 个集群。为隔离失败影响，**每个目标使用独立集群**。
> - U-04/U-05 共用低版本 `appv-2mer62ui`（7.2.7），U-06 用 `appv-r89epe6m`（5.0.11，因 7.2.7 不能降级到 7.0.4）。
> - 预期失败用例（U-02/U-03）若 API 返回错误则无版本变更，集群仍可清理。

## 5. 执行方式

```bash
cd /workspace/qc-tools
# 先扩展 CLI：actions.py 新增 UPGRADE_CLUSTERS（app_version、clusters）
# 按 U-01 → U-06 顺序执行（每个用例依赖前一用例结果，不适合纯 pytest 参数化）
```

执行脚本将按用例组织，每个用例：
1. 创建低版本集群（普通/调试模式），断言 `ret_code=0`；
2. 轮询 `describe-clusters` 至 `active`；
3. 调用 `upgrade-clusters`，断言退出码与 `ret_code`（预期失败用例除外）；
4. 轮询 job / 集群状态，验证 `app_version` 变化；
5. 收尾统一删除清理。

## 6. 风险与限制

- **真实资源与费用**：测试会创建多个真实集群（U-01~U-06 各 1 个），产生少量费用；测试结束必须删除。
- **升级耗时**：升级为异步任务，单步可能耗时数分钟，需设置合理轮询超时。
- **开发中版本不可见**：`appv-e3jvzled` API 不可见，其 `upgrade_policy` 参考 `appv-vmg56wlp`（用户确认配置相同）；若实际升级行为与预期不符，如实记录。
- **CLI 扩展**：需新增 `upgrade-clusters` 命令（`UPGRADE_CLUSTERS` action），并补充单元测试。
- **严禁误操作**：所有变更命令的目标 ID 必须来自本测试创建的集群；脚本内对目标 ID 做前缀/来源校验，防止误伤其他集群。
- **凭据安全**：`.qingcloud/config` 含真实凭据，已 git 排除，权限 600。
