# API接口规范文档
## API Specification v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**Base URL**: `http://localhost:8000` (开发) / `https://api.mengzhi.cloud` (生产)

---

## 一、通用规范

### 1.1 请求规范

**请求头**
```http
Content-Type: application/json
Authorization: Bearer {access_token}
X-Request-ID: {unique_request_id}
```

**响应格式**
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": "2026-06-11T10:30:00Z"
}
```

**错误响应**
```json
{
  "code": 400,
  "message": "Invalid parameter: product_id is required",
  "data": null,
  "timestamp": "2026-06-11T10:30:00Z",
  "error_detail": {
    "field": "product_id",
    "reason": "required field missing"
  }
}
```

### 1.2 状态码

| Code | 含义 | 说明 |
|------|------|------|
| 200 | Success | 请求成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未授权 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 429 | Too Many Requests | 请求频率过高 |
| 500 | Internal Server Error | 服务器错误 |

---

## 二、IP智能体API

### 2.1 对话接口

**POST /api/v1/ip/chat**

发起与IP智能体的对话。

**请求参数**
```json
{
  "ip_type": "xiaoshu",  // 必填: xiaoshu | xiaoshang
  "message": "推荐一款送礼的羊肉",  // 必填
  "session_id": "sess_xxx",  // 可选，不传则自动生成
  "user_id": 123,  // 可选
  "product_id": 456,  // 可选，当前讨论的产品
  "options": {
    "stream": false,  // 是否流式响应
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**响应示例**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "sess_xxx",
    "ip_type": "xiaoshu",
    "response": "咱们草原上的羊肉啊，要是送礼的话...",
    "suggestions": [
      "小数推荐的这款有什么特点？",
      "怎么保存和烹饪？"
    ],
    "cultural_elements": ["草原", "老额吉", "呼伦贝尔"],
    "tokens_used": 856,
    "latency_ms": 1234
  }
}
```

### 2.2 切换IP

**POST /api/v1/ip/switch**

切换当前对话的IP。

**请求参数**
```json
{
  "current_ip": "xiaoshu",
  "target_ip": "xiaoshang",
  "session_id": "sess_xxx"
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "message": "好的，我帮您转到小商那边。稍等片刻~",
    "context_preservation": {
      "product_info": "保留",
      "conversation_history": "保留"
    }
  }
}
```

### 2.3 品牌故事生成

**POST /api/v1/ip/brand-story**

生成产品品牌故事。

**请求参数**
```json
{
  "product_name": "锡林郭勒羊肉",
  "category": "牛羊肉",
  "origin": "锡林郭勒",
  "selling_points": ["草原散养", "肉质紧实", "无膻味"],
  "target_audience": "注重品质的都市家庭"
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "story_title": "锡林郭勒羊肉 - 草原的味道",
    "story_content": "在辽阔的锡林郭勒大草原上...",
    "word_count": 456,
    "cultural_elements": ["那达慕", "草原游牧文化"],
    "usage": {
      "tokens": 1234,
      "credits": 12
    }
  }
}
```

### 2.4 直播脚本生成

**POST /api/v1/ip/live-script**

生成直播带货脚本。

**请求参数**
```json
{
  "product_name": "锡林郭勒羊肉",
  "price": "299元/5斤",
  "promotion": "下单立减50元",
  "stock": "限量1000份",
  "duration": 5,  // 分钟
  "platform": "douyin",  // douyin/xiaohongshu/shipinhao
  "style": "热情"  // 热情/专业/亲和
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "product_name": "锡林郭勒羊肉",
    "duration": 5,
    "platform": "douyin",
    "script": [
      {
        "phase": "开场",
        "start": "0:00",
        "end": "0:30",
        "scene": "草原风景空镜 + 产品展示",
        "script": "老铁们好！欢迎来到直播间！..."
      },
      {
        "phase": "痛点引入",
        "start": "0:30",
        "end": "1:30",
        "scene": "主播近景",
        "script": "大家都知道，买羊肉最怕的就是..."
      },
      // ...更多分镜
    ],
    "bgm_suggestions": ["草原歌曲", "欢快背景音乐"],
    "shooting_tips": ["开场用航拍草原镜头", "产品讲解时多角度展示"]
  }
}
```

### 2.5 对话历史

**GET /api/v1/ip/history/{session_id}**

获取指定会话的对话历史。

**路径参数**
- `session_id`: 会话ID

**响应示例**
```json
{
  "code": 200,
  "data": {
    "session_id": "sess_xxx",
    "ip_type": "xiaoshu",
    "messages": [
      {
        "role": "user",
        "content": "推荐一款羊肉",
        "timestamp": "2026-06-11T10:00:00Z"
      },
      {
        "role": "ai",
        "content": "咱们草原上的羊肉...",
        "timestamp": "2026-06-11T10:00:02Z",
        "tokens_used": 856
      }
    ],
    "total_messages": 10,
    "total_tokens": 8560
  }
}
```

---

## 三、知识图谱API

### 3.1 文化元素列表

**GET /api/v1/knowledge/cultures**

查询文化元素。

**查询参数**
- `type`: 类型过滤（festival/skill/story/food/custom/craft）
- `keyword`: 关键词搜索
- `limit`: 返回数量，默认20

**响应示例**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "那达慕",
        "type": "festival",
        "description": "蒙古族传统盛会...",
        "origin_region": "内蒙古全域",
        "hot_score": 95
      }
    ],
    "total": 15
  }
}
```

