# AppCenter CLI E2E 测试报告：版本升级（真实 API）

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| 测试应用 | `app-zydumbxo`（Redis Standalone），owner `usr-hRAmdSn6` |
| 测试类型 | 创建/升级/删除真实集群（多可用区，最小费用），测试结束已清理 |
| CLI 扩展 | 新增 `upgrade-clusters` 命令（`UPGRADE_CLUSTERS` action），含单元测试 |
| 测试结果 | **规则 1、规则 2 全部通过；规则 3 部分通过**（开发中版本可升级，下架版本不可升级） |

## 2. 测试结果明细

| ID | 用例 | 结果 |
| --- | --- | --- |
| U-01 | 普通模式 5.0.11 → 7.2.14（已上架） | ✅ 升级成功，`cl-enkt8ajm`，`ret_code=0`，收敛后 `app_version=appv-tvzeju2i` |
| U-02 | 普通模式 5.0.11 → 7.2.11（已下架） | ✅ 预期失败，`ret_code=1400 PermissionDenied` |
| U-03 | 普通模式 5.0.11 → 7.0.4（开发中 `appv-e3jvzled`） | ✅ 预期失败，`ret_code=1400 PermissionDenied` |
| U-04 | 调试模式 7.2.7 → 7.2.14（已上架） | ✅ 升级成功，`cl-pw9vqqkp`，`ret_code=0`，收敛后 `app_version=appv-tvzeju2i` |
| U-05 | 调试模式 7.2.7 → 7.2.11（已下架） | ❌ **未达预期**：`ret_code=1400 PermissionDenied`（规则 3 预期成功） |
| U-06 | 调试模式 5.0.11 → 7.0.4（开发中 `appv-e3jvzled`） | ❌ **未达预期**：`ret_code=1400 PermissionDenied`（目标不在 `upgrade_policy`） |
| U-06b | 调试模式 5.0.11（已停止）→ 7.0.4（开发中 `appv-p17zoert`） | ✅ 升级成功，`cl-qiyqjdp2`，`ret_code=0`，`app_version=appv-p17zoert` |
| U-07/U-08 | 清理删除 | ✅ 6 个测试集群全部收敛 `deleted` |

> 说明：
> - U-05/U-06 未达预期，触发补充验证 U-06b（改用 `upgrade_policy` 中实际存在的开发中版本 `appv-p17zoert`，并先停止集群），升级成功。
> - 预期失败用例（U-02/U-03）如实记录，不视为 CLI 缺陷。

## 3. 测试发现

### 发现 1：规则 1 成立——`upgrade_policy` 配置字段决定可升级来源

- 每个版本的 `cluster.json.mustache` 中均有 `upgrade_policy` 数组，列出可升级到该版本的低版本 ID。
- 已逐一验证：`appv-tvzeju2i`（7.2.14）含 `r89epe6m`、`2mer62ui` 等；`appv-kxvo77jc`（7.2.11）含 `r89epe6m`、`2mer62ui` 等；`appv-2mer62ui`（7.2.7）含 `r89epe6m` 等。
- 集群的 `describe-clusters` 返回 `app_version_info.upgrade_policy`，即该集群当前版本**实际可升级的目标列表**（含状态），是升级可行性的权威依据。

### 发现 2：规则 2 成立——普通模式只能升级到已上架版本

- U-01：普通模式 5.0.11 → 7.2.14（已上架）→ **成功**。
- U-02：普通模式 5.0.11 → 7.2.11（已下架）→ **失败**，`PermissionDenied`。
- U-03：普通模式 5.0.11 → 7.0.4（开发中）→ **失败**，`PermissionDenied`。
- **结论**：普通模式集群只能升级到已上架版本，下架/开发中版本均被拒绝。

### 发现 3：规则 3 部分成立——调试模式可升级到**开发中**版本（重要发现）

- U-04：调试模式 7.2.7 → 7.2.14（已上架）→ **成功**。
- U-06b：调试模式 5.0.11（已停止）→ 7.0.4（开发中 `appv-p17zoert`）→ **成功**，`app_version` 收敛为 `appv-p17zoert`。
- 对比普通/调试模式集群的 `upgrade_policy`：
  - 普通模式 5.0.11：仅 `tvzeju2i`、`pbn7ic5e`（均 released）。
  - 调试模式 5.0.11：`tvzeju2i`、`pbn7ic5e` + **`p17zoert`（7.0.4，dev，draft）**。
