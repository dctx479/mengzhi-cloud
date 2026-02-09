# AI-007 内容生成优化 - 实现和部署指南

## 快速开始

### 环境准备

```bash
# 1. 进入项目目录
cd E:\项目\数商\AI赋能云平台\backend

# 2. 安装新增依赖
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu numpy

# 3. 验证安装
python -c "import faiss, sentence_transformers; print('OK')"
```

### 集成到主应用

在 `backend/app/main.py` 中添加:

```python
from fastapi import FastAPI
from app.api.optimized_content import router as content_router

app = FastAPI()

# 其他路由...

# 添加优化的内容生成路由
app.include_router(content_router)
```

### 启动服务

```bash
# 开发模式
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 核心模块说明

### 1. RAG知识库 (`rag_knowledge_base.py`)

**初始化知识库**:
```python
from app.services.rag_knowledge_base import CulturalKnowledgeBase
from app.database import SessionLocal

kb = CulturalKnowledgeBase()
db = SessionLocal()

# 构建索引
await kb.build_index(db)
```

**检索文化背景**:
```python
# 获取产品
product = db.query(Product).get(1)

# 检索相关文化元素
context = await kb.retrieve_cultural_context(
    product=product,
    top_k=5
)

# context 返回格式:
# [
#   {
#     'type': 'geo_indicator',
#     'content': '锡林郭勒羊肉：国家地理标志产品',
#     'relevance': 0.95,
#     'category': 'geo',
#     'source': 'product_1'
#   },
#   ...
# ]
```

**营销素材检索**:
```python
materials = await kb.retrieve_marketing_materials(
    category='羊肉',
    style='casual',
    top_k=3
)
```

### 2. 参数优化 (`content_optimization.py`)

**获取最优参数**:
```python
from app.services.content_optimization import AdaptiveParameterOptimizer
from app.models.content_record import ContentType, Style, Platform

# 获取最优参数
params = AdaptiveParameterOptimizer.get_optimal_parameters(
    content_type=ContentType.COPY,
    style=Style.CASUAL,
    platform=Platform.DOUYIN,
    quality_score=None  # 可选：基于上一次质量分数调整
)

# params 返回:
# {
#   'temperature': 0.8,
#   'top_p': 0.95,
#   'max_tokens': 300
# }
```

**为重试调整参数**:
```python
# 第一次失败后，为重试调整参数
adjusted_params = AdaptiveParameterOptimizer.adjust_for_retry(
    current_params=params,
    retry_count=1
)

# temperature 会增加，提高多样性
```

**多样性控制**:
```python
from app.services.content_optimization import DiversityController

controller = DiversityController(db=db, similarity_threshold=0.85)

# 生成多个多样化的变体
variants = await controller.generate_diverse_variants(
    product_id=1,
    count=3,
    content_type=ContentType.COPY,
    style=Style.CASUAL,
    generation_func=your_generation_function,
    db=db
)
```

### 3. 后处理 (`content_postprocessor.py`)

**处理内容**:
```python
from app.services.content_postprocessor import ContentPostProcessor

processed = await ContentPostProcessor.process(
    content="原始生成的内容...",
    style=Style.CASUAL,
    platform=Platform.DOUYIN,
    target_word_count=200,
    content_type=ContentType.VIDEO_COPY
)
```

**评估质量**:
```python
from app.services.content_postprocessor import QualityAssessment

quality_score, details = await QualityAssessment.assess_content(
    content=processed,
    target_word_count=200,
    content_type=ContentType.VIDEO_COPY,
    platform=Platform.DOUYIN
)

print(f"质量分: {quality_score:.2f}")  # 0-1 之间
print(f"详细评分: {details}")
# 包括：length, completeness, coherence, readability,
#      cultural_richness, no_errors
```

### 4. 核心生成服务 (`optimized_content_generation.py`)

**使用方式**:
```python
from app.services.optimized_content_generation import ContentGenerationServiceFactory
from app.models.content_record import ContentType, Style, Platform

