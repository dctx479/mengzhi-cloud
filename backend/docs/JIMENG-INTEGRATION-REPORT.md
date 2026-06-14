# 即梦AI (Jimeng) Provider 集成报告

## 项目概览

**完成日期**: 2026-06-13 (REST API + 品牌故事集成于 2026-06-14 补充)
**版本**: v1.1
**状态**: ✅ 全部完成并测试通过 (22/22)；REST API 13 端点已注册

## 一、功能特性

### 1.1 核心能力

即梦AI是字节跳动旗下火山引擎的**视觉智能平台**，提供图像/视频/音频生成能力。
与 `volcengine_provider.py` (方舟 Ark LLM) 是火山引擎下两个**不同的产品**:

| 产品 | endpoint | 用途 |
|------|----------|------|
| 方舟 Ark LLM | `ark.cn-beijing.volces.com/api/v3` | 文本对话、embedding |
| **即梦AI 视觉** | `visual.volcengineapi.com` | **图像/视频/音频生成** |

### 1.2 完整支持的模型 (14个)

**图像生成 (8个)**

| 模型 | 名称 | 价格 (元/次) | 适用场景 |
|------|------|------------|---------|
| `text-to-image-3.0` | 文生图3.0 | 0.2 | 稳定版本 |
| `text-to-image-3.1` | 文生图3.1 | 0.2 | 性价比高 (推荐) |
| `image-generation-4.0` | 图片生成4.0 | 0.5 | 高质量 |
| `image-generation-4.6` | 图片生成4.6 | 0.5 | 最新版本 |
| `image-to-image-3.0` | 图生图3.0智能参考 | 0.2 | 风格迁移 |
| `material-extraction` | 素材提取 | 0.5 | 电商商品图 |
| `inpainting` | 交互编辑 | - | 局部修复 |
| `outpainting` | 智能扩图 | - | 图片外延 |

**视频生成 (5个)**

| 模型 | 名称 | 计费 | 适用场景 |
|------|------|------|---------|
| `video-generation-3.0-pro` | 视频生成3.0 Pro | 按秒 | 高质量 |
| `video-generation-3.0-720p` | 视频生成3.0 720P | 按秒 | 标清 |
| `video-generation-3.0-1080p` | 视频生成3.0 1080P | 按秒 | 高清 |
| `action-imitation` | 动作模仿 | 按次 | 舞蹈/动作迁移 |
| `omni-human-1.5` | OmniHuman1.5数字人 | 按次 | 数字人生成 |

**音频生成 (1个)**

| 模型 | 名称 | 计费 |
|------|------|------|
| `tts` | 小云雀AI配音 | 按字符 |

## 二、系统架构

```
┌──────────────────────────────────────────────────┐
│ JimengAI Client (单类) │
│ - api_key: str │
│ - endpoint: str (默认 visual.volcengineapi.com) │
│ - headers: Bearer token │
├──────────────────────────────────────────────────┤
│ HTTP Layer (httpx.AsyncClient) │
│ - POST /api/v1/image/.. (图像) │
│ - POST /api/v1/video/.. (视频, 异步任务) │
│ - POST /api/v1/audio/.. (音频) │
│ - GET /api/v1/task/query (轮询任务结果) │
├──────────────────────────────────────────────────┤
│ 业务方法 (按媒体类型) │
│ 图像: text_to_image / image_to_image │
│ inpainting / outpainting / extract_material │
│ 视频: generate_video (sync/async) │
│ action_imitation / omni_human │
│ 音频: text_to_speech │
│ 工具: upload_image / test_connection │
└──────────────────────────────────────────────────┘
```

## 三、核心组件

### 3.1 JimengAI Client

**文件**: `app/services/ai/providers/jimeng_provider.py` (约384行)

**核心属性**:
```python
IMAGE_MODELS = { # 8个图像模型
 "text-to-image-3.0": {"name": "文生图3.0", "price": 0.2, ..},
 ..
}
VIDEO_MODELS = { # 5个视频模型
 "video-generation-3.0-pro": {"name": "视频生成3.0 Pro", ..},
 ..
}
AUDIO_MODELS = { # 1个音频模型
 "tts": {"name": "小云雀AI配音", ..},
}
```

