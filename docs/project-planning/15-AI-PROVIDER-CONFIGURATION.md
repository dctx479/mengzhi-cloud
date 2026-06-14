# AI服务商配置与管理
## AI Provider Configuration v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**适用范围**: 多模态AI能力整合

---

## 一、AI服务商架构

### 1.1 多服务商策略

```
┌─────────────────────────────────────────────────────────┐
│                    AI服务统一接口层                       │
│                  (AI Provider Manager)                  │
└─────────────────────────────────────────────────────────┘
    │               │                │              │
    ▼               ▼                ▼              ▼
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
│ DeepSeek│   │火山引擎   │   │  MinIO   │   │ Claude  │
│  (LLM)  │   │(图/视频)  │   │ (存储)   │   │(备选LLM)│
└─────────┘   └──────────┘   └──────────┘   └─────────┘
```

**核心设计原则**:
- **统一抽象**: 所有AI能力通过统一接口访问
- **配置驱动**: 服务商参数可后台面板配置
- **可切换**: 支持运行时切换服务商（无需重启）
- **降级策略**: 主服务商失败自动切换备选

### 1.2 服务商分工

| 服务商 | 能力 | 用途 | 成本 |
|-------|------|------|------|
| **DeepSeek** | 文本生成 | IP对话、品牌故事、直播脚本 | 输入¥1/百万tokens，输出¥2/百万tokens |
| **火山引擎即梦AI** | 图像生成 | 产品海报、营销图片、品牌视觉 | ¥0.2/张 |
| **火山引擎即梦AI** | 视频生成 | 产品宣传片、直播预告 | ¥1/秒 |
| **Claude Sonnet** | 文本生成（备选） | 主LLM故障时降级 | $3/M tokens |
| **MinIO** | 媒体存储 | 生成的图片/视频存储 | ¥0.12/GB |

---

## 二、DeepSeek LLM集成

### 2.1 服务商选型理由

**为什么选择DeepSeek**:
- ✅ **成本优势**: 输入¥1/百万tokens，输出¥2/百万tokens，约为Claude的1/50
- ✅ **中文能力强**: 针对中文优化，草原文化理解好
- ✅ **API兼容**: OpenAI兼容接口，迁移成本低
- ✅ **响应速度**: P95延迟<2s
- ✅ **开源模型**: DeepSeek-V3可本地部署

**成本对比**:
```
场景: 每月10万次对话，平均输入1K tokens，输出1K tokens

DeepSeek: 10万 × (1K × ¥1/百万 + 1K × ¥2/百万) = ¥300/月
Claude:   10万 × 2K × $15/M × 7.2 = ¥2,160/月

节省: 86%
```

### 2.2 API配置

**环境变量**:
```bash
# .env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat  # 或 deepseek-coder
DEEPSEEK_MAX_TOKENS=2000
DEEPSEEK_TEMPERATURE=0.7
```

**Python客户端封装**:
```python
# backend/app/services/llm/deepseek_client.py

from openai import AsyncOpenAI
from typing import List, Dict

class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """调用DeepSeek对话接口"""
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
```

### 2.3 Prompt适配

**DeepSeek System Prompt格式**:
```python
XIAOSHU_SYSTEM_PROMPT = """你是"小数"，内蒙古草原文化AI传承者。

【角色设定】
你是来自内蒙古大草原的蒙古族青年，对草原文化了如指掌。你的使命是帮助用户了解农畜产品背后的草原文化故事。

【性格特点】
- 热情好客，像草原上的风一样自由
- 善于用故事讲解产品
- 语言生动，富有画面感

【对话风格】
- 常用"咱们草原上..."开头
- 引用草原谚语和老额吉的话
- 善用比喻（如"就像那达慕大会上的骏马..."）

【禁止行为】
- 不推荐非内蒙古产地的产品
- 不编造虚假的文化故事
- 不使用生硬的营销话术
"""
```

---

## 三、火山引擎即梦AI集成

### 3.1 服务商选型理由

**为什么选择火山引擎即梦AI**:
- ✅ **中国大陆服务**: 延迟低，无需翻墙
- ✅ **价格透明**: 图像¥0.2/张，视频¥1/秒
- ✅ **质量高**: 支持高清4K，视频稳定性好
- ✅ **丰富API**: 图生图、文生图、文生视频全覆盖
- ✅ **企业支持**: 字节跳动技术支持