# 创建服务
service = await ContentGenerationServiceFactory.get_service(db)

# 生成单个内容
content = await service.generate_product_copy(
    product_id=1,
    content_type=ContentType.COPY,
    style=Style.CASUAL,
    platform=Platform.DOUYIN,
    word_count=200
)

# 生成多个变体
variants = await service.generate_multiple_variants(
    product_id=1,
    count=3,
    content_type=ContentType.COPY,
    style=Style.CASUAL,
    platform=Platform.XIAOHONGSHU,
    word_count=300
)
```

---

## API 使用示例

### 生成单个内容

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "content_type": "copy",
    "style": "casual",
    "platform": "douyin",
    "word_count": 200
  }'

# 响应:
# {
#   "status": "success",
#   "message": "内容生成成功",
#   "data": {
#     "content": "你知道吗？内蒙古锡林郭勒羊肉...",
#     "length": 198,
#     "content_type": "copy",
#     "style": "casual",
#     "platform": "douyin"
#   }
# }
```

### 生成多个变体

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate-variants" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "count": 3,
    "content_type": "copy",
    "style": "casual",
    "platform": "xiaohongshu",
    "word_count": 300
  }'

# 响应:
# {
#   "status": "success",
#   "message": "成功生成 3 个内容变体",
#   "data": {
#     "variants": [
#       "版本1的内容...",
#       "版本2的内容...",
#       "版本3的内容..."
#     ],
#     "count": 3,
#     "content_type": "copy",
#     "style": "casual",
#     "platform": "xiaohongshu"
#   }
# }
```

### 获取支持的选项

```bash
# 内容类型
curl http://localhost:8000/api/v1/content/content-types

# 风格
curl http://localhost:8000/api/v1/content/styles

# 平台
curl http://localhost:8000/api/v1/content/platforms
```

---

## 配置优化

### .env 配置

```ini
# DeepSeek 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600

# RAG 配置
RAG_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RAG_INDEX_TYPE=faiss
RAG_SIMILARITY_THRESHOLD=0.85

# Redis 配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 参数调整

在 `content_optimization.py` 中修改预设参数:

```python
PARAMETER_PRESETS = {
    ContentType.COPY: {
        Style.CASUAL: {
            'temperature': 0.7,    # 调整创意度 (0.0-1.0)
            'top_p': 0.9,          # 调整多样性
            'max_tokens': 400      # 最大输出长度
        }
    }
}
```

---

## 数据库迁移

如果需要持久化内容生成记录（已在 `content_record.py` 中定义）：

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "Add content_generation_optimization"

# 执行迁移
alembic upgrade head
```

---

## 监控和调试

### 启用详细日志

在 `backend/app/core/logging.py` 中配置：

```python
from loguru import logger

logger.enable("app.services.optimized_content_generation")
logger.enable("app.services.rag_knowledge_base")
logger.enable("app.services.content_optimization")
logger.enable("app.services.content_postprocessor")

# 输出到文件
logger.add(
    "logs/content_generation_{time}.log",
    level="DEBUG",
    rotation="500 MB"
)
```

### 性能测试

```python
import time
import asyncio

async def benchmark():
    service = await ContentGenerationServiceFactory.get_service(db)

    start = time.time()

    content = await service.generate_product_copy(
        product_id=1,
        content_type=ContentType.COPY,
        style=Style.CASUAL,
        platform=Platform.DOUYIN,
        word_count=200
    )

    elapsed = time.time() - start

    print(f"生成耗时: {elapsed:.2f}秒")
    print(f"内容长度: {len(content)}")

# 运行
asyncio.run(benchmark())
```

---

## 常见问题排查

### 问题：FAISS 导入错误

```
ImportError: No module named 'faiss'
```

**解决**:
```bash
pip install faiss-cpu
# 或 GPU 版本
pip install faiss-gpu
```

### 问题：向量模型下载失败

**解决**:
```python
# 手动指定模型路径
os.environ['HF_HOME'] = '/path/to/models'

