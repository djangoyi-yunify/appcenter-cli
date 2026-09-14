# appcenter-cli

青云 AppCenter 命令行工具，专为 AI Agent 设计。

青云官方 CLI 工具不包含 AppCenter 相关功能，本工具基于青云 API 文档
（https://docsv4.qingcloud.com/user_guide/development_docs/api/）实现，
覆盖 AppCenter 云应用的核心常用动作，方便 AI Agent 通过命令行管理
AppCenter 集群、应用、节点、监控等资源。

## 安装

### 方式一：uv tool（推荐）

使用 [uv](https://docs.astral.sh/uv/) 将 `appcenter` 作为全局工具安装（类似 pipx，自动隔离环境、管理可执行文件）：

```bash
uv tool install git+https://github.com/djangoyi-yunify/appcenter-cli.git
```

安装后 `appcenter` 命令即可全局使用：

```bash
appcenter --version
```

> 提示：某些 AI agent 环境可能会因为安全原因限制对系统目录（如 `~/.local/share/uv`）的写入，导致 `uv tool install` 报权限错误。此时可通过 `UV_TOOL_DIR` / `UV_TOOL_BIN_DIR` 指定可写目录，例如：
>
> ```bash
> UV_TOOL_DIR=/tmp/uv-tools UV_TOOL_BIN_DIR=/tmp/uv-bin \
>   uv tool install git+https://github.com/djangoyi-yunify/appcenter-cli.git
> export PATH="/tmp/uv-bin:$PATH"
> ```

### 方式二：pip 从 Git 仓库安装

```bash
# HTTPS（仓库公开时）
pip install git+https://github.com/djangoyi-yunify/appcenter-cli.git

# SSH
pip install git+ssh://git@github.com/djangoyi-yunify/appcenter-cli.git
```

### 方式三：本地开发安装

```bash
pip install -e .
```

## 卸载

按安装方式对应卸载：

```bash
# 方式一：uv tool 安装
uv tool uninstall appcenter-cli

# 方式二 / 方式三：pip 安装
pip uninstall appcenter-cli
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

## 开发

```bash
uv venv .venv
uv pip install -e . pytest
.venv/bin/python -m pytest
```

## 参考

- 青云 API 文档：https://docsv4.qingcloud.com/user_guide/development_docs/api/
- 青云 Python SDK：https://github.com/yunify/qingcloud-sdk-python
