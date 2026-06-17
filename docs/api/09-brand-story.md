# 品牌故事 API 文档

**版本**: v1.0  
**更新日期**: 2026-06-17  
**模块**: 品牌故事生成（Brand Story Generation）  
**基础路径**: `/api/v1/brand-story`

---

## 1. 模块概述

品牌故事生成模块基于 AI 大模型，为农畜产品生成具有文化底蕴与情感共鸣的品牌故事文案。支持 3 种风格、字数自定义、可选文化元素融合、可选自动配图（基于即梦 AI）。

**核心特性**：
- 🎨 3 种故事风格：现代简约 / 传统深沉 / 情感共鸣
- 📚 自动融合文化元素（66 个内蒙古草原文化元素库）
- 🖼️ 可选即梦 AI 自动配图
- 📊 完整 Token 用量与成本统计
- 💾 自动持久化生成记录

---

## 2. API 端点

### 2.1 生成品牌故事

**端点**: `POST /api/v1/brand-story/generate`

**权限**: 需登录 (`Authorization: Bearer <token>`)

**请求体**:

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `product_name` | string | ✅ | - | 产品名称（1-100 字符） |
| `origin` | string | ✅ | - | 产地（1-100 字符） |
| `features` | string | ❌ | "" | 产品特点（≤500 字符） |
| `purpose` | string | ❌ | "电商详情页" | 使用场景（≤50 字符） |
| `style` | string | ❌ | "现代简约" | 故事风格（现代简约/传统深沉/情感共鸣） |
| `word_count` | string | ❌ | "300字左右" | 字数要求 |
| `category` | string | ❌ | "" | 产品类别（≤50 字符） |
| `keywords` | string[] | ❌ | [] | 关键词列表 |
| `use_culture` | boolean | ❌ | true | 是否使用文化元素 |
| `product_id` | int | ❌ | null | 关联的产品 ID |
| `save_record` | boolean | ❌ | true | 是否保存生成记录 |
| `auto_generate_image` | boolean | ❌ | false | 是否自动生成即梦 AI 配图 |

**请求示例**:

```bash
curl -X POST http://localhost:8000/api/v1/brand-story/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "锡林郭勒羊肉",
    "origin": "内蒙古锡林郭勒盟",
    "features": "天然放养，肉质鲜美，无膻味",
    "style": "传统深沉",
    "word_count": "500字左右",
    "keywords": ["草原", "那达慕", "蒙古族"],
    "use_culture": true,
    "auto_generate_image": true
  }'
```

**响应示例**:

```json
{
  "story": "在锡林郭勒草原的深处，风吹草低见牛羊……",
  "cultural_elements": [
    {
      "element_id": 12,
      "name": "那达慕大会",
      "category": "节日习俗",
      "match_score": 0.92
    }
  ],
  "tokens": {
    "prompt_tokens": 280,
    "completion_tokens": 580,
    "total_tokens": 860
  },
  "cost": 0.0172,
  "metadata": {
    "model": "deepseek-chat",
    "duration_ms": 3450
  },
  "record_id": 12345,
  "image_url": "https://cdn.example.com/brand-story/xxx.jpg"
}
```

**错误码**:

| HTTP | 错误码 | 说明 |
|---|---|---|
| 400 | `INVALID_PARAMS` | 参数校验失败 |
| 401 | `UNAUTHORIZED` | 未登录 |
| 402 | `QUOTA_EXHAUSTED` | 配额不足 |
| 429 | `RATE_LIMIT` | 频率超限 |
| 500 | `INTERNAL_ERROR` | 内部错误（AI 调用失败等） |

---

### 2.2 查询生成记录

**端点**: `GET /api/v1/brand-story/records`

**权限**: 需登录

**查询参数**:

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `page` | int | 1 | 页码（≥1） |
| `page_size` | int | 20 | 每页大小（1-100） |
| `product_id` | int | null | 筛选产品 |
| `style` | string | null | 筛选风格 |

**响应示例**:

```json
[
  {
    "id": 12345,
    "product_name": "锡林郭勒羊肉",
    "style": "传统深沉",
    "story_preview": "在锡林郭勒草原的深处……",
    "image_url": "https://...",
    "tokens": {"total_tokens": 860},
    "cost": 0.0172,
    "created_at": "2026-06-17T10:30:25"
  }
]
```

---

### 2.3 查询单个记录

**端点**: `GET /api/v1/brand-story/records/{record_id}`

**权限**: 需登录；仅本人/企业成员可见

**响应**: 同 2.2 单条记录结构（包含完整 story 文本）

**错误码**:

| HTTP | 错误码 | 说明 |
|---|---|---|
| 404 | `RECORD_NOT_FOUND` | 记录不存在 |
| 403 | `FORBIDDEN` | 无权访问该记录 |

---

## 3. 使用示例（前端）

```typescript
import { brandStoryApi } from '@/api/brandStory'

const result = await brandStoryApi.generate({
  product_name: '锡林郭勒羊肉',
  origin: '内蒙古锡林郭勒盟',
  style: '传统深沉',
  word_count: '500字左右',
  use_culture: true,
  auto_generate_image: true,
})
console.log(result.story)
```

---

## 4. 文化元素融合机制

当 `use_culture=true` 时：
1. 系统根据 `product_name` + `origin` + `keywords` 在 66 个文化元素中匹配 Top-K
2. 将匹配的文化元素以 prompt context 形式注入 AI 请求
3. 返回结果中 `cultural_elements` 列出实际使用的元素及其匹配分数

**匹配权重**：
- 产地精确匹配: 0.5
- 关键词重合: 0.3
- 类别相关性: 0.2

---

## 5. Token 与成本

- Token 计费按 `BillingEngine.record_usage()` 计入当前用户的计费方案
- 单次生成成本约 ¥0.01-0.05（取决于模型与字数）
- 配额消耗: 1 次内容生成配额

---

## 6. 测试用例

参见: `backend/tests/test_brand_story.py`（单元测试）  
参见: `backend/tests/test_brand_story_integration.py`（集成测试）

---

## 7. 相关文档

- 文化元素 API: `docs/api/08-cultural-elements.md`
- 文化元素扩展报告: `docs/cultural/CULTURAL-ELEMENT-EXPANSION-REPORT.md`
- IP 智能体 API: `docs/api/07-ip-agent.md`
- 内容生成 API: `docs/api/04-content-generation.md`