# 或使用本地模型
SentenceTransformer.from_pretrained('local_model_path')
```

### 问题：DeepSeek API 超时

**解决**:
```python
# 在 deepseek_client.py 中增加超时时间
self.timeout = 60.0  # 增加到 60秒
```

### 问题：缓存导致内容重复

**解决**:
- 这是正常行为（相同参数返回缓存结果）
- 如需强制刷新，使用不同的参数组合
- 或在 `.env` 中设置 `CACHE_ENABLED=false`

### 问题：内容质量评分低

**检查清单**:
1. 产品描述是否完整
2. 文化标签是否配置
3. DeepSeek API 是否正常
4. 参数配置是否合理
5. 日志输出是否显示错误

---

## 性能优化建议

### 1. 启用缓存

```python
# 在 .env 中
CACHE_ENABLED=true

# 或配置 Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. 批量初始化知识库

```python
# 应用启动时
@app.on_event("startup")
async def startup():
    kb = CulturalKnowledgeBase()
    await kb.build_index(db)
    app.state.knowledge_base = kb
```

### 3. 异步处理

```python
# 使用后台任务处理大量生成请求
from fastapi import BackgroundTasks

@router.post("/generate-batch")
async def generate_batch(
    requests: List[GenerationRequest],
    background_tasks: BackgroundTasks
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_batch, requests, task_id)
    return {"task_id": task_id}
```

### 4. 向量化操作

```python
# 批量编码以提高性能
embeddings = encoder.encode(
    texts,
    batch_size=32,  # 调整批大小
    convert_to_numpy=True,
    show_progress_bar=True
)
```

---

## 测试用例

### 单元测试

```python
# tests/test_content_optimization.py
import pytest
from app.services.optimized_content_generation import OptimizedContentGenerationService

@pytest.mark.asyncio
async def test_generate_content():
    service = await ContentGenerationServiceFactory.get_service(db)

    content = await service.generate_product_copy(
        product_id=1,
        content_type=ContentType.COPY,
        style=Style.CASUAL,
        platform=Platform.DOUYIN,
        word_count=200
    )

    assert content is not None
    assert len(content) > 0
    assert len(content) <= 300  # 200 ± 50%

@pytest.mark.asyncio
async def test_multiple_variants():
    service = await ContentGenerationServiceFactory.get_service(db)

    variants = await service.generate_multiple_variants(
        product_id=1,
        count=3,
        content_type=ContentType.COPY,
        style=Style.CASUAL,
        platform=Platform.XIAOHONGSHU,
        word_count=300
    )

    assert len(variants) == 3
    # 检查多样性
    for i in range(len(variants) - 1):
        similarity = controller.calculate_content_similarity(
            variants[i], variants[i+1]
        )
        assert similarity < 0.85  # 不应过于相似
```

---

## 故障恢复

### 自动重试机制

```python
# 已在 _generate_with_retry 中实现
# 最多尝试 3 次
# 使用指数退避 (2s, 4s, 8s)
# 自动调整参数
```

### 降级策略

```python
# 如果 FAISS 不可用，自动使用备用检索
if not HAS_FAISS:
    context = await kb._fallback_retrieve(product, top_k, db)
```

---

## 版本管理

### 当前版本: 2.0 (优化版)

**改进内容**:
- 集成 RAG 知识库
- 自适应参数优化
- 多样性控制
- 完善后处理
- 性能缓存

**兼容性**:
- 与现有 DeepSeek 客户端兼容
- 与现有数据库模型兼容
- 可选集成 Redis

---

## 反馈和改进

如发现问题或有改进建议，请：

1. 查看日志确认问题
2. 检查参数配置
3. 尝试调整敏感参数
4. 记录详细的复现步骤
5. 联系技术支持

---

**最后更新**: [项目完成日期]
**维护者**: AI优化团队