### 3.2 产品文化溯源

**GET /api/v1/knowledge/trace/{product_id}**

获取产品的文化溯源报告。

**响应示例**
```json
{
  "code": 200,
  "data": {
    "product": {
      "id": 123,
      "name": "锡林郭勒羊肉",
      "category": "牛羊肉"
    },
    "origin": {
      "id": 1,
      "name": "锡林郭勒",
      "description": "内蒙古中部草原..."
    },
    "cultures": [
      {
        "name": "那达慕",
        "type": "festival",
        "level": "origin",
        "story": "那达慕大会的主场地..."
      },
      {
        "name": "手把肉",
        "type": "food",
        "level": "heritage",
        "story": "传统蒙古族吃法..."
      }
    ],
    "auto_story": "在辽阔的锡林郭勒大草原上..."
  }
}
```

### 3.3 推荐文化元素

**POST /api/v1/knowledge/recommend**

为产品推荐相关文化元素。

**请求参数**
```json
{
  "product_id": 123,
  "count": 3
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "recommendations": [
      {
        "id": 1,
        "name": "那达慕",
        "type": "festival",
        "relevance_score": 0.95,
        "reason": "产地锡林郭勒是那达慕主场地"
      }
    ]
  }
}
```

---

## 四、产品管理API（已有）

### 4.1 产品列表

**GET /api/v1/products**

**查询参数**
- `page`: 页码，默认1
- `size`: 每页数量，默认20
- `category`: 品类过滤
- `origin`: 产地过滤

### 4.2 产品详情

**GET /api/v1/products/{id}**

### 4.3 创建产品

**POST /api/v1/products**

---

## 五、速率限制

| 用户类型 | 限制 | 说明 |
|---------|------|------|
| 免费用户 | 100次/天 | IP对话+内容生成总次数 |
| 付费用户 | 1000次/天 | |
| 企业用户 | 10000次/天 | |

**超限响应**
```json
{
  "code": 429,
  "message": "Rate limit exceeded. Try again in 3600 seconds.",
  "data": {
    "limit": 100,
    "remaining": 0,
    "reset_at": "2026-06-12T00:00:00Z"
  }
}
```

---

## 六、媒体生成API（图像/视频）

### 6.1 生成产品营销图片

**POST /api/v1/media/generate-image**

生成产品营销图片（基于火山引擎即梦AI）。

**请求参数**
```json
{
  "prompt": "内蒙古草原上的羊群，夕阳下金黄色的草地",
  "product_id": 123,  // 可选，关联产品自动融合文化元素
  "style": "realistic",  // realistic | anime | oil_painting
  "width": 1024,
  "height": 1024,
  "negative_prompt": "低质量，模糊"  // 可选
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "image_url": "https://cdn.mengzhi.cloud/images/xxx.jpg",
    "image_id": "img_20260611_xxx",
    "prompt": "内蒙古草原羊群...",  // 增强后的Prompt
    "cultural_elements": ["草原游牧文化", "锡林郭勒"],
    "cost": 0.1,  // 单价（元）
    "resolution": "1024x1024"
  }
}
```

### 6.2 生成产品宣传视频

**POST /api/v1/media/generate-video**

生成产品宣传短视频（基于火山引擎即梦AI）。

**请求参数**
```json
{
  "prompt": "展示锡林郭勒草原的羊群，镜头从远景拉近",
  "product_id": 123,  // 可选
  "duration": 5,  // 秒数，支持5/10/15
  "resolution": "1080p",  // 720p | 1080p | 4k
  "fps": 30
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "video_url": "https://cdn.mengzhi.cloud/videos/xxx.mp4",
    "task_id": "vid_20260611_xxx",
    "status": "completed",  // processing | completed | failed
    "duration": 5,
    "resolution": "1080p",
    "cost": 2.0,  // 单价（元）
    "thumbnail_url": "https://cdn.mengzhi.cloud/thumbnails/xxx.jpg"
  }
}
```