- **结论**：调试模式会把开发中版本加入 `upgrade_policy`，从而允许升级到开发中版本；普通模式不显示开发中版本。

### 发现 4：规则 3 不成立——调试模式**不能**升级到已下架版本

- U-05：调试模式 7.2.7 → 7.2.11（已下架 `appv-kxvo77jc`）→ **失败**，`PermissionDenied`。
- 即使先停止集群再升级，仍失败（`PermissionDenied`）。
- 调试模式 7.2.7 集群的 `upgrade_policy` 仅含 `tvzeju2i`、`pbn7ic5e`（均 released），**不含下架版本**。
- 5.0.11 集群的 `upgrade_policy` 同样不含任何下架版本（6.2.5、7.2.5、7.2.7 等均未出现）。
- **结论**：下架版本被排除在 `upgrade_policy` 之外，即使调试模式集群也无法升级到已下架版本。规则 3 中"无论高版本是否下架"的表述**不成立**。

### 发现 5：开发中版本升级需**先停止集群**

- 对运行中的集群升级到开发中版本 `appv-p17zoert`，返回 `ret_code=1400 PermissionDenied, only stopped resource can be upgraded`。
- 先执行 `stop-clusters` 使集群收敛 `stopped` 后，再升级到开发中版本 → **成功**。
- 已上架版本升级（U-01/U-04）无需停止集群，运行中即可升级。
- **结论**：升级到开发中版本要求集群处于停止状态。

### 发现 6：`appv-e3jvzled` 不在 5.0.11 的 `upgrade_policy` 中，正确开发中版本为 `appv-p17zoert`

- 计划中 U-06 使用 `appv-e3jvzled`（用户提供，配置同 `appv-vmg56wlp`），但 5.0.11 集群的 `upgrade_policy` **不含** `appv-e3jvzled`，升级返回 `PermissionDenied`。
- 5.0.11 集群的 `upgrade_policy` 中实际存在的开发中版本为 **`appv-p17zoert`（7.0.4，dev，draft）**。
- 改用 `appv-p17zoert` 后升级成功（U-06b）。
- **结论**：`appv-e3jvzled` 虽可部署（调试模式），但未挂接升级路径；开发中版本升级需以目标版本实际出现在低版本集群的 `upgrade_policy` 为准。

### 发现 7：升级需集群**健康**（`health_status=healthy`）

- 集群收敛 `active` 后立即升级，可能返回 `ret_code=1400 PermissionDenied, only healthy cluster can be upgraded`。
- 需等待 `describe-clusters --verbose 1` 的 `health_status` 变为 `healthy` 后再升级。
- 本测试 6 个集群均等待至 `healthy` 后执行升级。

## 4. CLI 扩展

- `appcenter_cli/actions.py` 新增 `UPGRADE_CLUSTERS` action：
  - `app_version`（str，必填）：目标版本 ID；
  - `clusters`（list，必填）：集群 ID 数组。
- 注册命令 `upgrade-clusters`，返回 `job_id`、`cluster_ids`。
- `tests/test_cli.py` 新增 2 个单元测试（参数定义、参数收集），全部 81 个测试通过。
- 提交：`11f5d24 feat(actions): 新增 upgrade-clusters 命令`。

## 5. 结论

- **规则 1（`upgrade_policy` 配置字段）成立**。
- **规则 2（普通模式只能升级到已上架版本）成立**。
- **规则 3（调试模式可升级到任何符合规则 1 的高版本）部分成立**：
  - ✅ 调试模式可升级到**开发中**版本（需先停止集群）；
  - ❌ 调试模式**不能**升级到**已下架**版本（下架版本不在 `upgrade_policy` 中）。
- 开发中版本升级需先停止集群；已上架版本升级无需停止。
- 升级前需等待集群 `health_status=healthy`。
- 测试集群已全部删除清理，无残留资源。
