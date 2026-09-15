# AppCenter CLI E2E 测试计划（真实 API）

## 1. 概述

### 1.1 目标

对 `appcenter-cli`（青云 AppCenter 命令行工具）进行端到端（E2E）测试，**使用真实青云 API**，验证从**命令行入口 → 参数解析 → 配置加载 → 请求签名 → HTTP 请求 → 响应解析 → 输出渲染**的完整链路在真实环境下按预期工作。

### 1.2 范围

- 覆盖全部 22 个命令的入口、参数解析与请求构造
- 覆盖认证配置（`--config` 方式，凭据来自项目内 `.qingcloud/config`）
- 覆盖 JSON 与 table 两种输出格式
- 覆盖参数校验与错误处理（缺参、非法输入、真实 API 错误）
- 覆盖请求签名正确性（真实 API 验签，签名错误会返回认证失败）

### 1.3 方法

- 以子进程方式运行真实 CLI 可执行文件（`.venv/bin/appcenter`）
- 通过 `--config .qingcloud/config` 提供真实凭据
- 只读命令（`describe-*`）直接调用真实 API 并验证响应
- 变更命令（deploy/delete/start/stop 等）**不实际执行**，仅验证参数校验与错误处理路径（使用不存在的资源 ID，确保无真实副作用）
- 断言进程退出码、stdout、stderr 及响应结构

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| Python | 3.12（项目 venv） |
| 测试框架 | pytest 9.1.1 |
| 配置方式 | `--config .qingcloud/config`（真实凭据，已 git 排除） |
| 凭据来源 | `~/.config/agent-commons/.env`（由用户授权写入项目配置） |
| API 地址 | `api.qingcloud.com`（默认） |

## 3. 测试策略

按功能域分组，每组包含若干用例：

| 分组 | 覆盖点 |
| --- | --- |
| A. CLI 基础 | `--version`、`--help`、无命令、未知命令、子命令 `--help` |
| B. 认证与配置 | `--config` 方式、缺凭据报错、参数优先级 |
| C. 只读命令真实调用 | 全部 `describe-*` 命令 + `get-cluster-monitor`，验证真实响应 |
| D. 参数校验 | 缺必填参数、非法 JSON、非法整数 |
| E. 错误处理 | 真实 API 业务错误（不存在的资源 ID）、HTTP 错误 |
| F. 变更命令安全验证 | 变更命令仅验证参数构造与错误路径，不产生真实副作用 |

### 3.1 只读 vs 变更命令

| 类别 | 命令 | 测试方式 |
| --- | --- | --- |
| 只读（安全） | `describe-apps`、`describe-app-versions`、`describe-app-version-attachments`、`describe-clusters`、`describe-cluster-nodes`、`describe-cluster-jobs`、`describe-cluster-env`、`describe-cluster-display-tabs`、`get-cluster-monitor` | 真实调用，验证响应 |
| 变更（不执行） | `deploy-app-version`、`start-clusters`、`stop-clusters`、`restart-cluster-service`、`delete-clusters`、`cease-clusters`、`recover-clusters`、`resize-cluster`、`change-cluster-vxnet`、`update-cluster-env`、`add-cluster-nodes`、`delete-cluster-nodes`、`associate-eip-to-cluster-node`、`dissociate-eip-from-cluster-node` | 仅验证参数校验与错误路径（不存在的资源 ID） |

## 4. 测试用例清单

### A. CLI 基础

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| A-01 | 版本号 | `appcenter --version` | 输出 `appcenter 0.1.0`，退出码 0 |
| A-02 | 帮助信息 | `appcenter --help` | 列出全部 22 个命令，退出码 0 |
| A-03 | 无命令 | `appcenter` | 打印帮助，退出码 0 |
| A-04 | 未知命令 | `appcenter no-such-cmd` | argparse 报错，退出码 2 |
| A-05 | 子命令帮助 | `appcenter describe-clusters --help` | 显示该命令参数，退出码 0 |

