# 文化元素 API

> **版本**: v1
> **基础路径**: `/api/v1/cultural`
> **更新日期**: 2026-06-16

## 概述

文化元素系统管理内蒙古草原文化元素库，支持智能匹配、知识图谱查询和专家审核。核心能力：

- **66+ 文化元素**：地域、族群、历史、工艺、节日、营养、故事七大分类
- **630+ 知识图谱节点**：节点关系网络，支持语义检索
- **智能匹配**：L1 关键词精确匹配 × L3 知识图谱语义匹配双路召回
- **专家审核**：任务领取 → 审核 → 历史全流程

---

## 端点列表

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/elements` | 文化元素列表（分页+过滤） | 否 |
| GET | `/elements/{id}` | 文化元素详情 | 否 |
| POST | `/match` | 智能匹配文化元素 | 否 |
| GET | `/match/product/{id}` | 按产品ID匹配 | 否 |
| POST | `/collect/trigger` | 触发采集任务 | 必须 |
| GET | `/collect/tasks` | 采集任务列表 | 否 |
| GET | `/collect/tasks/{task_id}` | 采集任务状态 | 否 |
| GET | `/graph/statistics` | 知识图谱统计 | 否 |
| GET | `/graph/elements/by-region/{region}` | 按地域查元素 | 否 |
| GET | `/graph/elements/by-scenario/{scenario}` | 按场景查元素 | 否 |
| GET | `/review/pending` | 待审核任务列表 | 必须 |
| POST | `/review/assign/{id}` | 领取审核任务 | 必须 |
| POST | `/review/element/{id}` | 审核文化元素 | 必须 |
| GET | `/review/history` | 审核历史 | 必须 |
| GET | `/review/statistics` | 审核统计 | 必须 |
| GET | `/statistics/overview` | 文化元素统计概览 | 否 |


---

## 1. 文化元素列表

### 请求

```http
GET /api/v1/cultural/elements?type=工艺&page=1&page_size=20
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | ❌ | 元素类型过滤（如：`工艺`、`节日`、`历史`） |
| origin_region | string | ❌ | 产地过滤（模糊匹配） |
| keyword | string | ❌ | 关键词过滤（keywords 字段） |
| status | string | ❌ | 状态：`pending_review` / `approved` / `rejected` |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页数量，默认 20，最大 100 |

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "elements": [
      {
        "id": 1,
        "name": "马头琴",
        "type": "工艺",
        "origin_region": "内蒙古",
        "story_preview": "马头琴是蒙古族特有的拉弦乐器，因琴杆上端雕有马头而得名...",
        "keywords": ["乐器", "蒙古族", "非遗", "传统"],
        "status": "approved",
        "created_at": "2026-06-01T10:00:00"
      }
    ],
    "pagination": {
      "total": 66,
      "page": 1,
      "page_size": 20,
      "total_pages": 4
    }
  }
}
```


---


## 2. 文化元素详情

### 请求

```http
GET /api/v1/cultural/elements/1
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "马头琴",
    "type": "工艺",
    "story": "马头琴是蒙古族特有的拉弦乐器，因琴杆上端雕有马头而得名...",
    "origin_region": "内蒙古",
    "keywords": ["乐器", "蒙古族", "非遗", "传统"],
    "metadata": {
      "usage_scenarios": ["舞台演奏", "婚丧仪式", "草原集会"],
      "cultural_significance": "蒙古族音乐的代表符号"
    },
    "source": "蒙绣文化数据库",
    "status": "approved",
    "created_at": "2026-06-01T10:00:00",
    "reviewed_at": "2026-06-02T14:30:00"
  }
}
```

---


## 3. 智能匹配文化元素

根据产品信息匹配最相关的文化元素，支持双路召回（L1 关键词 + L3 知识图谱）。


### 请求


```http
POST /api/v1/cultural/match
Content-Type: application/json

