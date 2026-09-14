# AppCenter CLI E2E 测试计划：describe-app-versions --status 过滤参数（真实 API）

## 1. 概述

### 1.1 目标

对 `appcenter-cli` 的 `describe-app-versions` 命令新增的 **`--status` 过滤参数**进行端到端（E2E）测试，使用真实青云 API，验证：
- 按版本状态（`active` / `suspended`）过滤查询；
- 多状态组合过滤；
- 默认行为（不带 `--status`）；
- 无效状态值处理；
- 与 `limit`/`offset` 分页组合。

### 1.2 范围

| 用例 | 命令 | 说明 |
| --- | --- | --- |
| 默认查询 | `describe-app-versions --app-ids <id>` | 不带 `--status`，验证默认只返回 active |
| 单状态过滤 | `describe-app-versions --app-ids <id> --status active` | 只返回 active 版本 |
| 单状态过滤 | `describe-app-versions --app-ids <id> --status suspended` | 只返回 suspended（下架）版本 |
| 多状态过滤 | `describe-app-versions --app-ids <id> --status active --status suspended` | 返回全部版本 |
| 状态一致性 | 校验返回的每个版本 `status` 字段 | 与过滤条件一致 |
| 无效状态 | `describe-app-versions --app-ids <id> --status draft` | 返回 `InvailidRequestFormat`（1100） |
| 分页组合 | `--status suspended --limit 5 --offset 0/5` | 分页正确 |

### 1.3 安全约束

- 本测试**只读**（`describe-*`），不创建/修改/删除任何资源，无费用产生。
- 仅查询指定应用 `app-y6i338bf`，不涉及其他资源。

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| 配置方式 | `--config .qingcloud/config`（真实凭据，已 git 排除） |
| 测试应用 | `app-y6i338bf`（含 active 8 个 + suspended 15 个 = 23 个版本） |
| API 地址 | `api.qingcloud.com`（默认） |

## 3. 测试策略

1. 每个用例执行 `describe-app-versions`，断言退出码与 `ret_code=0`（无效状态除外）。
2. 校验 `total_count` 与返回的 `version_set` 数量。
3. 校验返回的每个版本 `status` 字段与过滤条件一致。
4. 无效状态用例断言返回 `ret_code=1100`（`InvailidRequestFormat`）。

## 4. 测试用例

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| S-01 | 默认查询（不带 --status） | `describe-app-versions --app-ids app-y6i338bf` | `ret_code=0`，`total_count=8`，全部 `status=active` |
| S-02 | 过滤 active | `describe-app-versions --app-ids app-y6i338bf --status active` | `ret_code=0`，`total_count=8`，全部 `status=active` |
| S-03 | 过滤 suspended | `describe-app-versions --app-ids app-y6i338bf --status suspended` | `ret_code=0`，`total_count=15`，全部 `status=suspended` |
| S-04 | 多状态组合 | `describe-app-versions --app-ids app-y6i338bf --status active --status suspended` | `ret_code=0`，`total_count=23`，含 active 与 suspended |
| S-05 | 状态一致性 | 对 S-02/S-03/S-04 返回的每个版本校验 `status` 字段 | 每个版本 `status` 均属于过滤条件集合 |
| S-06 | 无效状态值 | `describe-app-versions --app-ids app-y6i338bf --status draft` | 退出码非 0，`ret_code=1100`（`InvailidRequestFormat`） |
| S-07 | 分页组合 | `describe-app-versions --app-ids app-y6i338bf --status suspended --limit 5 --offset 0` 与 `--offset 5` | 两页各 5 个，无重复，合计 10 个 |
| S-08 | suspended 版本按 version_id 查询 | `describe-app-versions --version-ids <suspended_id>` | `ret_code=0`，`total_count=0`（suspended 版本无法按 version_id 定位） |
| S-09 | 开发中版本查询 | `describe-app-versions --version-ids appv-p17zoert` | `ret_code=0`，`total_count=0`（开发中版本 API 不可见） |

## 5. 执行方式

```bash
cd /workspace/appcenter-cli
# 按 S-01 → S-07 顺序执行，均为只读命令
```

## 6. 风险与限制

- **只读测试**：不创建资源，无费用、无清理需求。
- **版本数量可能变化**：若应用版本状态在测试期间变化，`total_count` 可能不同，以实际返回为准。
- **无效状态值**：API 对未知状态返回 `InvailidRequestFormat`，属预期行为。
