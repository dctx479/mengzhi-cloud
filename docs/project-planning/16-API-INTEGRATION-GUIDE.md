# AI服务商API接入完整指南
## API Integration Guide v1.1

**文档版本**: 1.1  
**创建日期**: 2026-06-12  
**最后更新**: 2026-06-12 (基于官方文档更新)  
**适用范围**: DeepSeek LLM + 火山引擎即梦AI（图像/视频生成）

---

## 一、DeepSeek API 接入指南

### 1.1 概述

**官方文档**: 
- 中文: https://api-docs.deepseek.com/zh-cn/
- 英文: https://api-docs.deepseek.com/

**核心特性**:
- ✅ OpenAI SDK 完全兼容（直接替换base_url）
- ✅ Anthropic SDK 兼容（`/anthropic`端点）
- ✅ 1M tokens上下文窗口，最大输出384K tokens
- ✅ 支持工具调用（Function Calling）、JSON输出、流式响应
- ✅ 支持Thinking Mode（深度推理模式）
- ✅ Prompt缓存（命中可节省98%成本）

### 1.2 认证方式

**API Key获取**: https://platform.deepseek.com/api_keys

**请求头格式**:
```http
Authorization: Bearer ${DEEPSEEK_API_KEY}
Content-Type: application/json
```

### 1.3 Base URL

| 格式 | URL |
|------|-----|
| OpenAI格式 | `https://api.deepseek.com` |
| Anthropic格式 | `https://api.deepseek.com/anthropic` |

### 1.4 可用模型

| 模型名称 | 状态 | 说明 |
|---------|------|------|
| **deepseek-v4-flash** | ✅ 当前推荐 | 快速响应，适合高频对话场景 |
| **deepseek-v4-pro** | ✅ 当前推荐 | 深度推理，支持Thinking Mode |
| `deepseek-chat` | ⚠️ 2026-07-24废弃 | 已映射到v4-flash（非推理模式） |
| `deepseek-reasoner` | ⚠️ 2026-07-24废弃 | 已映射到v4-flash（推理模式） |

**模型特性**:
- 上下文窗口: 1M tokens
- 最大输出: 384K tokens
- 支持功能: 工具调用、JSON输出、流式响应、推理模式

### 1.5 定价

**官方定价** (USD/百万tokens):

| 模型 | 输入(缓存命中) | 输入(缓存未命中) | 输出 |
|------|---------------|----------------|------|
| **deepseek-v4-flash** | $0.0028 | $0.14 | $0.28 |
| **deepseek-v4-pro** | $0.003625 | $0.435 | $0.87 |

**人民币参考价** (汇率1:7.2):

| 模型 | 输入价格 | 输出价格 | 备注 |
|------|---------|---------|------|
| **deepseek-v4-flash** | ¥1.01/M | ¥2.02/M | 缓存命中可节省98% |
| **deepseek-v4-pro** | ¥3.13/M | ¥6.26/M | 缓存命中可节省99.2% |

**缓存机制**: Prompt缓存命中时，输入成本大幅降低（flash降至$0.0028/M, pro降至$0.003625/M）

### 1.6 Python SDK 安装

```bash
pip install openai
```

### 1.7 完整代码示例

#### 基础对话（非流式）

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "你是一个有帮助的AI助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
print(f"Token使用: {response.usage.total_tokens}")
```

#### 流式对话

```python
stream = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "写一首关于草原的诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### 推理模式（Thinking Mode）

```python
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": "解释量子纠缠"}],
    reasoning_effort="high",  # low/medium/high
    extra_body={"thinking": {"type": "enabled"}}
)

# 访问推理过程
print("推理过程:", response.choices[0].message.reasoning_content)
print("最终回答:", response.choices[0].message.content)
```

#### 工具调用（Function Calling）

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "北京天气怎么样？"}],
    tools=tools
)

# 处理工具调用
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = tool_call.function.arguments
    print(f"调用函数: {function_name}, 参数: {arguments}")