{
  "product_name": "锡林郭勒有机羊肉",
  "origin": "锡林郭勒",
  "category": "肉类",
  "keywords": ["有机", "天然", "草原"],
  "use_knowledge_graph": true,
  "top_k": 10
}
```

**Body 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_name | string | ✅ | 产品名称 |
| origin | string | ✅ | 产地 |
| category | string | ❌ | 产品类别 |
| keywords | string[] | ❌ | 关键词列表 |
| use_knowledge_graph | bool | ❌ | 是否启用知识图谱，默认 true |
| top_k | int | ❌ | 返回前 K 个结果，默认 10，最大 50 |


### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "matched_elements": [
      {
        "element": {
          "name": "锡林郭勒草原",
          "type": "地域",
          "story": "锡林郭勒草原是内蒙古最著名的草原之一...",
          "origin_region": "锡林郭勒盟",
          "keywords": ["草原", "放牧", "天然"]
        },
        "score": 45.2,
        "match_reason": "产地"锡林郭勒"直接匹配 + 关键词"草原"重叠",
        "score_breakdown": {
          "exact_match": 20.0,
          "knowledge_graph": 25.2
        },
        "path_info": ["锡林郭勒草原", "→", "草原羊", "→", "有机羊肉"]
      }
    ],
    "total_count": 3,
    "query": {
      "name": "锡林郭勒有机羊肉",
      "origin": "锡林郭勒",
      "category": "肉类",
      "keywords": ["有机", "天然", "草原"]
    }
  }
}
```

**评分说明**：
- `exact_match`：L1 精确匹配得分（关键词命中、产地重叠等）
- `knowledge_graph`：L3 知识图谱语义匹配得分（关系路径推理）
- `score`：两者加权求和，量纲 0-60


---

## 4. 按产品ID匹配文化元素

### 请求

```http
GET /api/v1/cultural/match/product/42?use_knowledge_graph=true&top_k=5
```


**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| use_knowledge_graph | bool | ❌ | 是否启用 KG，默认 true |
| top_k | int | ❌ | 返回数量，默认 10 |

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "product_id": 42,
    "product_name": "有机草原鲜牛奶",
    "matched_elements": [...],
    "total_count": 5
  }
}
```


---


## 5. 触发采集任务

手动触发对特定产品相关文化元素的 AI 采集。


### 请求


```http
POST /api/v1/cultural/collect/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": 42,
  "product_name": "有机草原鲜牛奶",
  "origin": "呼伦贝尔",
  "category": "乳制品",
  "keywords": ["有机", "纯天然"]
}
```

### 响应


```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "collect-uuid-xxxx",
    "status": "pending",
    "message": "采集任务已创建"
  }
}
```

---

## 6. 采集任务列表

### 请求

```http
GET /api/v1/cultural/collect/tasks?status=pending&page=1&page_size=20
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | ❌ | 状态：`pending` / `running` / `completed` / `failed` |
| priority | string | ❌ | 优先级：`high` / `medium` / `low` |
| page | int | ❌ | 页码，默认 1 |
| page_size | int | ❌ | 每页数量，默认 20 |


### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tasks": [
      {
        "task_id": "collect-uuid-xxxx",
        "product_name": "有机草原鲜牛奶",
        "origin": "呼伦贝尔",
        "priority": "medium",
        "status": "completed",
        "targets": ["蒙古族奶文化", "呼伦贝尔草原"],
        "created_at": "2026-06-15T08:00:00",
        "completed_at": "2026-06-15T08:05:23"
      }
    ],
    "pagination": {
      "total": 12,
      "page": 1,
      "page_size": 20
    }
  }
}
```

---

## 7. 采集任务状态

### 请求

```http
GET /api/v1/cultural/collect/tasks/{task_id}
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "collect-uuid-xxxx",
    "status": "completed",
    "progress": 100,
    "collected_count": 3,
    "elements_found": ["蒙古族奶文化", "呼伦贝尔草原", "草原酸奶制作技艺"]
  }
}
```


---

## 8. 知识图谱统计

### 请求

```http
GET /api/v1/cultural/graph/statistics
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_nodes": 630,
    "total_edges": 1240,
    "by_type": {
      "地域": 89,
      "族群": 45,
      "历史": 112,
      "工艺": 78,
      "节日": 56,
      "营养": 67,
      "故事": 183
    }
  }
}
```

---

## 9. 按地域查找文化元素

### 请求

```http
GET /api/v1/cultural/graph/elements/by-region/锡林郭勒盟?include_synonyms=true
```

**Path 参数**：`region` — 地域名称

**Query 参数**：`include_synonyms` — 是否包含同义词，默认 true


### 响应


```json
{
  "code": 200,
  "message": "success",
  "data": {
    "region": "锡林郭勒盟",
    "count": 8,
    "elements": [
      {
        "name": "那达慕大会",
        "type": "节日",
        "story_preview": "那达慕是蒙古族传统的群众性集会...",
        "keywords": ["那达慕", "蒙古族", "体育竞技"]
      }
    ]
  }
}
```

---

## 10. 按场景查找文化元素

### 请求


```http
GET /api/v1/cultural/graph/elements/by-scenario/节庆送礼
```


**Path 参数**：`scenario` — 使用场景


### 响应


```json
{
  "code": 200,
  "message": "success",
  "data": {
    "scenario": "节庆送礼",
    "count": 5,
    "elements": [
      {
        "name": "蒙古族哈达",
        "type": "习俗",
        "story_preview": "哈达是蒙古族待客礼节中最庄重的礼节...",
        "usage_scenarios": ["节庆送礼", "婚丧仪式", "日常拜访"]
      }
    ]
  }
}
```

---

## 11. 待审核任务列表


### 请求


```http
GET /api/v1/cultural/review/pending?priority=high&limit=20
Authorization: Bearer <token>
```

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| priority | string | ❌ | 优先级过滤 |
| limit | int | ❌ | 返回数量，默认 20 |

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tasks": [
      {
        "id": 1,
        "element_name": "蒙古族马头琴",
        "priority": "high",
        "submitted_at": "2026-06-15T10:00:00",
        "submitter": "system"
      }
    ],
    "total": 5
  }
}
```

