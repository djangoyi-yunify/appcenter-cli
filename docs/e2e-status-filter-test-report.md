# AppCenter CLI E2E 测试报告：describe-app-versions --status 过滤参数（真实 API）

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| 测试应用 | `app-y6i338bf`（active 8 个 + suspended 15 个 = 23 个版本） |
| 测试类型 | **只读**（`describe-*`），无资源创建、无费用 |
| 测试结果 | **7/7 全部通过** |

## 2. 测试结果明细

| ID | 用例 | 结果 |
| --- | --- | --- |
| S-01 | 默认查询（不带 --status） | ✅ `total_count=8`，全部 `status=active` |
| S-02 | 过滤 active | ✅ `total_count=8`，全部 `status=active` |
| S-03 | 过滤 suspended | ✅ `total_count=15`，全部 `status=suspended` |
| S-04 | 多状态组合（active + suspended） | ✅ `total_count=23`，含 active 与 suspended |
| S-05 | 状态一致性（逐版本校验） | ✅ 23 个版本 status 均属于过滤集合 |
| S-06 | 无效状态值（draft） | ✅ 退出码 1，`ret_code=1100`（`InvailidRequestFormat`） |
| S-07 | 分页组合（limit=5, offset=0/5） | ✅ 两页各 5 个，无重复 |

## 3. 测试发现

### 发现 1：`--status` 过滤参数工作正常

- `--status active` / `--status suspended` 单状态过滤准确；
- `--status active --status suspended` 多状态组合返回全部 23 个版本；
- 返回的每个版本 `status` 字段均与过滤条件一致。

### 发现 2：默认行为为只返回 active 版本

- 不带 `--status` 时，API 默认只返回 `active` 版本（8 个），不返回 suspended 版本。
- 需查询下架版本时必须显式传 `--status suspended`。

### 发现 3：无效状态值返回明确错误

- `--status draft` 返回 `ret_code=1100`（`InvailidRequestFormat`），CLI 退出码 1。
- 合法状态值仅 `active`、`suspended`（与 API 文档一致）。

### 发现 4：分页与过滤可组合

- `--status suspended --limit 5 --offset 0/5` 分页正确，两页无重复版本。

## 4. 结论

- CLI 新增的 `--status` 过滤参数在真实 API 环境下**端到端可用**，单状态、多状态、分页组合均正常。
- 该参数为 list 类型，序列化为 `status.1/.2`，与 API 一致（提交 `0985e15`）。
- 本测试为只读，无资源创建、无清理需求。
