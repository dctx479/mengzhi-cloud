# 内容生成API

## 获取所有模板

**GET** `/api/content-generation/templates`

需要认证。

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 否 | 模板分类: product, slogan, marketing, social, video |

### 响应示例

```json
[
  {
    "id": "tpl_001",
    "category": "product",
    "name": "产品描述",
    "description": "生成吸引人的产品描述文案",
    "sample": "这款有机苹果来自山东烟台...",
    "difficulty": "easy",
    "usage_count": 1250,
    "parameters": {
      "word_count_range": [50, 500],
      "styles": ["professional", "casual", "emotional"]
    },
    "prompt": "根据产品信息生成描述...",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### cURL示例

```bash
# 获取所有模板
curl -X GET http://localhost:3000/api/content-generation/templates \
  -H "Authorization: Bearer <your_token>"

# 按分类筛选
curl -X GET "http://localhost:3000/api/content-generation/templates?category=product" \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取模板详情

**GET** `/api/content-generation/templates/:templateId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | string | 是 | 模板ID |

### 响应示例

```json
{
  "id": "tpl_001",
  "category": "product",
  "name": "产品描述",
  "description": "生成吸引人的产品描述文案",
  "sample": "这款有机苹果来自山东烟台...",
  "difficulty": "easy",
  "usage_count": 1250,
  "parameters": {
    "word_count_range": [50, 500],
    "styles": ["professional", "casual", "emotional", "creative"],
    "audiences": ["urban", "family", "health", "gourmet"]
  },
  "prompt": "根据产品信息生成描述...",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/templates/tpl_001 \
  -H "Authorization: Bearer <your_token>"
```

---

## 生成内容

**POST** `/api/content-generation/generate`

需要认证。

### 请求参数

```json
{
  "config": {
    "product_ids": ["prod_123", "prod_124"],
    "template_id": "tpl_001",
    "count": 3,
    "style": "professional",
    "word_count": 200,
    "target_audience": ["urban", "health"],
    "keywords": ["有机", "新鲜", "健康"],
    "avoid_words": "便宜,廉价",
    "temperature": 0.7
  },
  "batch_id": "batch_001"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| config.product_ids | string[] | 是 | 产品ID列表 |
| config.template_id | string | 是 | 模板ID |
| config.count | number | 是 | 生成数量 (1-10) |
| config.style | string | 是 | 文案风格: professional, casual, emotional, creative |
| config.word_count | number | 是 | 字数 (50-1000) |
| config.target_audience | string[] | 是 | 目标受众: urban, family, health, gourmet |
| config.keywords | string[] | 否 | 关键词 |
| config.avoid_words | string | 否 | 避免使用的词 |
| config.temperature | number | 否 | 创意度 (0-1, 默认0.7) |
| batch_id | string | 否 | 批量任务ID |

### 响应示例

```json
[
  {
    "id": "result_001",
    "content": "这款来自山东烟台的有机苹果，采用传统种植方式...",
    "metadata": {
      "word_count": 198,
      "template_id": "tpl_001",
      "product_id": "prod_123"
    }
  },
  {
    "id": "result_002",
    "content": "精选烟台优质有机苹果，口感脆甜，营养丰富...",
    "metadata": {
      "word_count": 205,
      "template_id": "tpl_001",
      "product_id": "prod_123"
    }
  }
]
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/content-generation/generate \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "product_ids": ["prod_123"],
      "template_id": "tpl_001",
      "count": 3,
      "style": "professional",
      "word_count": 200,
      "target_audience": ["urban", "health"],
      "keywords": ["有机", "新鲜"],
      "temperature": 0.7
    }
  }'
```

---

## 流式生成内容 (WebSocket)

**WebSocket** `/api/content-generation/stream/:taskId`

需要认证。使用WebSocket实现实时流式生成。

### 连接示例 (JavaScript)

```javascript
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const ws = new WebSocket(`${protocol}//localhost:3000/api/content-generation/stream/task_123`)

ws.onopen = () => {
  console.log('连接已建立')
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('收到数据:', data)
  // data: { type: 'progress', progress: 50, current: 5, total: 10 }
  // data: { type: 'result', result: {...} }
  // data: { type: 'complete' }
}

ws.onerror = (error) => {
  console.error('WebSocket错误:', error)
}

ws.onclose = () => {
  console.log('连接已关闭')
}
```

---

## 获取批量任务状态

**GET** `/api/content-generation/tasks/:taskId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | 是 | 任务ID |

### 响应示例

```json
{
  "id": "task_123",
  "name": "产品描述生成",
  "template": "产品描述",
  "template_id": "tpl_001",
  "count": 10,
  "progress": 80,
  "status": "running",
  "results": [
    {
      "id": "result_001",
      "template_id": "tpl_001",
      "product_id": "prod_123",
      "content": "这款来自山东烟台的有机苹果...",
      "word_count": 198,
      "rating": 4.5,
      "edited": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:01:00Z",
  "started_at": "2024-01-01T00:00:05Z"
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/tasks/task_123 \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取所有批量任务

**GET** `/api/content-generation/tasks`

需要认证。

### 响应示例

```json
[
  {
    "id": "task_123",
    "name": "产品描述生成",
    "template": "产品描述",
    "template_id": "tpl_001",
    "count": 10,
    "progress": 100,
    "status": "completed",
    "results": [],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:02:00Z",
    "started_at": "2024-01-01T00:00:05Z",
    "completed_at": "2024-01-01T00:02:00Z"
  }
]
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/tasks \
  -H "Authorization: Bearer <your_token>"
```

---

## 取消批量任务

**POST** `/api/content-generation/tasks/:taskId/cancel`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | 是 | 任务ID |

### 响应示例

```json
{
  "message": "任务已取消"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/content-generation/tasks/task_123/cancel \
  -H "Authorization: Bearer <your_token>"
```

---

## 导出结果为TXT

**GET** `/api/content-generation/tasks/:taskId/export/txt`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | 是 | 任务ID |

### 响应示例

```text
产品描述生成结果
生成时间: 2024-01-01 00:00:00

---

结果 1:
这款来自山东烟台的有机苹果，采用传统种植方式...

---

结果 2:
精选烟台优质有机苹果，口感脆甜，营养丰富...
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/tasks/task_123/export/txt \
  -H "Authorization: Bearer <your_token>" \
  -o results.txt
```

---

## 导出结果为DOCX

**GET** `/api/content-generation/tasks/:taskId/export/docx`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | 是 | 任务ID |

### 响应

返回DOCX文件的二进制数据。

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/tasks/task_123/export/docx \
  -H "Authorization: Bearer <your_token>" \
  -o results.docx
```

---

## 导出结果为PDF

**GET** `/api/content-generation/tasks/:taskId/export/pdf`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | 是 | 任务ID |

### 响应

返回PDF文件的二进制数据。

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/tasks/task_123/export/pdf \
  -H "Authorization: Bearer <your_token>" \
  -o results.pdf
```

---

## 保存配置

**POST** `/api/content-generation/configs`

需要认证。

### 请求参数

```json
{
  "name": "我的常用配置",
  "config": {
    "product_ids": ["prod_123"],
    "template_id": "tpl_001",
    "count": 3,
    "style": "professional",
    "word_count": 200,
    "target_audience": ["urban", "health"],
    "keywords": ["有机", "新鲜"],
    "avoid_words": "",
    "temperature": 0.7
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 配置名称 |
| config | object | 是 | 生成配置 |

### 响应示例

```json
{
  "id": "config_001",
  "name": "我的常用配置",
  "config": {
    "product_ids": ["prod_123"],
    "template_id": "tpl_001",
    "count": 3,
    "style": "professional",
    "word_count": 200,
    "target_audience": ["urban", "health"],
    "keywords": ["有机", "新鲜"],
    "avoid_words": "",
    "temperature": 0.7
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/content-generation/configs \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的常用配置",
    "config": {
      "product_ids": ["prod_123"],
      "template_id": "tpl_001",
      "count": 3,
      "style": "professional",
      "word_count": 200,
      "target_audience": ["urban", "health"],
      "keywords": ["有机", "新鲜"],
      "temperature": 0.7
    }
  }'
```

---

## 获取已保存的配置列表

**GET** `/api/content-generation/configs`

需要认证。

### 响应示例

```json
[
  {
    "id": "config_001",
    "name": "我的常用配置",
    "config": {
      "product_ids": ["prod_123"],
      "template_id": "tpl_001",
      "count": 3,
      "style": "professional",
      "word_count": 200,
      "target_audience": ["urban", "health"],
      "keywords": ["有机", "新鲜"],
      "avoid_words": "",
      "temperature": 0.7
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/configs \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取单个已保存的配置

**GET** `/api/content-generation/configs/:configId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| configId | string | 是 | 配置ID |

### 响应示例

```json
{
  "id": "config_001",
  "name": "我的常用配置",
  "config": {
    "product_ids": ["prod_123"],
    "template_id": "tpl_001",
    "count": 3,
    "style": "professional",
    "word_count": 200,
    "target_audience": ["urban", "health"],
    "keywords": ["有机", "新鲜"],
    "avoid_words": "",
    "temperature": 0.7
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/configs/config_001 \
  -H "Authorization: Bearer <your_token>"
```

---

## 删除已保存的配置

**DELETE** `/api/content-generation/configs/:configId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| configId | string | 是 | 配置ID |

### 响应示例

```json
{
  "message": "配置已删除"
}
```

### cURL示例

```bash
curl -X DELETE http://localhost:3000/api/content-generation/configs/config_001 \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取历史记录

**GET** `/api/content-generation/history`

需要认证。

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | number | 否 | 20 | 返回数量 |
| offset | number | 否 | 0 | 偏移量 |

### 响应示例

```json
{
  "items": [
    {
      "id": "history_001",
      "task_id": "task_123",
      "template_id": "tpl_001",
      "config": {},
      "results": [],
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 50
}
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/content-generation/history?limit=20&offset=0" \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取统计数据

**GET** `/api/content-generation/statistics`

需要认证。

### 响应示例

```json
{
  "total_tasks": 150,
  "total_results": 1500,
  "total_words": 300000,
  "most_used_template": {
    "id": "tpl_001",
    "name": "产品描述",
    "usage_count": 80
  },
  "recent_activity": [
    {
      "date": "2024-01-01",
      "tasks": 10,
      "results": 100
    }
  ]
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/content-generation/statistics \
  -H "Authorization: Bearer <your_token>"
```

---

## 错误处理

### 常见错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| TEMPLATE_NOT_FOUND | 404 | 模板不存在 |
| TASK_NOT_FOUND | 404 | 任务不存在 |
| CONFIG_NOT_FOUND | 404 | 配置不存在 |
| INVALID_PRODUCT_IDS | 400 | 无效的产品ID |
| INVALID_COUNT | 400 | 生成数量必须在1-10之间 |
| INVALID_WORD_COUNT | 400 | 字数必须在50-1000之间 |
| QUOTA_EXCEEDED | 429 | 配额已用完 |
| GENERATION_FAILED | 500 | 生成失败 |
| TASK_ALREADY_CANCELLED | 400 | 任务已取消 |
| EXPORT_FAILED | 500 | 导出失败 |
