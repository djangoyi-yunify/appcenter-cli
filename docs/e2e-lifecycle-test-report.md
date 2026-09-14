# AppCenter CLI E2E 测试报告：集群生命周期管理（真实 API）

## 1. 执行摘要

| 项 | 结果 |
| --- | --- |
| 测试日期 | 2026-09-11 |
| 测试环境 | 真实青云 API（`api.qingcloud.com`），`--config .qingcloud/config` |
| 测试应用 | Redis Standalone（`app-zydumbxo` / `appv-tvzeju2i`） |
| 部署模式 | 多可用区（region `pek3`，zones `pek3b`/`pek3d`）+ 单可用区（zone `pek3b`） |
| 测试集群 | 多可用区 `cl-5sel9a77`、单可用区 `cl-huvno0tu`、垂直扩容 `cl-heyz3n8j`、磁盘扩容 `cl-p7cykhno`（均已删除清理） |
| 生命周期阶段 | 创建、垂直扩容、水平扩容、修改配置、关闭/启动、删除 **全部通过** |
| 垂直扩容 | ✅ `resize-cluster --node-role ""`，cpu 1→2、memory 1024→2048、磁盘 10G→20G |

## 2. 测试环境

| 项 | 值 |
| --- | --- |
| CLI 可执行文件 | `.venv/bin/appcenter`（版本 0.1.0） |
| 配置方式 | `--config .qingcloud/config` |
| 应用 / 版本 | `app-zydumbxo` / `appv-tvzeju2i` |
| 多可用区网络 | `vxnet-kldf8dk`（VPC `rtr-52tkfywg`） |
| 单可用区网络 | `vxnet-mn82b92`（VPC `rtr-52tkfywg`） |
| 最小规格 | `instance_class=101/202`、`cpu=1`、`memory=1024`、`volume_size=10`、`count=1` |

## 3. 测试结果明细

### G. 创建集群（多可用区）✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| G-01 | 部署最小规格集群（多可用区） | ✅ `cl-5sel9a77`，`ret_code=0` |
| G-02 | 等待集群 active | ✅ 约 1 分钟收敛 `active` |
| G-03 | 验证最小规格 | ✅ `cpu=1`、`mem=1024`、`storage=10`、`node_count=1` |

### H. 垂直扩容 ✅

> 首次尝试 `resize-cluster --cluster cl-5sel9a77 --cpu 2`（不带 `--node-role`）返回 `InternalError`（5000），误判为应用不支持。经查 API 文档确认支持后，用新集群 `cl-heyz3n8j` 补测，**显式传 `--node-role ""` 后成功**。

| ID | 用例 | 结果 |
| --- | --- | --- |
| H-01 | 扩容 CPU | ✅ `resize-cluster --node-role "" --cpu 2`，`ret_code=0`，resize_info `cpu=2` |
| H-02 | 等待任务完成 | ✅ job `successful`（约 3 分钟） |
| H-03 | 验证 CPU | ✅ `cpu_asgn=2` |
| H-04 | 扩容内存 | ✅ `resize-cluster --node-role "" --memory 2048`，`ret_code=0`，resize_info `memory=2048` |
| H-05 | 等待任务完成 | ✅ job `successful`（约 3 分钟） |
| H-06 | 验证内存 | ✅ `mem_asgn=2048` |
| H-07 | 扩容磁盘 | ✅ `resize-cluster --node-role "" --storage-size 20`（`cl-p7cykhno`），`ret_code=0`，resize_info `storage_size=20` |
| H-08 | 等待任务完成 | ✅ job `successful`（约 1 分钟） |
| H-09 | 验证磁盘 | ✅ `storage_asgn=20`（10G→20G） |

### I. 水平扩容 ✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| I-01 | 增加节点 | ✅ `add-cluster-nodes --node-count 2 --node-role ""`，`ret_code=0` |
| I-02 | 等待任务完成 | ✅ job `successful`（约 3 分钟） |
| I-03 | 验证节点数 | ✅ `node_count=3`（奇数） |
| I-04 | 获取节点 ID | ✅ 新增 `cln-9rssjxix`、`cln-r9ootbt3` |
| I-05 | 删除新增节点 | ✅ `delete-cluster-nodes` 删除 2 个节点，`ret_code=0` |
| I-06 | 等待任务完成 | ✅ job `successful`（约 2 分钟） |
| I-07 | 验证节点数 | ✅ `node_count=1`（奇数） |