```

### 1.8 cURL 示例

```bash
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [
      {"role": "system", "content": "你是一个草原文化专家"},
      {"role": "user", "content": "介绍内蒙古那达慕"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### 1.9 错误处理

```python
from openai import APIError, RateLimitError, AuthenticationError

try:
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "测试"}]
    )
except AuthenticationError:
    print("API Key无效，检查环境变量")
except RateLimitError:
    print("请求频率超限，实施退避重试")
except APIError as e:
    print(f"API错误: {e.status_code} - {e.message}")
```

**常见错误码**:

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| 401 | 认证失败 | 检查API Key是否正确 |
| 429 | 速率限制 | 实施指数退避重试 |
| 500 | 服务器错误 | 稍后重试 |
| 503 | 服务暂不可用 | 检查服务状态页面 |

### 1.10 限流说明

**并发限制**:
- **deepseek-v4-flash**: 2500 并发请求
- **deepseek-v4-pro**: 500 并发请求

**速率限制**: 根据账户等级动态调整，超限返回429错误

**重试策略**:
```python
import time
from openai import RateLimitError

def call_with_retry(client, max_retries=3):
    for i in range(max_retries):
        try:
            return client.chat.completions.create(...)
        except RateLimitError:
            if i == max_retries - 1:
                raise
            wait_time = 2 ** i  # 指数退避: 1s, 2s, 4s
            time.sleep(wait_time)
```

### 1.11 最佳实践

1. **成本优化**:
   - 优先使用 `deepseek-v4-flash`（成本仅为pro的1/3）
   - 启用Prompt缓存，命中可节省98%成本
   - 合理设置 `max_tokens` 避免浪费
   - 对简单问答使用模板回复，降低LLM调用

2. **性能优化**:
   - 使用流式响应(`stream=True`)提升用户体验
   - 实施请求队列，控制并发不超过限制
   - 缓存高频问题的响应（Redis, 1小时TTL）

3. **Prompt工程**:
   - 系统提示词放在 `system` role，保持稳定以利用缓存
   - 明确指定输出格式（如JSON Schema）
   - 中文任务性能优异，无需英文翻译
   - Thinking Mode适用于复杂推理场景（数学、逻辑）

4. **集成建议**:
   - 使用官方 `openai` Python包（完全兼容）
   - 环境变量管理API Key，不硬编码
   - 实施降级策略：DeepSeek → Claude（高可用）
   - 记录Token使用量，监控成本

---

## 二、火山引擎即梦AI接入指南

### 2.1 概述

**官方文档**: https://www.volcengine.com/docs/85621/1756900  
**产品**: 火山引擎视觉智能 - 即梦AI  
**能力**: 
- 文生图3.1（jimeng_t2i_v31）
- 图生图3.0（jimeng_i2i_v30）

### 2.2 认证方式

**签名机制**: 火山引擎OpenAPI签名v4  
**详细文档**: https://www.volcengine.com/docs/6369/67268

**固定参数**:
- Region: `cn-north-1`
- Service: `cv`

### 2.3 请求配置

**Base URL**: `https://visual.volcengineapi.com`  
**请求方式**: POST  
**Content-Type**: `application/json`

### 2.4 文生图3.1 API

#### 提交任务

**接口**: `CVSync2AsyncSubmitTask`

**Query参数**:
```
https://visual.volcengineapi.com?Action=CVSync2AsyncSubmitTask&Version=2022-08-31
```

**Body参数**:
```json
{
  "req_key": "jimeng_t2i_v31",
  "prompt": "内蒙古草原上的羊群，夕阳金黄",
  "use_pre_llm": true,
  "seed": -1,
  "width": 1328,
  "height": 1328
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| req_key | string | ✅ | 固定值: `jimeng_t2i_v31` |
| prompt | string | ✅ | 提示词，建议≤120字符，最长800字符 |
| use_pre_llm | bool | ❌ | 文本扩写，短prompt建议开启，默认true |
| seed | int | ❌ | 随机种子，-1为随机，默认-1 |
| width | int | ❌ | 宽度，默认1328 |
| height | int | ❌ | 高度，默认1328 |

**支持分辨率**:
- 标清1K: 1328×1328, 1472×1104, 1584×1056, 1664×936, 2016×864
- 高清2K: 2048×2048, 2304×1728, 2496×1664, 2560×1440, 3024×1296

**约束**:
- 宽高比: 1:3 ~ 3:1
- 像素乘积: [512×512, 2048×2048]

**返回示例**:
```json
{
  "code": 10000,
  "data": {
    "task_id": "7392616336519610409"
  },
  "message": "Success",
  "request_id": "20240720103939AF0029465CF6A74E51EC"
}
```

#### 查询任务

**接口**: `CVSync2AsyncGetResult`

**Query参数**:
```
https://visual.volcengineapi.com?Action=CVSync2AsyncGetResult&Version=2022-08-31
```

**Body参数**:
```json
{
  "req_key": "jimeng_t2i_v31",
  "task_id": "7392616336519610409",
  "req_json": "{\"return_url\":true,\"logo_info\":{\"add_logo\":false}}"
}
```

**返回示例**:
```json
{
  "code": 10000,
  "data": {
    "status": "done",
    "image_urls": ["https://xxxx"],
    "binary_data_base64": null
  },
  "message": "Success"
}
```

**任务状态**:
- `in_queue`: 已提交
- `generating`: 处理中
- `done`: 完成（根据code判断成功/失败）
- `not_found`: 任务未找到
- `expired`: 任务过期（12小时）

### 2.5 图生图3.0 API

#### 提交任务

**接口**: `CVSync2AsyncSubmitTask`

**Body参数**:
```json
{
  "req_key": "jimeng_i2i_v30",
  "image_urls": ["https://example.com/input.jpg"],
  "prompt": "背景换成演唱会现场",
  "seed": -1,
  "scale": 0.5,
  "width": 1328,
  "height": 1328
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| req_key | string | ✅ | 固定值: `jimeng_i2i_v30` |
| image_urls | array | ✅二选一 | 输入图片URL（1张） |
| binary_data_base64 | array | ✅二选一 | 输入图片base64（1张） |
| prompt | string | ✅ | 编辑指令，建议≤120字符 |
| seed | int | ❌ | 随机种子，默认-1 |
| scale | float | ❌ | 编辑强度，范围[0,1]，默认0.5 |
| width | int | ❌ | 输出宽度，范围[512,2016] |
| height | int | ❌ | 输出高度，范围[512,2016] |

**输入图片要求**:
- 格式: JPEG/PNG（推荐JPEG）
- 大小: 最大4.7MB
- 分辨率: 最大4096×4096
- 长短边比例: ≤3:1

**输出图片说明**:
- 范围: [512, 1536]
- 实际宽高为最接近16整数倍的值

**Prompt编写建议**:
- 设计场景加"海报、平面设计"增强效果
- 文字用引号标注提升准确率（如："Merry Christmas"）
- 使用自然语言，单指令优先
- 局部编辑时描述精准（如"删除图上的女孩"）
- 效果不明显时调整scale值

**示例指令**:
- 添加/删除实体: "添加一道彩虹" / "删除图上的女孩"
- 修改实体: "把手里的鸡腿变成汉堡"
- 修改风格: "改成漫画风格"
- 修改色彩: "把衣服改成粉色的"
- 修改动作: "让他笑"
- 修改背景: "背景换成海边"

#### 查询任务

与文生图相同，使用`CVSync2AsyncGetResult`接口，`req_key`改为`jimeng_i2i_v30`

### 2.6 Python SDK示例（官方）

**安装**:
```bash
pip install volcengine-python-sdk
```

**文生图示例**:
```python
import json
from volcengine.visual.VisualService import VisualService

# 初始化
service = VisualService()
service.set_ak('your_access_key')
service.set_sk('your_secret_key')

# 提交任务
submit_params = {
    'req_key': 'jimeng_t2i_v31',
    'prompt': '内蒙古草原，夕阳金黄',
    'seed': -1,
    'width': 1328,
    'height': 1328
}

resp = service.cv_sync2_async_submit_task('CVSync2AsyncSubmitTask', submit_params)
result = json.loads(resp)
task_id = result['data']['task_id']

# 查询结果
query_params = {
    'req_key': 'jimeng_t2i_v31',
    'task_id': task_id,
    'req_json': json.dumps({
        'return_url': True,
        'logo_info': {
            'add_logo': False
        }
    })
}

resp = service.cv_sync2_async_get_result('CVSync2AsyncGetResult', query_params)
result = json.loads(resp)

if result['code'] == 10000 and result['data']['status'] == 'done':
    image_urls = result['data']['image_urls']
    print(f"生成成功: {image_urls}")
```

**图生图示例**:
```python
import base64

# 读取本地图片为base64
with open('input.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

submit_params = {
    'req_key': 'jimeng_i2i_v30',
    'binary_data_base64': [image_base64],
    'prompt': '背景换成星空',
    'scale': 0.5
}

resp = service.cv_sync2_async_submit_task('CVSync2AsyncSubmitTask', submit_params)
# ... 后续查询同上
```

### 2.7 错误码

| HttpCode | 错误码 | 说明 | 是否重试 |
|----------|--------|------|---------|
| 200 | 10000 | 成功 | ❌ |
| 400 | 50411 | 输入图片审核未通过 | ❌ |
| 400 | 50412 | 输入文本审核未通过 | ❌ |
| 400 | 50413 | 输入文本含敏感词 | ❌ |
| 400 | 50511 | 输出图片审核未通过 | ✅ |
| 400 | 50518 | 输入版权图未通过 | ❌ |
| 400 | 50519 | 输出版权图未通过 | ✅ |
| 429 | 50429 | QPS超限 | ✅ |
| 429 | 50430 | 并发超限 | ✅ |
| 500 | 50500 | 内部错误 | ❌ |

### 2.8 定价

**实际定价**: ¥0.2/张（以火山引擎官方计费为准）

### 2.9 最佳实践

1. **Prompt优化**:
   - 文生图: 明确风格、场景、元素（如"蒙古包、马群、草原"）
   - 图生图: 使用自然语言单指令，局部编辑描述精准

2. **成本控制**:
   - 优先生成1K分辨率，特殊需求用2K
   - 实现Redis缓存（相似prompt复用结果）
   - 设置用户配额限制

3. **性能优化**:
   - 异步任务队列（Celery）
   - 轮询间隔5-10秒
   - 图片上传MinIO后返回CDN地址

### 2.10 视频生成3.0 Pro API

#### 提交任务

**接口**: `CVSync2AsyncSubmitTask`

**Body参数**:
```json
{
  "req_key": "jimeng_ti2v_v30_pro",
  "prompt": "内蒙古草原上的马群奔跑，蓝天白云",
  "seed": -1,
  "frames": 121,
  "aspect_ratio": "16:9"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| req_key | string | ✅ | 固定值: `jimeng_ti2v_v30_pro` |
| prompt | string | 文生视频必选 | 提示词，建议≤400字，最长800字 |
| binary_data_base64 | array | 图生视频可选 | 首帧图片base64（1张） |
| image_urls | array | 图生视频可选 | 首帧图片URL（1张） |
| seed | int | ❌ | 随机种子，默认-1 |
| frames | int | ❌ | 总帧数，121(5秒)或241(10秒)，默认121 |
| aspect_ratio | string | ❌ | 宽高比，默认"16:9" |

**支持宽高比**:
- 21:9 (2176×928)
- 16:9 (1920×1088)
- 4:3 (1664×1248)
- 1:1 (1440×1440)
- 3:4 (1248×1664)
- 9:16 (1088×1920)

**图片要求**（图生视频）:
- 格式: JPEG/PNG
- 大小: 最大4.7MB
- 分辨率: 最大4096×4096，最短边≥320
- 长短边比例: ≤3:1

**图片裁剪规则**: 输入图片与目标宽高比不一致时，系统自动居中裁剪

#### 查询任务

**Body参数**:
```json
{
  "req_key": "jimeng_ti2v_v30_pro",
  "task_id": "7491596536074305586",
  "req_json": "{\"aigc_meta\":{\"content_producer\":\"xxx\",\"producer_id\":\"xxx\"}}"
}
```

**返回示例**:
```json
{
  "code": 10000,
  "data": {
    "status": "done",
    "video_url": "https://xxxx",
    "aigc_meta_tagged": true
  },
  "message": "Success"
}
```

**注意**: 视频URL有效期仅1小时，需及时下载到MinIO

#### Python SDK示例

```python
import json
from volcengine.visual.VisualService import VisualService

service = VisualService()
service.set_ak('your_access_key')
service.set_sk('your_secret_key')

# 文生视频
submit_params = {
    'req_key': 'jimeng_ti2v_v30_pro',
    'prompt': '内蒙古草原，骏马奔驰，蓝天白云',
    'seed': -1,
    'frames': 121,  # 5秒
    'aspect_ratio': '16:9'
}

resp = service.cv_sync2_async_submit_task('CVSync2AsyncSubmitTask', submit_params)
result = json.loads(resp)
task_id = result['data']['task_id']

# 轮询结果（视频生成需要3-10分钟）
import time
for _ in range(120):  # 最多等待10分钟
    time.sleep(5)
    
    query_params = {
        'req_key': 'jimeng_ti2v_v30_pro',
        'task_id': task_id
    }
    
    resp = service.cv_sync2_async_get_result('CVSync2AsyncGetResult', query_params)
    result = json.loads(resp)
    
    if result['code'] == 10000:
        status = result['data']['status']
        if status == 'done':
            video_url = result['data']['video_url']
            print(f"视频生成成功: {video_url}")
            break
        elif status in ['not_found', 'expired']:
            print(f"任务异常: {status}")
            break
```

**定价**: ¥1/秒（5秒视频=¥5，10秒视频=¥10）

---

## 三、项目集成方案

### 3.1 统一AI管理层架构

```python
# backend/app/services/ai/providers/volcengine_provider.py

import json
import base64
import asyncio
from volcengine.visual.VisualService import VisualService
from typing import Dict, Optional

class VolcengineProvider:
    """火山引擎即梦AI Provider"""
    
    def __init__(self, access_key: str, secret_key: str):
        self.service = VisualService()
        self.service.set_ak(access_key)
        self.service.set_sk(secret_key)
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1328,
        height: int = 1328,
        **kwargs
    ) -> Dict:
        """文生图3.1"""
        submit_params = {
            'req_key': 'jimeng_t2i_v31',
            'prompt': prompt,
            'seed': kwargs.get('seed', -1),
            'width': width,
            'height': height,
            'use_pre_llm': kwargs.get('use_pre_llm', True)
        }
        
        resp = self.service.cv_sync2_async_submit_task(
            'CVSync2AsyncSubmitTask',
            submit_params
        )
        result = json.loads(resp)
        
        if result['code'] != 10000:
            raise Exception(f"任务提交失败: {result['message']}")
        
        task_id = result['data']['task_id']
        
        # 轮询结果
        for _ in range(60):
            await asyncio.sleep(5)
            
            query_params = {
                'req_key': 'jimeng_t2i_v31',
                'task_id': task_id,
                'req_json': json.dumps({'return_url': True})
            }
            
            resp = self.service.cv_sync2_async_get_result(
                'CVSync2AsyncGetResult',
                query_params
            )
            result = json.loads(resp)
            
            if result['code'] != 10000:
                raise Exception(f"查询失败: {result['message']}")
            
            status = result['data']['status']
            
            if status == 'done':
                return {
                    'image_url': result['data']['image_urls'][0],
                    'cost': 0.2
                }
            elif status in ['not_found', 'expired']:
                raise Exception(f"任务异常: {status}")
        
        raise TimeoutError("图片生成超时")
    
    async def edit_image(
        self,
        image_path: str,
        prompt: str,
        scale: float = 0.5,
        **kwargs
    ) -> Dict:
        """图生图3.0"""
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        submit_params = {
            'req_key': 'jimeng_i2i_v30',
            'binary_data_base64': [image_base64],
            'prompt': prompt,
            'seed': kwargs.get('seed', -1),
            'scale': scale,
            'width': kwargs.get('width', 1328),
            'height': kwargs.get('height', 1328)
        }
        
        resp = self.service.cv_sync2_async_submit_task(
            'CVSync2AsyncSubmitTask',
            submit_params
        )
        result = json.loads(resp)
        
        if result['code'] != 10000:
            raise Exception(f"任务提交失败: {result['message']}")
        
        task_id = result['data']['task_id']
        
        # 轮询结果（同文生图）
        return await self._poll_result('jimeng_i2i_v30', task_id)
    
    async def generate_video(
        self,
        prompt: str,
        frames: int = 121,
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> Dict:
        """文生视频3.0 Pro"""
        submit_params = {
            'req_key': 'jimeng_ti2v_v30_pro',
            'prompt': prompt,
            'seed': kwargs.get('seed', -1),
            'frames': frames,
            'aspect_ratio': aspect_ratio
        }
        
        # 如果有首帧图片（图生视频）
        if image_path := kwargs.get('image_path'):
            with open(image_path, 'rb') as f:
                submit_params['binary_data_base64'] = [
                    base64.b64encode(f.read()).decode('utf-8')
                ]
        
        resp = self.service.cv_sync2_async_submit_task(
            'CVSync2AsyncSubmitTask',
            submit_params
        )
        result = json.loads(resp)
        
        if result['code'] != 10000:
            raise Exception(f"任务提交失败: {result['message']}")
        
        task_id = result['data']['task_id']
        
        # 轮询结果（视频生成需要3-10分钟）
        for _ in range(120):
            await asyncio.sleep(5)
            
            query_params = {
                'req_key': 'jimeng_ti2v_v30_pro',
                'task_id': task_id
            }
            
            resp = self.service.cv_sync2_async_get_result(
                'CVSync2AsyncGetResult',
                query_params
            )
            result = json.loads(resp)
            
            if result['code'] != 10000:
                raise Exception(f"查询失败: {result['message']}")
            
            status = result['data']['status']
            
            if status == 'done':
                video_url = result['data']['video_url']
                # 视频URL有效期1小时，需立即下载
                return {
                    'video_url': video_url,
                    'cost': frames / 24  # ¥1/秒
                }
            elif status in ['not_found', 'expired']:
                raise Exception(f"任务异常: {status}")
        
        raise TimeoutError("视频生成超时")
    
    async def _poll_result(self, req_key: str, task_id: str) -> Dict:
        """统一轮询逻辑"""
        for _ in range(60):
            await asyncio.sleep(5)
            
            query_params = {
                'req_key': req_key,
                'task_id': task_id,
                'req_json': json.dumps({'return_url': True})
            }
            
            resp = self.service.cv_sync2_async_get_result(
                'CVSync2AsyncGetResult',
                query_params
            )
            result = json.loads(resp)
            
            if result['code'] != 10000:
                raise Exception(f"查询失败: {result['message']}")
            
            status = result['data']['status']
            
            if status == 'done':
                return {
                    'image_url': result['data'].get('image_urls', [None])[0],
                    'cost': 0.2
                }
            elif status in ['not_found', 'expired']:
                raise Exception(f"任务异常: {status}")
        
        raise TimeoutError("生成超时")
```

### 3.2 DeepSeek Provider 实现

```python
# backend/app/services/ai/providers/deepseek_provider.py

from openai import AsyncOpenAI
from typing import List, Dict, Optional
import os

class DeepSeekProvider:
    """DeepSeek LLM Provider"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-flash"
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """对话接口"""
        response = await self.client.chat.completions.create(
            model=kwargs.get('model', self.model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            return response  # 返回流对象
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model
        }
    
    async def chat_with_thinking(
        self,
        messages: List[Dict[str, str]],
        reasoning_effort: str = "high"
    ) -> Dict:
        """推理模式对话"""
        response = await self.client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=messages,
            reasoning_effort=reasoning_effort,
            extra_body={"thinking": {"type": "enabled"}}
        )
        
        return {
            "content": response.choices[0].message.content,
            "reasoning_content": response.choices[0].message.reasoning_content,
            "usage": response.usage.dict()
        }

### 3.3 统一AI管理器

```python
# backend/app/services/ai/manager.py

from typing import Dict, List, Optional
from .providers.deepseek_provider import DeepSeekProvider
from .providers.volcengine_provider import VolcengineProvider

class AIProviderManager:
    """统一AI服务商管理器"""
    
    def __init__(self):
        self.deepseek = None
        self.volcengine = None
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有Provider"""
        from app.core.config import settings
        
        # DeepSeek
        if settings.DEEPSEEK_API_KEY:
            self.deepseek = DeepSeekProvider(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model=settings.DEEPSEEK_MODEL
            )
        
        # 火山引擎
        if settings.VOLCENGINE_ACCESS_KEY and settings.VOLCENGINE_SECRET_KEY:
            self.volcengine = VolcengineProvider(
                access_key=settings.VOLCENGINE_ACCESS_KEY,
                secret_key=settings.VOLCENGINE_SECRET_KEY
            )
    
    async def chat(
        self,
        messages: List[Dict],
        provider: str = "deepseek",
        **kwargs
    ) -> Dict:
        """统一对话接口（带降级）"""
        if provider == "deepseek" and self.deepseek:
            try:
                return await self.deepseek.chat(messages, **kwargs)
            except Exception as e:
                # 降级到Claude（如果配置）
                if self.claude:
                    return await self.claude.chat(messages, **kwargs)
                raise e
        
        raise ValueError(f"Provider {provider} not available")
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        """生成图片"""
        if not self.volcengine:
            raise ValueError("Volcengine not configured")
        return await self.volcengine.generate_image(prompt, **kwargs)
    
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        """生成视频"""
        if not self.volcengine:
            raise ValueError("Volcengine not configured")
        return await self.volcengine.generate_video(prompt, **kwargs)

# 全局单例
ai_manager = AIProviderManager()
```

### 3.4 环境变量配置

```bash
# .env

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# 火山引擎配置
VOLCENGINE_ACCESS_KEY=your_access_key
VOLCENGINE_SECRET_KEY=your_secret_key

# 加密密钥（AES-256）
SECRET_KEY=your-secret-key-for-encryption
```

### 3.3 FastAPI端点示例

```python
# backend/app/api/v1/media.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.services.ai.providers.volcengine_provider import VolcengineProvider

router = APIRouter()

@router.post("/generate-image")
async def generate_image(
    request: ImageGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """生成产品营销图片"""
    # 1. 检查配额
    await check_quota(current_user["user_id"], "image_generation")
    
    # 2. 获取Provider
    from app.core.config import settings
    provider = VolcengineProvider(
        access_key=settings.VOLCENGINE_ACCESS_KEY,
        secret_key=settings.VOLCENGINE_SECRET_KEY
    )
    
    # 3. 增强Prompt（融合草原文化）
    enhanced_prompt = await enhance_prompt_with_culture(
        request.prompt,
        request.product_id
    )
    
    # 4. 生成图片
    result = await provider.generate_image(
        prompt=enhanced_prompt,
        width=request.width or 1328,
        height=request.height or 1328
    )
    
    # 5. 上传到MinIO
    from app.services.storage.minio_service import upload_from_url
    local_url = await upload_from_url(
        result["image_url"],
        bucket="marketing-images"
    )
    
    # 6. 记录成本
    await log_media_cost(
        user_id=current_user["user_id"],
        media_type="image",
        cost=result["cost"],
        provider="volcengine"
    )
    
    return {
        "image_url": local_url,
        "prompt": enhanced_prompt,
        "cost": result["cost"]
    }
```

### 3.5 FastAPI端点示例

```python
# backend/app/api/v1/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.services.ai.manager import ai_manager

router = APIRouter()

@router.post("/chat")
async def chat_with_ip(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """IP智能体对话（小数/小商）"""
    # 1. 检查配额
    await check_quota(current_user["user_id"], "chat")
    
    # 2. 构建System Prompt（根据IP类型）
    system_prompt = get_ip_system_prompt(request.ip_type)  # xiaoshu/xiaoshang
    
    messages = [
        {"role": "system", "content": system_prompt},
        *request.messages
    ]
    
    # 3. 调用DeepSeek（带降级）
    try:
        result = await ai_manager.chat(
            messages=messages,
            provider="deepseek",
            temperature=0.7,
            max_tokens=2000
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务异常: {str(e)}")
    
    # 4. 记录成本
    await log_token_usage(
        user_id=current_user["user_id"],
        provider="deepseek",
        usage=result["usage"]
    )
    
    return {
        "message": result["content"],
        "usage": result["usage"]
    }


# backend/app/api/v1/media.py

@router.post("/generate-image")
async def generate_image(
    request: ImageGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """生成产品营销图片"""
    # 1. 检查配额
    await check_quota(current_user["user_id"], "image_generation")
    
    # 2. 增强Prompt（融合草原文化）
    enhanced_prompt = await enhance_prompt_with_culture(
        request.prompt,
        request.product_id
    )
    
    # 3. 生成图片
    try:
        result = await ai_manager.generate_image(
            prompt=enhanced_prompt,
            width=request.width or 1328,
            height=request.height or 1328
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")
    
    # 4. 上传到MinIO
    from app.services.storage.minio_service import upload_from_url
    local_url = await upload_from_url(
        result["image_url"],
        bucket="marketing-images"
    )
    
    # 5. 记录成本
    await log_media_cost(
        user_id=current_user["user_id"],
        media_type="image",
        cost=result["cost"],
        provider="volcengine"
    )
    
    return {
        "image_url": local_url,
        "prompt": enhanced_prompt,
        "cost": result["cost"]
    }


@router.post("/generate-video")
async def generate_video(
    request: VideoGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """生成产品宣传视频"""
    # 1. 检查配额
    await check_quota(current_user["user_id"], "video_generation")
    
    # 2. 提交异步任务
    try:
        result = await ai_manager.generate_video(
            prompt=request.prompt,
            frames=request.frames or 121,
            aspect_ratio=request.aspect_ratio or "16:9"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")
    
    return {
        "task_id": result["task_id"],
        "status": "processing",
        "estimated_time": "3-10分钟"
    }


@router.get("/video-task/{task_id}")
async def get_video_task(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """查询视频生成任务状态"""
    result = await ai_manager.volcengine.query_video_task(task_id)
    
    if result["status"] == "done":
        # 上传到MinIO（视频URL仅1小时有效）
        local_url = await upload_from_url(
            result["video_url"],
            bucket="marketing-videos"
        )
        result["video_url"] = local_url
    
    return result
```

### 3.6 数据库迁移脚本

```python
# backend/alembic/versions/xxx_add_volcengine_config.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 插入火山引擎配置
    op.execute("""
        INSERT INTO ai_provider_configs 
        (provider, provider_type, api_key_encrypted, api_endpoint, model_name, priority)
        VALUES
        ('volcengine', 'image', 'ENCRYPTED_AK_SK', 'https://visual.volcengineapi.com', 'jimeng_t2i_v31', 1);
    """)
```

---

## 四、测试与验证

### 4.1 DeepSeek连接测试

```python
# tests/test_deepseek.py

import pytest
from openai import OpenAI

def test_deepseek_basic():
    client = OpenAI(
        api_key="sk-test-key",
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0
```

### 4.2 火山引擎图像生成测试

```python
# tests/test_volcengine.py

import json
from volcengine.visual.VisualService import VisualService

def test_volcengine_text_to_image():
    service = VisualService()
    service.set_ak('test_ak')
    service.set_sk('test_sk')
    
    # 提交任务
    params = {
        'req_key': 'jimeng_t2i_v31',
        'prompt': '测试图片',
        'width': 1328,
        'height': 1328
    }
    
    resp = service.cv_sync2_async_submit_task('CVSync2AsyncSubmitTask', params)
    result = json.loads(resp)
    
    assert result['code'] == 10000
    assert 'task_id' in result['data']
```

---

## 五、常见问题（FAQ）

### 5.1 DeepSeek相关

**Q: 如何降低成本？**  
A: ① 优先使用flash模型 ② 启用缓存 ③ 优化Prompt减少Token ④ 设置合理的max_tokens

**Q: 支持哪些语言？**  
A: 中英文均支持，中文能力尤其出色

### 5.2 火山引擎相关

**Q: 图片生成时间？**  
A: 通常5-30秒，复杂场景可能更长

**Q: 如何提升文字准确率？**  
A: 在prompt中用引号标注文字内容（如："Merry Christmas"）

**Q: 图生图效果不明显怎么办？**  
A: 调整scale参数（0-1），值越大编辑强度越大

**Q: 任务过期时间？**  
A: 12小时，过期需重新提交

**Q: 图片链接有效期？**  
A: 24小时，建议及时下载到MinIO

---

**文档结束**

> 本文档基于火山引擎官方文档（2026-06-12）整理，涵盖DeepSeek LLM + 火山引擎即梦AI（文生图3.1 + 图生图3.0）的完整接入方案。

```python
# backend/app/services/ai/ai_provider_manager.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

class BaseAIProvider(ABC):
    """AI服务商抽象基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """文本对话"""
        pass
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        """图像生成（可选实现）"""
        pass
    
    @abstractmethod
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        """视频生成（可选实现）"""
        pass


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek LLM Provider"""
    
    def __init__(self, api_key: str, base_url: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        model = kwargs.get("model", "deepseek-v4-flash")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model
        }
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        raise NotImplementedError("DeepSeek不支持图像生成")
    
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        raise NotImplementedError("DeepSeek不支持视频生成")


class VolcengineProvider(BaseAIProvider):
    """火山引擎即梦AI Provider"""
    
    def __init__(self, api_key: str, base_url: str):
        from byteplussdkarkruntime import Ark
        self.client = Ark(api_key=api_key, base_url=base_url)
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        raise NotImplementedError("火山引擎不支持文本对话")
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        size = kwargs.get("size", "2K")
        watermark = kwargs.get("watermark", False)
        
        response = self.client.images.generate(
            model="seedream-4-5-251128",
            prompt=prompt,
            size=size,
            watermark=watermark,
            response_format="url"
        )
        
        return {
            "image_url": response.data[0].url,
            "cost": 0.2  # ¥0.2/张
        }
    
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        duration = kwargs.get("duration", 5)
        resolution = kwargs.get("resolution", "1080p")
        
        # 提交异步任务
        response = self.client.videos.generate(
            model="seedance-2-0",
            prompt=prompt,
            duration=duration,
            resolution=resolution
        )
        
        return {
            "task_id": response.task_id,
            "status": "processing",
            "cost": duration * 1.0  # ¥1/秒
        }


class AIProviderManager:
    """AI服务商统一管理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers: Dict[str, BaseAIProvider] = {}
    
    async def get_provider(self, provider_name: str) -> BaseAIProvider:
        """获取Provider实例（带缓存）"""
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        # 从数据库加载配置
        from app.models import AIProviderConfig
        config = await self.db.query(AIProviderConfig).filter_by(
            provider=provider_name,
            is_active=True
        ).first()
        
        if not config:
            raise ValueError(f"Provider {provider_name} 未配置或未激活")
        
        # 实例化Provider
        if provider_name == "deepseek":
            self.providers[provider_name] = DeepSeekProvider(
                api_key=config.api_key_decrypted,  # 需解密
                base_url=config.api_endpoint
            )
        elif provider_name == "volcengine":
            self.providers[provider_name] = VolcengineProvider(
                api_key=config.api_key_decrypted,
                base_url=config.api_endpoint
            )
        
        return self.providers[provider_name]
    
    async def chat_with_fallback(self, messages: List[Dict], **kwargs) -> Dict:
        """带降级的对话接口"""
        from app.models import AIProviderConfig
        
        # 按优先级获取所有活跃的LLM Provider
        configs = await self.db.query(AIProviderConfig).filter_by(
            provider_type="llm",
            is_active=True
        ).order_by(AIProviderConfig.priority).all()
        
        last_error = None
        for config in configs:
            try:
                provider = await self.get_provider(config.provider)
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                print(f"Provider {config.provider} 失败: {e}")
                last_error = e
                continue
        
        raise Exception(f"所有LLM Provider均失败: {last_error}")
```

### 4.2 环境变量配置

```bash
# .env

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# 火山引擎配置
VOLCENGINE_API_KEY=your_ark_api_key
VOLCENGINE_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# 加密密钥（AES-256）
SECRET_KEY=your-secret-key-for-encryption
```

### 4.3 FastAPI端点示例

```python
# backend/app/api/v1/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.services.ai.ai_provider_manager import AIProviderManager

router = APIRouter()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """IP智能体对话"""
    manager = AIProviderManager(db)
    
    # 构建消息
    messages = [
        {"role": "system", "content": get_system_prompt(request.ip_type)},
        *request.messages
    ]
    
    # 调用LLM（自动降级）
    try:
        response = await manager.chat_with_fallback(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        # 记录Token使用
        await log_token_usage(
            user_id=current_user["user_id"],
            provider="deepseek",
            usage=response["usage"]
        )
        
        return {
            "content": response["content"],
            "model": response["model"],
            "usage": response["usage"]
        }
    except Exception as e:
        raise HTTPException(500, f"对话失败: {str(e)}")


# backend/app/api/v1/media.py

@router.post("/generate-image")
async def generate_image(
    request: ImageGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """生成产品营销图片"""
    manager = AIProviderManager(db)
    provider = await manager.get_provider("volcengine")
    
    # 增强Prompt（融合草原文化）
    enhanced_prompt = await enhance_prompt_with_culture(
        request.prompt,
        request.product_id
    )
    
    # 生成图片
    result = await provider.generate_image(
        prompt=enhanced_prompt,
        size=request.size
    )
    
    # 上传到MinIO
    from app.services.storage.minio_service import upload_from_url
    local_url = await upload_from_url(
        result["image_url"],
        bucket="marketing-images"
    )
    
    # 记录成本
    await log_media_cost(
        user_id=current_user["user_id"],
        media_type="image",
        cost=result["cost"]
    )
    
    return {
        "image_url": local_url,
        "prompt": enhanced_prompt,
        "cost": result["cost"]
    }
```

### 4.4 数据库迁移脚本

```python
# backend/alembic/versions/xxx_add_ai_provider_tables.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 创建ai_provider_configs表
    op.create_table(
        'ai_provider_configs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('provider', sa.String(50), nullable=False, unique=True),
        sa.Column('provider_type', sa.String(20), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('api_endpoint', sa.String(500)),
        sa.Column('model_name', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('config_json', sa.JSON()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now())
    )
    
    # 插入默认配置
    op.execute("""
        INSERT INTO ai_provider_configs 
        (provider, provider_type, api_key_encrypted, api_endpoint, model_name, priority)
        VALUES
        ('deepseek', 'llm', 'ENCRYPTED_KEY_1', 'https://api.deepseek.com', 'deepseek-v4-flash', 1),
        ('volcengine', 'image', 'ENCRYPTED_KEY_2', 'https://ark.ap-southeast.bytepluses.com/api/v3', 'seedream-4-5-251128', 1);
    """)
```

---

## 五、测试与验证

### 5.1 DeepSeek连接测试

```python
# tests/test_deepseek.py

import pytest
from openai import OpenAI

def test_deepseek_basic():
    client = OpenAI(
        api_key="sk-test-key",
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "你好"}]
    )
    
    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0
```

### 5.2 火山引擎图像生成测试

```python
# tests/test_volcengine.py

def test_seedream_image_generation():
    from byteplussdkarkruntime import Ark
    
    client = Ark(
        base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
        api_key="test-key"
    )
    
    response = client.images.generate(
        model="seedream-4-5-251128",
        prompt="测试图片生成",
        size="2K",
        watermark=False
    )
    
    assert response.data[0].url.startswith("http")
```

---

## 六、常见问题（FAQ）

### 6.1 DeepSeek相关

**Q: 如何降低成本？**  
A: ① 优先使用flash模型 ② 启用缓存 ③ 优化Prompt减少Token ④ 设置合理的max_tokens

**Q: 支持哪些语言？**  
A: 中英文均支持，中文能力尤其出色

**Q: 如何启用推理模式？**  
A: 设置 `reasoning_effort="high"` 和 `extra_body={"thinking": {"type": "enabled"}}`

### 6.2 火山引擎相关

**Q: 图片生成时间？**  
A: 2K图片约5-15秒，4K约15-30秒

**Q: 支持哪些图片格式？**  
A: 输入支持JPG/PNG/WebP，输出为PNG

**Q: 如何避免生成违规内容？**  
A: Prompt中明确描述合规内容，避免敏感词汇

**Q: 视频生成API是否已发布？**  
A: Seedance 2.0视频生成能力存在，但API细节需参考官方最新文档

---

**文档结束**

> 本文档涵盖DeepSeek LLM + 火山引擎即梦AI的完整接入方案，包含认证、代码示例、成本优化、项目集成架构。

