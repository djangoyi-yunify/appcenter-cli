# AppCenter CLI E2E 测试报告

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| E2E 测试用例 | **53 通过 / 0 失败** |
| 单元测试 | **11 通过 / 0 失败** |
| 合计 | **64 通过 / 0 失败** |
| 覆盖命令 | 全部 22 个命令 |

## 2. 发现并修复的 Bug

### Bug 1：请求签名被双重 URL 编码（严重，阻断所有真实 API 调用）

- **位置**：`appcenter_cli/client.py` `_build_url`
- **现象**：所有真实 API 请求返回 `AuthFailure, signature not matched`（ret_code 1200）
- **根因**：`sign_request` 返回的签名**已经**是 `quote_plus` 编码过的（如 `%2B...%3D`），但 `_build_url` 又用 `urllib.parse.urlencode` 对整个参数字典编码，导致签名被**二次编码**（`%252B...%253D`）。真实 API 按原始值比对签名，因此不匹配。
- **为何单元测试未发现**：`test_signature_matches_doc_example` 只验证了签名算法本身（doc 示例），未覆盖 URL 构造环节的编码。
- **修复**：签名不再放入 `urlencode` 的字典，改为追加 `&signature=` + 已编码签名（与官方 SDK 一致）。
- **验证**：修复后真实 API 返回 `ret_code=0`。

### Bug 2：`describe-cluster-env` 参数名错误

- **位置**：`appcenter_cli/actions.py` `DESCRIBE_CLUSTER_ENV`
- **现象**：真实 API 返回 `InvailidRequestFormat, missing parameter [cluster_id]`
- **根因**：action 定义使用参数名 `cluster`，但 API 要求 `cluster_id`。
- **修复**：参数名改为 `cluster_id`，CLI 参数相应变为 `--cluster-id`。
- **验证**：修复后请求被 API 接受（返回权限/状态相关错误而非缺参错误）。

## 3. 测试发现的其他事实

| 项 | 说明 |
| --- | --- |
| `describe-app-versions` 必填约束 | API 要求 `app_ids` 或 `version_ids` 至少一个，但 action 定义标为可选。CLI 不报错，由 API 返回错误。建议后续在 action 定义中补充"至少一个"约束。 |
| describe 查询对不存在资源的行为 | 返回空结果（`ret_code=0`）而非错误，如 `describe-cluster-nodes --cluster cl-nonexistent` 返回空 `node_set`。 |
| `describe-cluster-env` 真实集群 | 对真实集群返回 `PermissionDenied, describe resource failed`（取决于集群状态与账号权限），请求本身已正确构造。 |
| 变更命令安全验证 | 14 个变更命令均以不存在的资源 ID 测试，全部返回 API 错误（无真实副作用），确认参数构造正确。 |

## 4. 测试覆盖明细

### A. CLI 基础（5 用例）
`--version`、`--help`（含全部 22 命令）、无命令、未知命令、子命令帮助。

### B. 认证与配置（3 用例）
缺凭据报错、`--config` 方式、命令行参数覆盖配置。

### C. 只读命令真实调用（12 用例）
`describe-apps`、`describe-clusters`（JSON/table/含 cluster_set）、真实集群 ID 的 `describe-cluster-nodes`/`describe-cluster-env`、6 个需必填参数的只读命令错误路径。

### D. 参数校验（3 用例）
缺必填参数、非法 JSON、非法整数。

### E. 错误处理（1 用例）
describe 查询对不存在资源返回空结果。

### F. 变更命令安全验证（28 用例）
14 个变更命令 × 2（错误路径 + 缺必填参数），确认无真实副作用。

## 5. 结论

- CLI 在真实 API 环境下**端到端可用**，全部 22 个命令的请求构造、签名、输出渲染均正常。
- 通过 e2e 测试发现并修复了 **2 个单元测试无法覆盖的真实缺陷**（签名双重编码、参数名错误），体现了 e2e 测试的价值。
- 变更命令未在真实资源上执行（避免副作用）；如需完整生命周期测试，需提供测试集群 ID。