**核心方法** (按类别分组):

```python
# 客户端
def __init__(api_key, endpoint=None, timeout=120.0)
async def test_connection() -> Dict

# 图像生成
async def text_to_image(prompt, model="text-to-image-3.1", ..) -> {image_url, cost_cny}
async def image_to_image(reference_image_url, prompt, strength=0.7) -> {image_url, cost_cny}
async def extract_material(image_url, material_type="POD") -> {materials, cost_cny}
async def inpainting(image_url, mask_url, prompt) -> {image_url}
async def outpainting(image_url, direction="all", ratio=1.5) -> {image_url}
async def upload_image(image_path) -> image_url # 本地图片转URL

# 视频生成 (异步任务模式)
async def generate_video(prompt, model="video-generation-3.0-pro", wait=True, ..) -> {task_id, video_url}
async def action_imitation(source_video_url, target_image_url, ..) -> {task_id, video_url}
async def omni_human(image_url, audio_url=None, script=None) -> {task_id, video_url}

# 音频生成
async def text_to_speech(text, voice="female_1", speed=1.0, pitch=1.0, ..) -> {audio_url, duration_sec}
```

### 3.2 异步任务轮询机制

视频生成是**异步任务**模式: 提交任务 → 轮询状态 → 获取结果。

```python
async def _poll_task(self, task_id, max_attempts=60, interval=5.0):
 for attempt in range(max_attempts):
 data = await self._request("GET", "/api/v1/task/query", params={"task_id": task_id})
 if data["status"] == "completed":
 return data # 包含 video_url
 elif data["status"] == "failed":
 raise JimengAPIError(f"Task failed: {data['error']}")
 await asyncio.sleep(interval)
 raise TimeoutError(..)
```

## 四、测试结果

### 4.1 测试覆盖

**测试文件**: `test_jimeng_api.py` (265行, 22个测试用例)

| 类别 | 测试数 | 覆盖点 |
|------|--------|--------|
| 模型常量 | 5 | 8个图像 + 5个视频 + 1个音频 + 价格 |
| 客户端初始化 | 5 | 名称、endpoint、headers、别名 |
| 图像生成 | 4 | v3.1/v4.0 payload、错误、image_to_image |
| 视频生成 | 2 | 同步等待 + 异步提交 |
| 音频生成 | 1 | TTS参数验证 |
| 错误处理 | 3 | API错误码、HTTP错误、任务失败 |
| test_connection | 2 | 成功 + 失败 |
| **合计** | **22** | **100% 通过** |

### 4.2 测试输出

```
test_jimeng_api.py::test_image_models_count PASSED [ 4%]
test_jimeng_api.py::test_video_models_count PASSED [ 9%]
test_jimeng_api.py::test_audio_models_count PASSED [ 13%]
test_jimeng_api.py::test_supported_models_total PASSED [ 18%]
test_jimeng_api.py::test_model_pricing PASSED [ 22%]
..
test_jimeng_api.py::test_test_connection_failure PASSED [100%]

======================= 22 passed, 6 warnings in 5.95s ========================
```

## 五、使用指南

### 5.1 快速开始

```python
from app.services.ai.providers.jimeng_provider import JimengAI

client = JimengAI(api_key="your_jimeng_api_key")

# 文生图 (推荐 3.1, 0.2元/图)
result = await client.text_to_image("一只可爱的橘猫", model="text-to-image-3.1")
print(result["image_url"]) # https://img.jimeng.io/xxx.jpg

# 高质量图片 (4.0, 0.5元/图)
result = await client.text_to_image("山水画", model="image-generation-4.0")

# 视频生成 (异步轮询, 默认 5 秒间隔, 60 次)
result = await client.generate_video("小猫追逐蝴蝶", model="video-generation-3.0-pro", duration=5)
print(result["video_url"])

# TTS
result = await client.text_to_speech("欢迎使用即梦AI", voice="female_1", speed=1.0)
print(result["audio_url"])

# 测试连接
status = await client.test_connection()
print(status) # {"success": True, "latency_ms": 123}
```