### J. 修改配置 ✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| J-01 | 修改环境变量 | ✅ `update-cluster-env --env '{"maxmemory-policy":"allkeys-lru"}'`，`ret_code=0` |
| J-02 | 等待任务完成 | ✅ job `successful` |
| J-03 | 验证配置生效 | ✅ `describe-cluster-env` 显示 `maxmemory-policy=allkeys-lru` |

### K. 关闭/启动 ✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| K-01 | 停止集群 | ✅ `stop-clusters`，`ret_code=0` |
| K-02 | 等待停止完成 | ✅ 约 2 分钟收敛 `stopped` |
| K-03 | 启动集群 | ✅ `start-clusters`，`ret_code=0` |
| K-04 | 等待启动完成 | ✅ 约 2 分钟收敛 `active` |

### L. 删除集群（清理）✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| L-01 | 删除测试集群 | ✅ `delete-clusters`，`ret_code=0` |
| L-02 | 等待删除完成 | ✅ 约 2 分钟收敛 `deleted` |

### M. 单可用区部署（附加验证）✅

| ID | 用例 | 结果 |
| --- | --- | --- |
| M-01 | 部署单可用区集群 | ✅ `cl-huvno0tu`（zone `pek3b`，vxnet `vxnet-mn82b92`），`ret_code=0` |
| M-02 | 等待集群 active | ✅ 约 2 分钟收敛 `active` |
| M-03 | 验证最小规格 | ✅ `cpu=1`、`mem=1024`、`storage=10`、`node_count=1`、`zone_id=pek3b` |
| M-04 | 删除单可用区集群 | ✅ `delete-clusters`，`ret_code=0` |
| M-05 | 等待删除完成 | ✅ 收敛 `deleted` |

## 4. 测试发现

### 发现 1：`resize-cluster` 与 `add-cluster-nodes` 均需显式传 `--node-role ""`

- 不带 `--node-role` 时，`resize-cluster` 与 `add-cluster-nodes` 均返回 `InternalError`（5000）
- 显式传 `--node-role ""`（空字符串角色）后均成功
- **结论**：CLI 参数构造正确；单角色应用需显式指定空角色，属 API 行为。首次误判为"应用不支持垂直扩容"，经查 API 文档确认支持后补测通过

### 发现 2：CLI `resize-cluster` 参数名与 SDK 不一致（已修复）

- CLI 参数：`--storage`、`--gpu`；SDK/API 参数：`storage_size`、`instance_class`
- `--storage` 应为 `--storage_size` 才能正确映射到 API；`--gpu` 为 API 未定义参数
- **修复**：提交 `89c9091` 将 `storage` 改为 `storage_size`，补充 `instance_class`
- **验证**：磁盘扩容测试 `--storage-size 20` 成功（resize_info `storage_size=20`），确认修复生效

### 发现 3：测试计划 I-05 修正

- 原计划"删除 1 个节点从 3 回到 1"有误（3-1=2）
- 修正为删除 **2 个新增节点**（3→1），已同步更新测试计划文档

### 发现 4：版本区域匹配

- 原定版本 `appv-c11mwclr` 可用区域为 `pekt3d,pekt3`（`pekt3` 区域），与 vxnet 所在 `pek3` 区域不匹配，部署返回 `PermissionDenied`
- 改用 `appv-tvzeju2i`（`pek3` 区域可用）后部署成功
- **结论**：部署前需确认版本可用区域与 vxnet 区域一致

### 发现 5：`global_uuid` 为可选参数（已实证）

- 真实控制台请求的 conf 中携带 `global_uuid`（随机小数，用于区分同名集群）
- **实证**：创建不带 `global_uuid` 的集群（`cl-dgpc9w07`）部署成功并收敛 `active`，确认该字段**可选**
- **结论**：测试计划 conf 模板已移除 `global_uuid`，避免所有集群使用相同值（如 `0.123456789`）带来的潜在冲突

## 5. 结论

- CLI 的集群生命周期管理在真实 API 环境下**端到端可用**：创建（多/单可用区）、垂直扩容、水平扩容、修改配置、关闭/启动、删除均正常。
- 通过真实测试发现：**单角色应用需显式传空 `node_role`**（`resize-cluster` 与 `add-cluster-nodes` 均如此）；**CLI `resize-cluster` 的 `--storage`/`--gpu` 参数名与 API 不一致**（已修复）；**`global_uuid` 为可选参数**（已实证并移除）。
- 测试集群已全部删除清理，无残留资源。
- 为支持多可用区部署，CLI 新增 `--multi-deploy-zones` 参数（提交 `b79dcad`），单元测试 19 个全部通过。
