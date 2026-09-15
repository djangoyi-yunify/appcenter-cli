# qc-tools

青云（QingCloud）命令行工具集，专为 AI Agent 设计，提供多套 CLI：

- **App Center CLI**（`appcenter`）：管理 AppCenter 集群、应用、节点、监控等资源。
- **IaaS CLI**（`iaas`）：管理青云 IaaS 云资源（计算、存储、网络等），**规划中，尚未实现**。

青云官方 CLI 工具不包含 AppCenter 相关功能，本工具基于青云 API 文档
（https://docsv4.qingcloud.com/user_guide/development_docs/api/）实现，
覆盖 AppCenter 云应用的核心常用动作，方便 AI Agent 通过命令行管理
AppCenter 集群、应用、节点、监控等资源。

## 安装

### 方式一：uv tool（推荐）

使用 [uv](https://docs.astral.sh/uv/) 将 `qc-tools` 作为全局工具安装（类似 pipx，自动隔离环境、管理可执行文件）：

```bash
uv tool install git+https://github.com/djangoyi-yunify/qc-tools.git
```

安装后 `appcenter` 命令即可全局使用：

```bash
appcenter --version
```

> 提示：某些 AI agent 环境可能会因为安全原因限制对系统目录（如 `~/.local/share/uv`）的写入，导致 `uv tool install` 报权限错误。此时可通过 `UV_TOOL_DIR` / `UV_TOOL_BIN_DIR` 指定可写目录，例如：
>
> ```bash
> UV_TOOL_DIR=/tmp/uv-tools UV_TOOL_BIN_DIR=/tmp/uv-bin \
>   uv tool install git+https://github.com/djangoyi-yunify/qc-tools.git
> export PATH="/tmp/uv-bin:$PATH"
> ```

### 方式二：pip 从 Git 仓库安装

```bash
# HTTPS（仓库公开时）
pip install git+https://github.com/djangoyi-yunify/qc-tools.git

# SSH
pip install git+ssh://git@github.com/djangoyi-yunify/qc-tools.git
```

### 方式三：本地开发安装

```bash
pip install -e .
```

## 卸载

按安装方式对应卸载：

```bash
# 方式一：uv tool 安装
uv tool uninstall qc-tools

# 方式二 / 方式三：pip 安装
pip uninstall qc-tools
```

> 提示：卸载仅移除 `appcenter` 命令与 Python 包，**不会删除**认证配置文件（`~/.qingcloud/config`）及其中保存的凭据。如需彻底清理，请手动删除该配置文件。

## 认证配置

凭据按以下优先级解析（高到低）：

1. 命令行参数（`--access-key-id`、`--secret-access-key`、`--zone`、`--host`）
2. 环境变量
3. 配置文件 `~/.qingcloud/config`（可用 `QINGCLOUD_CONFIG` 指定路径）

### 环境变量

| 变量 | 说明 |
| --- | --- |
| `QINGCLOUD_ACCESS_KEY_ID` | API 密钥 ID |
| `QINGCLOUD_SECRET_ACCESS_KEY` | API 密钥 Secret |
| `QINGCLOUD_ZONE` | 区域 ID，如 `pek3a` |
| `QINGCLOUD_HOST` | API 地址，默认 `api.qingcloud.com` |
| `QINGCLOUD_CONFIG` | 配置文件路径 |

### 配置文件

配置文件是**可选的**：凭据也可通过命令行参数或环境变量提供（见上文优先级）。仅当未通过命令行参数或环境变量提供凭据时，才会读取配置文件。

- **默认存放位置**：`~/.qingcloud/config`
- **自定义位置**：可将配置文件放在其他路径，并通过环境变量 `QINGCLOUD_CONFIG` 指定，例如：

```bash
export QINGCLOUD_CONFIG=/path/to/my-qingcloud-config
```

配置文件格式（INI）：

```ini
[default]
access_key_id = YOUR_ACCESS_KEY_ID
secret_access_key = YOUR_SECRET_ACCESS_KEY
zone = pek3a
host = api.qingcloud.com
```

## 使用

```bash
# 查看所有命令
appcenter --help

# 查看某个命令的参数
appcenter describe-clusters --help

# 查看某个命令的详细用法与注意事项（示例、约束、注意事项）
appcenter wiki describe-clusters

# 列出集群（JSON 输出，默认）
appcenter describe-clusters

# 列出集群（表格输出，便于人类阅读）
appcenter describe-clusters --output table

# 按 ID 过滤
appcenter describe-clusters --clusters cl-xxxx --clusters cl-yyyy

# 部署应用版本
appcenter deploy-app-version --version-id appv-xxxx '--conf={"name":"demo","vxnet":"vxnet-0"}'

# 启动/停止/删除集群
appcenter start-clusters --clusters cl-xxxx
appcenter stop-clusters --clusters cl-xxxx
appcenter delete-clusters --clusters cl-xxxx

# 查看集群节点
appcenter describe-cluster-nodes --cluster cl-xxxx

# 获取集群监控数据
appcenter get-cluster-monitor --resource cln-xxxx --step 5m \
  --start-time 2026-09-10T00:00:00Z --end-time 2026-09-10T01:00:00Z \
  --meters cpu --meters memory
```

### 面向 AI Agent 的辅助参数

所有子命令均支持以下参数，便于 AI Agent 调试与安全演练：

```bash
# 预览将发送的请求而不真正执行（适合删除/销毁等破坏性操作前演练）
appcenter delete-clusters --clusters cl-xxxx --dry-run

# 打印实际发送的 HTTP 请求（签名已隐藏，不泄露密钥）
appcenter describe-clusters --trace

# 两者可组合：打印请求但不发送
appcenter upgrade-clusters --app-version appv-xxxx --clusters cl-xxxx --trace --dry-run
```

- `--dry-run`：构建并打印完整请求 URL，不发送，退出码 0。
- `--trace`：将请求 URL 打印到 stderr（`signature` 值以 `***` 隐藏），随后正常发送。

### wiki 子命令

`appcenter wiki` 是本地帮助命令（不访问 API），展示各子命令的详细用法：

```bash
# 列出所有命令及说明
appcenter wiki

# 查看某个命令的详细用法：参数、约束、示例、注意事项
appcenter wiki describe-clusters
```

## 支持的命令

| 命令 | API 动作 | 说明 |
| --- | --- | --- |
| `describe-apps` | DescribeApps | 获取应用信息 |
| `describe-app-versions` | DescribeAppVersions | 获取应用版本信息 |
| `describe-app-version-attachments` | DescribeAppVersionAttachments | 获取应用版本配置文件 |
| `deploy-app-version` | DeployAppVersion | 部署应用版本（创建集群） |
| `describe-clusters` | DescribeClusters | 获取集群信息 |
| `describe-cluster-nodes` | DescribeClusterNodes | 获取集群节点信息 |
| `describe-cluster-jobs` | DescribeClusterJobs | 获取集群操作日志 |
| `describe-cluster-env` | DescribeClusterEnvironment | 获取集群环境变量 |
| `describe-cluster-display-tabs` | DescribeClusterDisplayTabs | 获取集群 display tabs |
| `start-clusters` | StartClusters | 启动集群 |
| `stop-clusters` | StopClusters | 停止集群 |
| `restart-cluster-service` | RestartClusterService | 重启集群服务 |
| `delete-clusters` | DeleteClusters | 删除集群 |
| `cease-clusters` | CeaseClusters | 销毁集群 |
| `recover-clusters` | RecoverClusters | 恢复集群 |
| `resize-cluster` | ResizeCluster | 调整集群节点规格 |
| `change-cluster-vxnet` | ChangeClusterVxnet | 切换集群私网 |
| `update-cluster-env` | UpdateClusterEnvironment | 更新集群环境变量 |
| `add-cluster-nodes` | AddClusterNodes | 增加集群节点 |
| `delete-cluster-nodes` | DeleteClusterNodes | 删除集群节点 |
| `associate-eip-to-cluster-node` | AssociateEipToClusterNode | 绑定公网 IP 到节点 |
| `dissociate-eip-from-cluster-node` | DissociateEipFromClusterNode | 解绑节点公网 IP |
| `get-cluster-monitor` | GetClusterMonitor | 获取集群监控数据 |

> 另有 `wiki` 子命令（非 API 动作），用于查看各命令的详细用法与注意事项，见上文「wiki 子命令」。

## 尚未实现的 API 动作

以下 AppCenter 相关 API 动作尚未实现，后续按需增加。

### SaaS 应用 - SSO API

参考：https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/appcenter/saas/account_api/

| API 动作 | 说明 |
| --- | --- |
| 获取授权码 | OAuth 2.0 授权码模式，`GET /sso/oauth2/` |
| 获取 ACCESS_TOKEN | `POST /sso/token/` |
| 校验 ACCESS_TOKEN | `POST /sso/check_token/` |
| 更新 ACCESS_TOKEN | `POST /sso/refresh_token/` |

### SaaS 应用 - 用户计费 API

参考：https://docsv4.qingcloud.com/user_guide/development_docs/api/api_list/appcenter/saas/new_billing_api/

| API 动作 | 说明 |
| --- | --- |
| NBCreatePrdOrder | 创建 Package 订单 |
| NBCancelPrdOrder | 取消订单 |
| NBChargePrdOrder | 支付 Package 订单 |
| NBRenewProdInstance | 续订产品实例 |
| NBStopProdInstance | 停止产品实例计费 |
| NBChangeProdInstanceConfig | 修改产品实例配置 |

## 输出格式

- 默认输出格式化 JSON，便于 AI Agent 解析。
- 使用 `--output table` 输出对齐表格，便于人类阅读。
- 错误信息统一输出到 stderr（stdout 保持干净，便于机器解析），并区分退出码：
  - `0`：成功
  - `1`：API 错误（含 `ret_code` 与 `message`）
  - `2`：参数或配置错误（如缺少必填参数、JSON 格式错误、缺少凭据）
- 参数错误会指明具体参数名（如 `invalid input for --conf: ...`），并附带 usage 行，便于 AI Agent 自我纠正。

## 开发与测试

### 环境搭建

```bash
uv venv .venv
uv pip install -e ".[dev]"
```

> `.[dev]` 安装项目及 `pyproject.toml` 中声明的开发依赖（pytest）。

### 运行测试

```bash
.venv/bin/python -m pytest
```

常用变体：

```bash
# 运行单个测试文件
uv run pytest tests/test_cli.py

# 运行单个用例
uv run pytest tests/test_cli.py::test_xxx
```

测试类型：

- `tests/` 下为**离线单元测试**（不访问真实 API）。
- `tests/e2e/` 为**真实 API 端到端测试**，需要 `.qingcloud/config` 凭据，缺失时自动跳过。

### 构建发行包

```bash
uv build
```

生成 `dist/` 下的 sdist 与 wheel。

## 参考

- 青云 API 文档：https://docsv4.qingcloud.com/user_guide/development_docs/api/
- 青云 Python SDK：https://github.com/yunify/qingcloud-sdk-python