### 5.2 环境变量配置

```bash
# .env
JIMENG_API_KEY=your_api_key_here
# JIMENG_API_ENDPOINT=https://visual.volcengineapi.com # 可选
```

### 5.3 异步 vs 同步视频生成

| 模式 | 参数 | 返回 | 适用场景 |
|------|------|------|---------|
| 同步 (wait=True) | 默认 | {task_id, video_url, status: "completed"} | 立即需要结果的场景 |
| 异步 (wait=False) | wait=False | {task_id, status: "submitted"} | 批量提交,稍后查询 |

## 六、技术亮点

### 6.1 零依赖设计

- **无需额外SDK**: 直接使用 httpx (项目已有依赖)
- **统一请求方法**: `_request()` 封装超时、错误、JSON解析
- **类型注解完整**: 所有方法签名均有完整类型提示

### 6.2 异步任务模式

- **轮询机制**: 视频/数字人等长任务通过 `_poll_task()` 自动轮询
- **灵活等待**: `wait=True` 同步等结果, `wait=False` 立即返回 task_id
- **超时保护**: 默认 60 次 × 5秒 = 5分钟

### 6.3 错误处理完善

- **JimengAPIError**: 业务错误, 携带 `code` 字段
- **HTTPStatusError**: 透传 httpx 错误, 401/429/500 都有明确语义
- **TaskFailedError**: 任务失败时携带 server 错误信息

### 6.4 与 BaseAIProvider 的关系

即梦AI **不继承** `BaseAIProvider`, 因为它不是 LLM chat 模型:
- 无 `chat` / `chat_stream` 方法 (无文本对话能力)
- 无 `embedding` 方法 (即梦AI的向量化不在此endpoint)
- 提供 `text_to_image` / `generate_video` / `text_to_speech` 等多媒体方法

如需统一接口, 后续可创建 `MultimediaProvider` 抽象基类:

```python
class MultimediaProvider(ABC):
 @abstractmethod
 async def generate(..) -> Dict: pass
 @abstractmethod
 async def test_connection(self) -> Dict: pass
```

## 七、集成清单

### 7.1 文件交付

| 文件 | 行数 | 描述 |
|------|------|------|
| `app/services/ai/providers/jimeng_provider.py` | 384 | Provider实现 + 模型常量 + 错误类型 |
| `test_jimeng_api.py` | 265 | 完整测试套件 (22 个用例) |

### 7.2 依赖项

无需新增依赖,使用项目已有的:
- `httpx>=0.24.0` (HTTP 客户端)
- `loguru` (日志)
- `asyncio` (标准库)
- `base64` (标准库, 本地图片上传)

### 7.3 集成步骤

1. ✅ 创建 `jimeng_provider.py` (384行)
2. ✅ 实现 14 个模型 (图像 8 + 视频 5 + 音频 1)
3. ✅ 编写 22 个测试用例, 100% 通过
4. ✅ 创建 REST API 端点 (`/api/v1/jimeng/..`, 13个) — 见第十三章
5. ✅ 集成到内容生成工作流 (品牌故事自动配图) — 见 `BRAND-STORY-INTEGRATION-REPORT.md`
6. ✅ 注册到多媒体工厂 `MultimediaProviderFactory` (`app/services/ai/multimedia_factory.py`)

## 八、成本分析

### 8.1 图像生成成本

| 模型 | 单价 (元/图) | 1000次成本 |
|------|------------|-----------|
| 文生图3.0/3.1 | 0.2 | ¥200 |
| 图片生成4.0/4.6 | 0.5 | ¥500 |
| 素材提取 | 0.5 | ¥500 |
| 图生图3.0 | 0.2 | ¥200 |

### 8.2 视频生成成本

按秒计费,假设 1元/秒:
- 5秒视频 × 1000次 = ¥5,000

### 8.3 优化建议

