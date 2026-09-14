# AppCenter CLI E2E 测试报告：describe-app-versions --status 过滤参数（真实 API）

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| 测试应用 | `app-y6i338bf`（active 8 个 + suspended 15 个 = 23 个版本） |
| 测试类型 | **只读**（`describe-*`），无资源创建、无费用 |
| 测试结果 | **9/9 全部通过** |

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
| S-08 | suspended 版本按 version_id 查询 | ✅ `total_count=0`（suspended 版本无法按 version_id 定位） |
| S-09 | 开发中版本查询（appv-p17zoert） | ✅ `total_count=0`（开发中版本 API 不可见） |

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

### 发现 5：`status` 字段是唯一的状态指示字段

- 版本信息中**只有 `status` 字段**表示版本状态：`active`（上架）、`suspended`（已下架）。
- `status_time` 记录状态变更时间（辅助字段）。
- 其他字段（`visibility`、`console_id` 等）在 API 响应中均为 `None` 或不存在，**不表示状态**。
- **"开发中"状态无对应字段**：开发中版本（如 `appv-p17zoert`）**不通过 API 暴露**，仅在 Web 控制台（应用开发平台）可见；按 `version_id` 查询返回 0，任何 `status` 过滤也查不到。

### 发现 6：suspended 版本无法按 version_id 直接查询

跨两个应用验证，规律一致：

| 应用 | active 版本 | 按 version_id 可查 | suspended 版本 | 按 version_id 可查 |
| --- | --- | --- | --- | --- |
| `app-zydumbxo` | 8 | ✅ 8/8 | 24 | ❌ 0/24 |
| `app-y6i338bf` | 8 | ✅ 8/8 | 15 | ❌ 0/15 |

- **active 版本**：可按 `version_id` 直接查询。
- **suspended 版本**：**只能**通过 `app_ids + status=suspended` 过滤查到，直接按 `version_id` 查询返回 0（即使组合 `app_ids + version_ids` 也查不到）。
- **结论**：查询下架版本必须使用 `--status suspended` 过滤，无法通过 `--version-ids` 定位。

## 4. 结论

- CLI 新增的 `--status` 过滤参数在真实 API 环境下**端到端可用**，单状态、多状态、分页组合均正常。
- 该参数为 list 类型，序列化为 `status.1/.2`，与 API 一致（提交 `0985e15`）。
- **`status` 是唯一状态指示字段**；"开发中"版本 API 不可见；**suspended 版本只能通过 `--status suspended` 过滤查询**，无法按 `version_id` 定位。
- 本测试为只读，无资源创建、无清理需求。