### 6.3 查询视频生成任务

**GET /api/v1/media/video-task/{task_id}**

查询视频生成任务状态（异步任务）。

**响应示例**
```json
{
  "code": 200,
  "data": {
    "task_id": "vid_20260611_xxx",
    "status": "processing",  // processing | completed | failed
    "progress": 65,  // 进度百分比
    "estimated_time": 120,  // 预计剩余秒数
    "video_url": null  // 完成后才有
  }
}
```

### 6.4 媒体生成历史

**GET /api/v1/media/history**

获取用户的媒体生成历史记录。

**查询参数**
- `type`: image | video
- `page`: 页码，默认1
- `size`: 每页数量，默认20

**响应示例**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "type": "image",
        "prompt": "草原羊群",
        "media_url": "https://cdn.mengzhi.cloud/images/xxx.jpg",
        "cost": 0.1,
        "created_at": "2026-06-11T10:00:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "size": 20
  }
}
```

---

## 七、AI服务商配置API（管理员）

### 7.1 查询服务商配置

**GET /api/v1/admin/ai-providers**

获取所有AI服务商配置（需要admin权限）。

**响应示例**
```json
{
  "code": 200,
  "data": [
    {
      "provider": "deepseek",
      "model_name": "deepseek-chat",
      "is_active": true,
      "priority": 1,
      "api_key_masked": "sk-****xxxx",
      "config": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    },
    {
      "provider": "volcengine",
      "model_name": "jimeng-ai",
      "is_active": true,
      "priority": 2,
      "api_key_masked": "AKLT****xxxx"
    }
  ]
}
```

### 7.2 创建服务商配置

**POST /api/v1/admin/ai-providers**

**请求参数**
```json
{
  "provider": "deepseek",
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "api_endpoint": "https://api.deepseek.com/v1",
  "model_name": "deepseek-chat",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

### 7.3 测试服务商连接

**POST /api/v1/admin/ai-providers/{provider}/test**

测试指定服务商的连接状态。

**响应示例**
```json
{
  "code": 200,
  "data": {
    "success": true,
    "message": "连接成功",
    "latency_ms": 234
  }
}
```

---

---

## 八、FAQ智能匹配API

### 8.1 FAQ自动提取

**POST /api/v1/faq/extract**

从历史对话中自动提取常见问题和答案。

**请求参数**
```json
{
  "session_ids": ["sess_1", "sess_2"],  // 可选，指定会话
  "category": "product",  // 可选，过滤类别
  "min_confidence": 0.7,  // 最小置信度
  "limit": 50  // 最多提取数量
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "extracted_count": 12,
    "faqs": [
      {
        "question": "如何挑选新鲜羊肉",
        "answer": "咱们草原上选羊肉啊...",
        "confidence": 0.85,
        "source_sessions": ["sess_1", "sess_3"]
      }
    ]
  }
}
```

### 8.2 FAQ匹配查询

**POST /api/v1/faq/match**

在发起对话前先匹配FAQ，命中则直接返回。

**请求参数**
```json
{
  "question": "怎么挑选羊肉",
  "category": "product",  // 可选
  "min_confidence": 0.75
}
```

**响应示例**
```json
{
  "code": 200,
  "data": {
    "matched": true,
    "faq_id": 123,
    "question": "如何挑选新鲜羊肉",
    "answer": "咱们草原上选羊肉啊...",
    "confidence": 0.87,
    "ip_type": "xiaoshu"
  }
}
```

### 8.3 获取FAQ列表

**GET /api/v1/faq/list**

**Query参数**
- category: 类别过滤
- ip_type: IP类型
- page: 页码
- page_size: 每页数量

**响应示例**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 123,
        "question": "如何挑选新鲜羊肉",
        "answer": "...",
        "category": "product",
        "usage_count": 45
      }
    ],
    "total": 120,
    "page": 1
  }
}
```

---

## 九、Webhook（未来扩展）

### 8.1 对话完成通知

**POST {your_webhook_url}**

```json
{
  "event": "conversation.completed",
  "data": {
    "session_id": "sess_xxx",
    "user_id": 123,
    "message_count": 5,
    "total_tokens": 4280
  },
  "timestamp": "2026-06-11T10:30:00Z"
}
```

---

**文档结束**

> 完整API文档：https://api.mengzhi.cloud/docs (Swagger UI)