1. 优先使用文生图3.1 (性价比最高, 0.2元/图)
2. 批量任务用 `wait=False` 异步提交, 避免长时间阻塞
3. 缓存结果: 相同 prompt 的生成结果可缓存
4. 监控失败率, 设置告警

## 九、与 volcengine_provider.py 的关系

| 维度 | volcengine_provider.py | jimeng_provider.py |
|------|----------------------|-------------------|
| 产品 | 方舟 Ark | 即梦AI 视觉 |
| endpoint | ark.cn-beijing.volces.com/api/v3 | visual.volcengineapi.com |
| 能力 | LLM chat / embedding | 图像/视频/音频生成 |
| 协议 | OpenAI 兼容 | 自有 JSON API |
| 流式 | 是 (SSE) | 否 (仅轮询) |
| 任务模式 | 同步 + 流式 | 同步 + 异步任务 |
| 继承 | BaseAIProvider | 独立类 (多媒体) |
| 模型数 | 15 (LLM) | 14 (多媒体) |

## 十、文档索引

- **Provider 源码**: `app/services/ai/providers/jimeng_provider.py`
- **测试用例**: `test_jimeng_api.py`
- **参考文档**: `F:\Ai\API接入聚合指南\即梦AI API接入示例.md`
- **官方文档**: https://www.volcengine.com/product/visual
- **控制台**: https://console.volcengine.com/visual

## 十一、下一步优化

### 11.1 短期 (1-2周)

- [x] 创建 FastAPI REST 端点 `/api/v1/jimeng/..` (13个, 已完成)
- [x] 集成到品牌故事生成器 (自动配图, 已完成)
- [ ] 实现结果本地缓存 (避免重复生成)
- [ ] 添加成本统计中间件

### 11.2 中期 (1-2月)

- [ ] 创建 `MultimediaProvider` 抽象基类, 统一接口
- [ ] 集成到 AIProviderFactory (扩展 `_providers` 字典)
- [ ] 图像编辑工作流 (upload → inpainting → outpainting 链式)
- [ ] 视频任务进度 WebSocket 推送

### 11.3 长期 (3-6月)

- [ ] 多媒体内容审核 (生成前过滤违规 prompt)
- [ ] CDN 加速 + 图片懒加载
- [ ] A/B 测试不同 prompt 与模型组合的效果
- [ ] 与产品图库联动 (生成的图片自动归档)

## 十二、总结

✅ **已完成**:
1. JimengAI 完整实现 (384行)
2. 14 个多媒体模型 (8 图像 + 5 视频 + 1 音频)
3. 22 个测试用例, 100% 通过 (265行)
4. 异步任务轮询机制 (视频/数字人)
5. 完善错误处理 (JimengAPIError + HTTP错误 + 任务失败)
6. 模型价格表内置, 便于成本估算

🎯 **核心优势**:
- **零新增依赖**: 仅使用 httpx + 标准库
- **多媒体全覆盖**: 图像/视频/音频一站式接入
- **异步友好**: 视频长任务支持 wait=True/False 两种模式
- **国产化**: 即梦AI 是中国合规的视觉AI服务商
- **价格优势**: 0.2元/图 起, 比国外服务便宜 50%+

📈 **业务价值**:
- 为品牌故事、产品详情页自动生成配图
- 数字人短视频 (OmniHuman1.5) 降低视频制作成本
- TTS 配音快速生成产品介绍语音
- 风格迁移/扩图 提升图片素材利用率

系统已生产就绪! 🚀

## 十三、REST API 端点 (v1.1 新增)

**文件**: `app/api/v1/jimeng.py`
**前缀**: `/api/v1/jimeng` (由 `app/api/v1/router.py` 注册)
**认证**: 全部端点依赖 `get_current_user`，按企业 (`enterprise_id`) 查询 `TenantAIConfig` 中 `provider=="jimeng"` 且 `is_active==True` 的配置，按 `priority` 降序取第一条，解密 `api_key_encrypted` 后构造 `JimengAI` 客户端。

### 13.1 端点清单 (13个)