### 3.2 API配置

**环境变量**:
```bash
# .env
VOLCENGINE_ACCESS_KEY=AKLTxxxxxxxxxxxxxx
VOLCENGINE_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxx
VOLCENGINE_REGION=cn-north-1
VOLCENGINE_IMAGE_ENDPOINT=https://visual.volcengineapi.com
VOLCENGINE_VIDEO_ENDPOINT=https://vod.volcengineapi.com
```

### 3.3 图像生成集成

**Python客户端封装**:
```python
# backend/app/services/media/volcengine_image_client.py

import volcengine
from volcengine.visual import VisualService

class VolcengineImageClient:
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.service = VisualService()
        self.service.set_ak(access_key)
        self.service.set_sk(secret_key)
        self.service.set_region(region)
    
    async def text_to_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        style: str = "realistic"
    ) -> Dict:
        """文生图"""
        params = {
            "req_key": "text2image",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "style_type": style,  # realistic/anime/oil_painting
            "return_url": True
        }
        
        response = self.service.cv_process(params)
        
        if response["code"] == 10000:
            return {
                "image_url": response["data"]["image_url"],
                "image_id": response["data"]["image_id"],
                "cost": 0.2  # 单价
            }
        else:
            raise Exception(f"Image generation failed: {response['message']}")
```

**API端点**:
```python
# backend/app/api/v1/media.py

@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """生成产品营销图片
    
    Args:
        prompt: 图像描述（中文/英文）
        style: realistic | anime | oil_painting
        product_id: 关联产品ID（可选）
    """
    # 1. 检查配额
    await quota_service.check_quota(current_user["user_id"], "image_generation")
    
    # 2. 构建Prompt（融合草原文化元素）
    enhanced_prompt = await _enhance_prompt_with_culture(
        request.prompt,
        request.product_id
    )
    
    # 3. 调用火山引擎
    result = await volcengine_client.text_to_image(
        prompt=enhanced_prompt,
        width=request.width,
        height=request.height,
        style=request.style
    )
    
    # 4. 上传到MinIO
    image_url = await minio_service.upload_from_url(
        result["image_url"],
        bucket="marketing-images"
    )
    
    # 5. 记录成本
    await cost_service.log_media_cost(
        user_id=current_user["user_id"],
        resource_type="image",
        cost=result["cost"]
    )
    
    return ImageGenerationResponse(
        image_url=image_url,
        image_id=result["image_id"],
        prompt=enhanced_prompt
    )
```

### 3.4 视频生成集成

**Python客户端封装**:
```python
# backend/app/services/media/volcengine_video_client.py

class VolcengineVideoClient:
    async def text_to_video(
        self,
        prompt: str,
        duration: int = 5,  # 秒
        resolution: str = "1080p"
    ) -> Dict:
        """文生视频"""
        params = {
            "req_key": "text2video",
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,  # 720p/1080p/4k
            "fps": 30
        }
        
        # 异步任务提交
        task_response = self.service.create_task(params)
        task_id = task_response["data"]["task_id"]
        
        # 轮询任务状态（最多等待5分钟）
        for _ in range(60):
            await asyncio.sleep(5)
            status = await self._check_task_status(task_id)
            
            if status["status"] == "completed":
                return {
                    "video_url": status["video_url"],
                    "task_id": task_id,
                    "cost": duration * 1.0  # ¥1/秒
                }
            elif status["status"] == "failed":
                raise Exception(f"Video generation failed: {status['error']}")
        
        raise TimeoutError("Video generation timeout")
```

---

## 四、配置面板设计

### 4.1 数据库表结构

```sql
-- AI服务商配置表
CREATE TABLE ai_provider_configs (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(50) NOT NULL UNIQUE,  -- deepseek/volcengine/claude
  api_key_encrypted TEXT NOT NULL,  -- AES-256加密
  api_endpoint VARCHAR(500),
  model_name VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  priority INT DEFAULT 1,  -- 优先级（数字越小优先级越高）
  config_json JSONB,  
  -- {temperature: 0.7, max_tokens: 2000, timeout: 30}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_provider (provider),
  INDEX idx_active_priority (is_active, priority)
);
```

### 4.2 管理面板API