---

## 12. 领取审核任务


### 请求


```http
POST /api/v1/cultural/review/assign/1
Authorization: Bearer <token>
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": 1,
    "assigned_to": "expert-uuid-xxx",
    "assigned_at": "2026-06-16T09:00:00"
  }
}
```

---

## 13. 审核文化元素

### 请求


```http
POST /api/v1/cultural/review/element/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "decision": "approve",
  "comments": "内容准确，文化背景描述完整",
  "corrections": {
    "story": "（可选）修改后的故事文本"
  }
}
```

**Body 参数**：


| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| decision | string | ✅ | 决策：`approve` / `reject` / `request_revision` |
| comments | string | ❌ | 审核意见 |
| corrections | object | ❌ | 修正内容（key 为字段名，value 为修正值） |


### 响应


```json
{
  "code": 200,
  "message": "success",
  "data": {
    "element_id": 1,
    "decision": "approve",
    "reviewed_at": "2026-06-16T09:15:00",
    "status": "approved"
  }
}
```

---

## 14. 审核历史

### 请求

```http
GET /api/v1/cultural/review/history?element_id=1&limit=50
Authorization: Bearer <token>
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "history": [
      {
        "element_id": 1,
        "element_name": "马头琴",
        "decision": "approve",
        "comments": "内容准确",
        "reviewed_at": "2026-06-16T09:15:00"
      }
    ],
    "total": 1
  }
}
```

---


## 15. 审核统计


### 请求

```http
GET /api/v1/cultural/review/statistics
Authorization: Bearer <token>
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_reviewed": 42,
    "approved": 38,
    "rejected": 3,
    "revision_requested": 1,
    "approval_rate": 90.48
  }
}
```


---

## 16. 文化元素统计概览

### 请求


```http
GET /api/v1/cultural/statistics/overview
```

### 响应


```json
{
  "code": 200,
  "message": "success",
  "data": {
    "elements": {
      "total": 66,
      "approved": 60,
      "pending": 6
    },
    "by_type": {
      "工艺": 12,
      "节日": 8,
      "历史": 15,
      "地域": 10,
      "族群": 7,
      "营养": 6,
      "故事": 8
    },
    "tasks": {
      "total": 24,
      "completed": 22,
      "success_rate": 91.67
    }
  }
}
```

---


## 错误码

| code | HTTP状态 | 说明 |
|------|---------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 参数错误 / 决策无效 |
| 401 | 401 | 未认证或 Token 失效 |
| 403 | 403 | 无审核权限 |
| 404 | 404 | 元素/产品/任务不存在 |
| 500 | 500 | 服务器内部错误（采集/匹配/查询失败） |


---

## 评分体系详解

智能匹配采用双路召回 + 加权评分：


```
总得分 = exact_match × 0.4 + knowledge_graph × 0.2
```

| 维度 | 满分 | 计分方式 |
|------|------|---------|
| L1 精确匹配 | 40分 | 产地命中 ×2、关键词命中 ×1、品类命中 ×0.5 |
| L3 知识图谱 | 20分 | 路径推理深度 × 节点权重 |


> **阈值建议**：得分 ≥ 10.0 的元素适合展示给用户；≥ 20.0 为高质量匹配。


---

## 相关文档

- [双IP智能体API](./07-ip-agent.md)
- [产品API](./products-api.md)
- [错误码定义](./06-error-codes.md)
- [IP Agent架构设计](../technical/IP-AGENT-ARCHITECTURE.md)
- [文化元素系统架构](../technical/CULTURAL-ELEMENT-SYSTEM.md)

---

**更新日志**

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-16 | 初始版本，支持 CRUD、智能匹配、知识图谱、审核全流程 |
