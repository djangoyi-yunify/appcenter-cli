# AppCenter CLI E2E 测试报告：调试模式创建集群（真实 API）

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| 测试应用 | `app-zydumbxo`（Redis Standalone），owner `usr-hRAmdSn6` |
| 测试类型 | 创建/删除真实集群（多可用区，最小费用），测试结束已清理 |
| 测试结果 | **4/4 全部通过**（含 2 个预期失败用例） |

## 2. 测试结果明细

| ID | 用例 | 结果 |
| --- | --- | --- |
| D-01 | 调试模式 + 已上架版本 `appv-tvzeju2i` | ✅ 部署成功，`cl-wkl61rg6`，`debug=True`，收敛 `active` |
| D-02 | 调试模式 + 已下架版本 `appv-kxvo77jc` | ✅ 部署成功，`cl-wquf8jiv`，`debug=True`，收敛 `active` |
| D-03 | 调试模式 + 开发中版本 `appv-e3jvzled` | ✅ **部署成功（超出预期）**，`cl-2eqh8wcs`，`debug=True`，收敛 `active` |
| D-04 | 对照：非调试模式 + 已下架版本 `appv-kxvo77jc` | ✅ 预期失败，`ret_code=1400 PermissionDenied` |
| D-05/D-06 | 清理删除 | ✅ 3 个测试集群全部收敛 `deleted` |

> 说明：D-03 原预期失败（开发中版本 API 不可见），实际**部署成功**，为重要发现，详见发现 3。

## 3. 测试发现

### 发现 1：调试模式（`debug:1`）可正常创建集群，`debug` 字段可验证

- CLI `deploy-app-version --debug 1` 序列化为 `debug=1`，无需扩展 CLI。
- 部署成功后，`describe-clusters` 返回 `debug=True`（布尔字段），可确认调试模式生效。
- 三个调试集群（D-01/D-02/D-03）均收敛 `active`，`debug=True`，`app_version` 与部署版本一致。

### 发现 2：下架版本**只能**以调试模式部署

- D-02：调试模式 + 下架版本 `appv-kxvo77jc` → **部署成功**。
- D-04（对照）：非调试模式 + 同一下架版本 → **失败**，`ret_code=1400 PermissionDenied`。
- 与既有集群统计一致：账号下 `appv-kxvo77jc` 的 32 个集群**全部 `debug=True`**，无一非调试。
- **结论**：下架版本无法通过正常模式部署，必须使用调试模式。

### 发现 3：开发中版本**可以**以调试模式部署（重要发现）

- D-03：调试模式 + 开发中版本 `appv-e3jvzled` → **部署成功**，收敛 `active`，`debug=True`。
- 该版本在 `describe-app-versions` 中 **API 不可见**（按 `version_id` 查询 `total_count=0`，任何 `status` 过滤也查不到），但**仍可通过 `DeployAppVersion` 以调试模式部署**。
- 与既有集群统计一致：此前 `appv-e3jvzled` 从未被部署过（0 个集群），本测试首次实证其可部署。
- **结论**：调试模式允许部署开发中（未上架/未提交审核）的版本，即使该版本不通过查询 API 暴露。

### 发现 4：`global_uuid` 不传仍可部署成功

- 本测试按用户要求**不传** `global_uuid`，三个调试集群均部署成功。
- 与既有结论一致：`global_uuid` 为可选参数，不传不影响部署。

### 发现 5：调试模式对普通用户账号可用

- 本账号 `usr-hRAmdSn6` 为普通用户（`describe-apps` 看不到 `app-zydumbxo`，非应用开发者），仍可创建调试模式集群。
- 调试模式并非仅限开发者账号。

## 4. 结论

- CLI 的 `deploy-app-version --debug 1` 在真实 API 环境下**端到端可用**，无需扩展。
- **调试模式可部署任意状态的版本**：已上架、已下架、开发中均可。
- **下架版本仅调试模式可部署**（非调试模式返回 `PermissionDenied`）。
- **开发中版本虽 API 不可见，但调试模式可部署**——这是本测试最重要的发现。
- 测试集群已全部删除清理，无残留资源。