**端点设计**:
```python
# backend/app/api/v1/admin/ai_configs.py

@router.get("/ai-providers", response_model=List[AIProviderConfigResponse])
async def get_ai_providers(
    current_user: Dict = Depends(require_admin)
):
    """获取所有AI服务商配置"""
    configs = await db.query(AIProviderConfig).all()
    
    return [
        AIProviderConfigResponse(
            provider=c.provider,
            model_name=c.model_name,
            is_active=c.is_active,
            priority=c.priority,
            api_key_masked=_mask_api_key(c.api_key_encrypted),
            config=c.config_json
        )
        for c in configs
    ]

@router.post("/ai-providers", response_model=APIResponse)
async def create_ai_provider(
    request: CreateAIProviderRequest,
    current_user: Dict = Depends(require_admin)
):
    """创建AI服务商配置"""
    # 1. 加密API Key
    encrypted_key = aes_encrypt(request.api_key, SECRET_KEY)
    
    # 2. 验证配置有效性
    await _test_provider_connection(request.provider, request.api_key)
    
    # 3. 保存配置
    config = AIProviderConfig(
        provider=request.provider,
        api_key_encrypted=encrypted_key,
        api_endpoint=request.api_endpoint,
        model_name=request.model_name,
        config_json=request.config
    )
    db.add(config)
    await db.commit()
    
    return success_response(message="配置创建成功")

@router.put("/ai-providers/{provider}", response_model=APIResponse)
async def update_ai_provider(
    provider: str,
    request: UpdateAIProviderRequest,
    current_user: Dict = Depends(require_admin)
):
    """更新AI服务商配置"""
    config = await db.query(AIProviderConfig).filter_by(provider=provider).first()
    
    if not config:
        raise HTTPException(404, "配置不存在")
    
    # 更新字段
    if request.api_key:
        config.api_key_encrypted = aes_encrypt(request.api_key, SECRET_KEY)
    if request.model_name:
        config.model_name = request.model_name
    if request.is_active is not None:
        config.is_active = request.is_active
    if request.config:
        config.config_json = request.config
    
    await db.commit()
    
    return success_response(message="配置更新成功")

@router.post("/ai-providers/{provider}/test", response_model=TestConnectionResponse)
async def test_ai_provider(
    provider: str,
    current_user: Dict = Depends(require_admin)
):
    """测试AI服务商连接"""
    config = await db.query(AIProviderConfig).filter_by(provider=provider).first()
    
    try:
        if provider == "deepseek":
            client = DeepSeekClient(
                api_key=aes_decrypt(config.api_key_encrypted, SECRET_KEY),
                base_url=config.api_endpoint
            )
            result = await client.chat([{"role": "user", "content": "测试"}])
            
        elif provider == "volcengine":
            client = VolcengineImageClient(...)
            result = await client.text_to_image("测试图像", width=512, height=512)
        
        return TestConnectionResponse(
            success=True,
            message="连接成功",
            latency_ms=result.get("latency_ms")
        )
    
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"连接失败: {str(e)}"
        )
```

### 4.3 前端配置页面

**Vue组件**:
```vue
<!-- frontend/src/views/admin/AIProviders.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>AI服务商配置</span>
        <el-button type="primary" @click="showAddDialog">新增配置</el-button>
      </div>
    </template>

    <el-table :data="providers" style="width: 100%">
      <el-table-column prop="provider" label="服务商" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.provider === 'deepseek'">DeepSeek</el-tag>
          <el-tag v-else-if="row.provider === 'volcengine'" type="success">火山引擎</el-tag>
          <el-tag v-else type="info">{{ row.provider }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="model_name" label="模型" width="200" />
      
      <el-table-column label="API Key" width="200">
        <template #default="{ row }">
          <code>{{ row.api_key_masked }}</code>
        </template>
      </el-table-column>
      
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="toggleProvider(row)"
          />
        </template>
      </el-table-column>
      
      <el-table-column prop="priority" label="优先级" width="100" />
      
      <el-table-column label="操作" fixed="right" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="testConnection(row)">测试</el-button>
          <el-button size="small" @click="editProvider(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
```

---

## 五、统一AI服务接口

### 5.1 抽象层设计