### B. 认证与配置

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| B-01 | 缺凭据 | 无 `--config` 且无环境变量运行 | stderr 含 `Missing credentials`，退出码 2 |
| B-02 | `--config` 方式 | `--config .qingcloud/config` 运行 | 请求成功，退出码 0 |
| B-03 | 参数覆盖 | `--config` + 命令行 `--access-key-id` 覆盖 | 使用命令行参数值 |

### C. 只读命令真实调用

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| C-01 | describe-apps | 真实调用 | 退出码 0，stdout 为合法 JSON，`ret_code=0` |
| C-02 | describe-app-versions | 真实调用 | 同上 |
| C-03 | describe-app-version-attachments | 带必填参数（不存在的 ID） | 退出码 0 或 API 业务错误（退出码 1），无崩溃 |
| C-04 | describe-clusters | 真实调用 | 退出码 0，JSON 含 `cluster_set` |
| C-05 | describe-clusters table | `--output table` | 输出对齐表格，含表头 |
| C-06 | describe-cluster-nodes | 带必填参数 | 退出码 0 或 API 业务错误，无崩溃 |
| C-07 | describe-cluster-jobs | 带必填参数 | 同上 |
| C-08 | describe-cluster-env | 带必填参数 | 同上 |
| C-09 | describe-cluster-display-tabs | 带必填参数 | 同上 |
| C-10 | get-cluster-monitor | 带必填参数 | 同上 |
| C-11 | list 参数 | `describe-clusters --clusters <id>` | 请求构造正确，响应正常 |
| C-12 | 公共参数 | 任意请求 | 请求含 action/zone/access_key_id/signature 等（由真实 API 验签） |

### D. 参数校验

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| D-01 | 缺必填参数 | `describe-cluster-nodes`（缺 `--cluster`） | stderr 含 `Missing required parameter`，退出码 2 |
| D-02 | 非法 JSON | `deploy-app-version --conf 'not-json'` | stderr 含 `invalid input`，退出码 2 |
| D-03 | 非法整数 | `describe-apps --limit abc` | stderr 含 `invalid input`，退出码 2 |

### E. 错误处理（真实 API）

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| E-01 | 不存在的资源 | `describe-cluster-nodes --cluster cl-nonexistent` | 退出码 1，stderr 含 API 错误信息 |
| E-02 | 变更命令错误路径 | `start-clusters --clusters cl-nonexistent` | 退出码 1，stderr 含 API 错误信息，无真实副作用 |

### F. 变更命令安全验证

| ID | 用例 | 步骤 | 预期结果 |
| --- | --- | --- | --- |
| F-01 | 变更命令参数构造 | 每个变更命令带必填参数（不存在的 ID） | 请求构造正确，API 返回业务错误（退出码 1），不产生真实变更 |
| F-02 | 变更命令缺参 | 每个变更命令缺必填参数 | 退出码 2，stderr 含 `Missing required parameter` |

## 5. 执行方式

```bash
cd /workspace/qc-tools
.venv/bin/python -m pytest tests/e2e -v
```

## 6. 执行结果

- **2026-09-11 已执行**：54 个 e2e 用例全部通过（含 15 个单元测试共 69 通过）
- 发现并修复 3 个缺陷：签名双重 URL 编码（`client.py`）、`describe-cluster-env` 参数名错误（`actions.py`）、`describe-app-versions` 缺少"至少一个"参数约束（`actions.py` + `cli.py`）
- 详细结果见 [e2e-test-report.md](e2e-test-report.md)

## 7. 风险与限制

- **真实 API 有速率限制**：测试用例应控制调用频率，避免触发限流
- **变更命令不实际执行**：避免对真实云资源产生副作用；如需完整生命周期测试，需用户提供测试集群 ID
- **响应内容依赖账号实际资源**：只读命令的返回数据量取决于账号下真实资源
- **凭据安全**：`.qingcloud/config` 含真实凭据，已加入 `.gitignore` 排除，权限设为 600
