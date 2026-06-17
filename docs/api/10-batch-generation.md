# 批量内容生成 API 文档

**版本**: v1.0  
**更新日期**: 2026-06-17  
**模块**: 批量内容生成（Batch Content Generation）  
**基础路径**: `/api/v1/content-generation`

---

## 1. 模块概述

批量内容生成模块允许用户一次性创建大量内容（最多 500 条/批），通过异步任务并行生成。底层基于 asyncio + Semaphore 实现 10 路并发，单批 100 条内容生成耗时从 25 分钟降至 2.5 分钟（10x 提速）。

**核心特性**：
- 🚀 异步并行生成（10 路并发，Semaphore 控制）
- 📊 实时进度跟踪 + 心跳检测
- 🔄 失败任务重试（retry_count 字段记录）
- 📁 多格式导出（TXT / DOCX / PDF）
- ⏸️ 协作式取消（不影响正在生成的内容）
- 🛡️ 自动清理僵尸任务（5 分钟心跳超时）

---

## 2. 任务生命周期

```
PENDING → RUNNING → COMPLETED
                  → FAILED
                  → CANCELLED (协作式)
                  → PARTIAL (部分成功)
```

**状态说明**:
| 状态 | 含义 |
|---|---|
| `pending` | 任务已创建，等待启动 |
| `running` | 任务运行中，包含已完成/失败计数 |
| `completed` | 全部内容生成成功 |
| `failed` | 任务异常终止 |
| `cancelled` | 用户主动取消（已生成的保留） |
| `partial` | 部分内容成功（部分失败） |

---

## 3. API 端点

### 3.1 创建批量任务

**端点**: `POST /api/v1/content-generation/tasks`

**权限**: 需登录

**请求体**:

```json
{
  "name": "锡盟羊肉产品批量生成",
  "template": "product_intro",
  "template_id": 1,
  "count": 100,
  "config": {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "style": "现代简约",
    "word_count": "200字左右"
  },
  "products": [
    {"product_id": 101, "product_name": "锡盟羊肉"},
    {"product_id": 102, "product_name": "锡盟牛肉"}
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | ✅ | 任务名称 |
| `template` | string | ✅ | 模板类型 (product_intro/live_script/social_post) |
| `template_id` | int | ❌ | 模板 ID（与 template 二选一） |
| `count` | int | ✅ | 生成数量（1-500） |
| `config` | object | ✅ | 生成配置（模型、风格等） |
| `products` | object[] | ❌ | 关联产品列表（用于上下文） |

**响应**:

```json
{
  "task_id": "uuid-xxxx",
  "status": "pending",
  "count": 100,
  "created_at": "2026-06-17T10:30:00"
}
```

---

### 3.2 查询任务列表

**端点**: `GET /api/v1/content-generation/tasks`

**查询参数**:

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `status` | string | null | 筛选状态 |
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页大小 |

**响应**:

```json
{
  "items": [
    {
      "task_id": "uuid-xxxx",
      "name": "锡盟羊肉批量生成",
      "status": "running",
      "progress": {"completed": 65, "total": 100, "failed": 3},
      "retry_count": 0,
      "created_at": "2026-06-17T10:30:00",
      "started_at": "2026-06-17T10:30:05",
      "last_heartbeat_at": "2026-06-17T10:35:20"
    }
  ],
  "total": 12
}
```

---

### 3.3 查询任务详情

**端点**: `GET /api/v1/content-generation/tasks/{task_id}`

**响应**:

```json
{
  "task_id": "uuid-xxxx",
  "name": "锡盟羊肉批量生成",
  "status": "completed",
  "progress": {"completed": 100, "total": 100, "failed": 0},
  "results": [
    {
      "index": 0,
      "content": "...",
      "status": "success",
      "tokens": 580,
      "duration_ms": 2300
    },
    {
      "index": 1,
      "content": null,
      "status": "failed",
      "error": "AI 调用超时"
    }
  ],
  "retry_count": 1,
  "error_message": null,
  "created_at": "2026-06-17T10:30:00",
  "started_at": "2026-06-17T10:30:05",
  "completed_at": "2026-06-17T10:32:35"
}
```

---

### 3.4 取消任务

**端点**: `POST /api/v1/content-generation/tasks/{task_id}/cancel`

**行为**: 协作式取消 —— 标记 `status='cancelled'`，已生成的内容保留在 `results` 中，正在生成的子任务完成后再退出。

**响应**:

```json
{
  "task_id": "uuid-xxxx",
  "status": "cancelled",
  "cancelled_at": "2026-06-17T10:32:00"
}
```

---

### 3.5 重试任务

**端点**: `POST /api/v1/content-generation/tasks/{task_id}/retry`

**适用**: `failed` / `cancelled` / `partial` 状态的任务  
**行为**: 重置 `retry_count += 1`，重新执行失败项；不重复执行已成功项

**响应**:

```json
{
  "task_id": "uuid-xxxx",
  "status": "running",
  "retry_count": 1
}
```

---

### 3.6 单任务导出

**端点**: `GET /api/v1/content-generation/tasks/{task_id}/export/{fmt}`

**格式**: `txt` / `docx` / `pdf`

**响应**: 文件下载（`Content-Disposition: attachment`）

**流式实现**: TXT 格式使用 `StreamingResponse`，每 50 条 yield 一次，避免大文件内存爆炸。

---

### 3.7 批量导出

**端点**: `POST /api/v1/content-generation/tasks/bulk-export`

**请求体**:

```json
{
  "task_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "format": "txt"
}
```

**响应**: ZIP 压缩包下载

---

## 4. 并发与性能

| 指标 | 值 |
|---|---|
| 并发数 | 10 (Semaphore) |
| 单批上限 | 500 条 |
| 单条平均耗时 | 2.5s |
| 单批 100 条总耗时 | ~25s |
| 心跳间隔 | 30s |
| 僵尸任务清理 | 启动时扫描 > 5min 无心跳的 running 任务 |

---

## 5. 配额与计费

- 配额消耗: `count` × 单条成本
- 单条成本 ≈ ¥0.005-0.02（视模型与字数）
- 100 条批量任务 ≈ ¥0.5-2.0

**配额不足处理**:
- 创建任务前预检 `count × unit_cost ≤ user.quota`
- 不足时返回 `402 QUOTA_EXHAUSTED`，提示用户升级套餐

---

## 6. 失败处理与重试

| 错误类型 | 处理策略 |
|---|---|
| AI 调用超时 | 单条重试 3 次，仍失败则该项标记 failed |
| 配额耗尽 | 整个任务标记 failed，回滚已扣减配额 |
| 网络异常 | 同 AI 超时 |
| 数据库异常 | 任务标记 failed，事务回滚 |

**重试 API 不影响历史记录**：`retry_count` 字段追踪重试次数，便于审计。

---

## 7. 测试

参见: `backend/test_batch_content.py`（18 个测试用例，覆盖任务全生命周期、并发、取消、重试、导出）

---

## 8. 前端集成

`BatchTaskManager.vue` 提供：
- 任务列表 + 状态筛选
- 批量选择 + 导出对话框
- 展开行查看内容预览
- 重试/取消按钮
- 实时进度条（30s 轮询）

---

## 9. 相关文档

- 内容生成 API: `docs/api/04-content-generation.md`
- 即梦 AI API: `docs/api/11-jimeng-ai.md`（待补充）
- 计费引擎: `specs/SPEC-BILLING-AUTOBIND.md`
- 配额管理: `docs/api/05-user-center.md#配额`