| 方法 | 路径 | 业务方法 | 说明 |
|------|------|---------|------|
| POST | `/api/v1/jimeng/text-to-image` | `text_to_image` | 文生图 |
| POST | `/api/v1/jimeng/image-to-image` | `image_to_image` | 图生图/风格迁移 |
| POST | `/api/v1/jimeng/inpainting` | `inpainting` | 局部修复 |
| POST | `/api/v1/jimeng/outpainting` | `outpainting` | 智能扩图 |
| POST | `/api/v1/jimeng/extract-material` | `extract_material` | 素材提取 |
| POST | `/api/v1/jimeng/generate-video` | `generate_video` | 视频生成 (异步轮询) |
| POST | `/api/v1/jimeng/action-imitation` | `action_imitation` | 动作模仿 |
| POST | `/api/v1/jimeng/omni-human` | `omni_human` | OmniHuman1.5 数字人 |
| POST | `/api/v1/jimeng/text-to-speech` | `text_to_speech` | TTS 配音 |
| POST | `/api/v1/jimeng/upload-image` | `upload_image` | 本地图片转 URL |
| GET | `/api/v1/jimeng/task/{task_id}` | `_poll_task` | 查询异步任务状态 |
| GET | `/api/v1/jimeng/models` | - | 返回支持的模型列表 |
| POST | `/api/v1/jimeng/test-connection` | `test_connection` | 连通性测试 |

### 13.2 请求体示例

```jsonc
// POST /api/v1/jimeng/text-to-image
{
  "prompt": "中国传统水墨山水画",
  "model": "text-to-image-3.1",   // 默认
  "width": 1024,                   // 256-2048
  "height": 1024,                  // 256-2048
  "steps": 50,                     // 1-100
  "guidance_scale": 7.5,           // 0-20
  "seed": -1,
  "negative_prompt": ""
}

// POST /api/v1/jimeng/image-to-image
{
  "reference_image_url": "https://.../ref.jpg",
  "prompt": "改为油画风格",
  "strength": 0.7,                 // 0-1
  "seed": -1
}
```

### 13.3 错误处理

- `JimengAPIError` → `HTTP 400`，`detail` 为业务错误信息
- 未配置即梦 → `HTTP 404` `"Jimeng not configured"`
- API Key 解密失败 → `HTTP 500` `"API Key decrypt failed"`

### 13.4 已知修复

- **2026-06-14**: 修复 `_get_jimeng_client` 中 `endpoint = config.base_url or None` 误置于 `except` 块内（`raise` 之后不可达），导致成功路径下 `endpoint` 未定义触发 `NameError`。已移至函数体层级，所有端点恢复正常。

### 13.5 关于工厂注册

即梦 **未** 注册到 `AIProviderFactory`（该工厂仅管理继承 `BaseAIProvider` 的 LLM chat/embedding Provider，其故障转移逻辑依赖 `provider.chat`，与多媒体生成不兼容）。

**2026-06-14**：已建立平行的多媒体抽象与独立工厂：
- `app/services/ai/multimedia_provider.py` — `MultimediaProvider` 抽象基类（能力声明式：`capabilities` + `generate_image/generate_video/generate_audio`，未支持能力抛 `UnsupportedCapabilityError`）
- `JimengAI` 现 **原地继承** `MultimediaProvider`（声明 IMAGE/VIDEO/AUDIO 三项能力，保留全部既有方法）
- `app/services/ai/multimedia_factory.py` — `MultimediaProviderFactory`，注册表 `{"jimeng": JimengAI}`，复用 chat 工厂的「SHA-256 缓存键 + 线程锁」模式，提供 `create / create_from_config / resolve_for_enterprise`
- `jimeng.py::_get_jimeng_client` 与 `brand_story::_generate_cover_image` 已重构为统一走 `MultimediaProviderFactory.resolve_for_enterprise`，消除重复的「查配置+解密+实例化」代码
- 测试：`test_multimedia_provider.py`（13 用例全通过），`test_jimeng_api.py`（22 用例回归通过）