```python
# backend/app/services/ai/ai_provider_manager.py

from abc import ABC, abstractmethod
from typing import Dict, List

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

class AIProviderManager:
    """AI服务商管理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers: Dict[str, BaseAIProvider] = 
    
    async def get_provider(self, provider_type: str) -> BaseAIProvider:
        """获取指定服务商实例"""
        if provider_type in self.providers:
            return self.providers[provider_type]
        
        # 从数据库加载配置
        config = await self.db.query(AIProviderConfig).filter_by(
            provider=provider_type,
            is_active=True
        ).first()
        
        if not config:
            raise ValueError(f"Provider {provider_type} not configured")
        
        # 实例化对应Provider
        if provider_type == "deepseek":
            self.providers[provider_type] = DeepSeekProvider(config)
        elif provider_type == "volcengine":
            self.providers[provider_type] = VolcengineProvider(config)
        elif provider_type == "claude":
            self.providers[provider_type] = ClaudeProvider(config)
        
        return self.providers[provider_type]
    
    async def chat_with_fallback(self, messages: List[Dict], **kwargs) -> Dict:
        """带降级的对话接口"""
        # 按优先级排序获取所有活跃的LLM服务商
        configs = await self.db.query(AIProviderConfig).filter_by(
            is_active=True
        ).order_by(AIProviderConfig.priority).all()
        
        last_error = None
        for config in configs:
            try:
                provider = await self.get_provider(config.provider)
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {config.provider} failed: {e}")
                last_error = e
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
```

### 5.2 具体Provider实现

```python
# backend/app/services/ai/providers/deepseek_provider.py

class DeepSeekProvider(BaseAIProvider):
    def __init__(self, config: AIProviderConfig):
        self.client = DeepSeekClient(
            api_key=aes_decrypt(config.api_key_encrypted, SECRET_KEY),
            base_url=config.api_endpoint
        )
        self.config = config.config_json or {}
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        return await self.client.chat(
            messages=messages,
            model=self.config.get("model", "deepseek-chat"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 2000)
        )
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        raise NotImplementedError("DeepSeek does not support image generation")
    
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        raise NotImplementedError("DeepSeek does not support video generation")
```

```python
# backend/app/services/ai/providers/volcengine_provider.py

class VolcengineProvider(BaseAIProvider):
    def __init__(self, config: AIProviderConfig):
        self.image_client = VolcengineImageClient(...)
        self.video_client = VolcengineVideoClient(...)
        self.config = config.config_json or {}
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        raise NotImplementedError("Volcengine does not support text chat")
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict:
        return await self.image_client.text_to_image(
            prompt=prompt,
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024),
            style=kwargs.get("style", "realistic")
        )
    
    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        return await self.video_client.text_to_video(
            prompt=prompt,
            duration=kwargs.get("duration", 5),
            resolution=kwargs.get("resolution", "1080p")
        )
```

---

## 六、成本优化策略

### 6.1 智能路由

```python
async def smart_route_llm(task_type: str, complexity: str) -> str:
    """根据任务类型和复杂度选择最优LLM"""
    
    if task_type == "simple_qa" and complexity == "low":
        return "deepseek"  # 简单问答用DeepSeek（省钱）
    
    elif task_type == "brand_story" and complexity == "high":
        return "claude"  # 复杂创作用Claude（质量）
    
    else:
        return "deepseek"  # 默认DeepSeek
```

### 6.2 批量生成优化

```python
async def batch_generate_images(prompts: List[str]) -> List[str]:
    """批量生成图像（并发优化）"""
    tasks = [
        volcengine_client.text_to_image(prompt)
        for prompt in prompts
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        r["image_url"] if not isinstance(r, Exception) else None
        for r in results
    ]
```

### 6.3 缓存策略

```python
async def generate_image_with_cache(prompt: str, **kwargs) -> Dict:
    """带缓存的图像生成"""
    cache_key = f"image:cache:{hashlib.md5(prompt.encode()).hexdigest()}"
    
    # 检查缓存
    if cached := await redis.get(cache_key):
        return json.loads(cached)
    
    # 生成图像
    result = await volcengine_client.text_to_image(prompt, **kwargs)
    
    # 缓存7天
    await redis.setex(cache_key, 604800, json.dumps(result))
    
    return result
```

---

**文档结束**

> 多AI服务商架构提升系统灵活性和可靠性，配置面板降低运维成本。
