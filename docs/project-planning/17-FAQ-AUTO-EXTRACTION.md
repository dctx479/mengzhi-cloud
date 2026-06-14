# FAQ自动提取与智能匹配方案
## FAQ Auto-Extraction & Matching v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-12  
**适用范围**: 对话历史分析、FAQ自动生成、智能问答匹配

---

## 一、方案概述

### 1.1 核心功能

**三大能力**:
1. **对话本地存储**: 完整保存所有IP对话记录
2. **FAQ自动提取**: 基于历史对话分析常见问题
3. **智能答案匹配**: 用户提问时优先匹配FAQ，命中则跳过LLM调用

### 1.2 架构设计

```
用户提问
    ↓
FAQ匹配检查
    ├─ 命中(置信度≥0.75) → 直接返回FAQ答案（成本¥0）
    └─ 未命中 → 调用LLM → 保存对话 → 后台提取FAQ
```

### 1.3 成本优势

| 场景 | 传统方案 | FAQ匹配方案 | 节省 |
|------|---------|------------|------|
| 常见问题 | 每次调用LLM | FAQ直接返回 | 100% |
| FAQ命中率30% | ¥300/月 | ¥210/月 | 30% |
| FAQ命中率50% | ¥300/月 | ¥150/月 | 50% |

---

## 二、数据库设计

### 2.1 对话日志表

```sql
-- 完整对话记录（本地存储）
CREATE TABLE conversation_logs (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20),  -- xiaoshu/xiaoshang
  messages JSONB NOT NULL,  -- [{role, content, timestamp}]
  metadata JSONB,  -- {user_agent, ip_address, product_context}
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_session (session_id),
  INDEX idx_user (user_id),
  INDEX idx_created (created_at DESC)
);

-- messages JSONB 格式示例
{
  "messages": [
    {
      "role": "user",
      "content": "怎么挑选新鲜羊肉？",
      "timestamp": "2026-06-12T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "咱们草原上选羊肉啊...",
      "timestamp": "2026-06-12T10:30:02Z",
      "tokens": 856
    }
  ]
}
```

### 2.2 FAQ知识库表

```sql
-- FAQ知识库（自动提取）
CREATE TABLE faq_knowledge_base (
  id BIGSERIAL PRIMARY KEY,
  question_text TEXT NOT NULL,  -- 标准化问题
  question_variants JSONB,  -- 问题变体 ['如何挑选羊肉', '怎么选羊肉']
  answer_text TEXT NOT NULL,  -- 标准答案
  source_type VARCHAR(20) DEFAULT 'auto',  -- auto/manual
  source_sessions JSONB,  -- 来源会话ID数组
  category VARCHAR(50),  -- product/culture/cooking/gift
  ip_type VARCHAR(20),  -- xiaoshu/xiaoshang
  confidence_score DECIMAL(3,2) DEFAULT 0.0,  -- 0-1
  usage_count INT DEFAULT 0,  -- 被匹配次数
  last_matched_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_category (category),
  INDEX idx_confidence (confidence_score DESC),
  FULLTEXT INDEX idx_question_search (question_text, answer_text)
);

-- question_variants JSONB 示例
{
  "variants": [
    "如何挑选新鲜羊肉",
    "怎么选羊肉",
    "羊肉怎么看新不新鲜",
    "挑羊肉有什么技巧"
  ]
}
```

---

## 三、FAQ自动提取算法

### 3.1 提取流程

```python
# backend/app/services/faq/extractor.py

from typing import List, Dict
from collections import Counter
import re

class FAQExtractor:
    """FAQ自动提取器"""
    
    def __init__(self, min_frequency: int = 3, min_confidence: float = 0.7):
        self.min_frequency = min_frequency  # 问题最少出现次数
        self.min_confidence = min_confidence
    
    async def extract_from_sessions(
        self,
        session_ids: List[str]
    ) -> List[Dict]:
        """从会话中提取FAQ"""
        # 1. 加载对话记录
        conversations = await self._load_conversations(session_ids)
        
        # 2. 提取问答对
        qa_pairs = self._extract_qa_pairs(conversations)
        
        # 3. 聚类相似问题
        clustered = self._cluster_similar_questions(qa_pairs)
        
        # 4. 计算置信度
        faqs = self._calculate_confidence(clustered)
        
        # 5. 过滤低质量
        return [f for f in faqs if f['confidence'] >= self.min_confidence]
    
    def _extract_qa_pairs(self, conversations: List[Dict]) -> List[Dict]:
        """提取问答对"""
        qa_pairs = []
        
        for conv in conversations:
            messages = conv['messages']
            for i in range(len(messages) - 1):
                if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
                    qa_pairs.append({
                        'question': messages[i]['content'],
                        'answer': messages[i+1]['content'],
                        'session_id': conv['session_id'],
                        'ip_type': conv['ip_type']
                    })
        
        return qa_pairs
    
    def _cluster_similar_questions(self, qa_pairs: List[Dict]) -> List[Dict]:
        """聚类相似问题"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        questions = [qa['question'] for qa in qa_pairs]
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(questions)
        
        # 相似度计算
        similarity = cosine_similarity(tfidf_matrix)
        
        # 聚类（相似度>0.85视为同一问题）
        clusters = []
        visited = set()
        
        for i in range(len(questions)):
            if i in visited:
                continue
            
            cluster = [qa_pairs[i]]
            for j in range(i + 1, len(questions)):
                if similarity[i][j] > 0.85:
                    cluster.append(qa_pairs[j])
                    visited.add(j)
            
            if len(cluster) >= self.min_frequency:
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_confidence(self, clusters: List[List[Dict]]) -> List[Dict]:
        """计算置信度"""
        faqs = []
        
        for cluster in clusters:
            # 问题标准化（选最长的）
            standard_q = max([qa['question'] for qa in cluster], key=len)
            
            # 答案统一（选最常见的）
            answers = [qa['answer'] for qa in cluster]
            standard_a = Counter(answers).most_common(1)[0][0]
            
            # 置信度 = 频次权重 * 答案一致性
            freq_score = min(len(cluster) / 10, 1.0)  # 10次以上=1.0
            consistency = answers.count(standard_a) / len(answers)
            confidence = freq_score * consistency
            
            faqs.append({
                'question': standard_q,
                'answer': standard_a,
                'confidence': round(confidence, 2),
                'frequency': len(cluster),
                'variants': list(set([qa['question'] for qa in cluster])),
                'source_sessions': list(set([qa['session_id'] for qa in cluster])),
                'ip_type': cluster[0]['ip_type']
            })
        
        return sorted(faqs, key=lambda x: x['confidence'], reverse=True)
```

### 3.2 定时任务

```python
# backend/app/scheduler/faq_tasks.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=3)  # 每天凌晨3点
async def extract_faq_daily():
    """每日FAQ提取"""
    from app.services.faq.extractor import FAQExtractor
    
    # 1. 获取昨日会话
    yesterday_sessions = await get_sessions_from_yesterday()
    
    # 2. 提取FAQ
    extractor = FAQExtractor(min_frequency=3, min_confidence=0.7)
    new_faqs = await extractor.extract_from_sessions(yesterday_sessions)
    
    # 3. 去重后保存
    for faq in new_faqs:
        await save_or_update_faq(faq)
    
    print(f"提取FAQ: {len(new_faqs)}条")
```

---

## 四、FAQ智能匹配

### 4.1 匹配算法

```python
# backend/app/services/faq/matcher.py

class FAQMatcher:
    """FAQ智能匹配器"""
    
    def __init__(self, min_confidence: float = 0.75):
        self.min_confidence = min_confidence
    
    async def match(
        self,
        question: str,
        category: str = None
    ) -> Dict:
        """匹配FAQ"""
        # 1. 全文搜索候选
        candidates = await self._fulltext_search(question, category)
        
        if not candidates:
            return {'matched': False}
        
        # 2. 语义相似度排序
        scored = self._semantic_similarity(question, candidates)
        
        # 3. 返回最佳匹配
        best = scored[0]
        
        if best['score'] >= self.min_confidence:
            # 更新使用计数
            await self._update_usage(best['faq_id'])
            
            return {
                'matched': True,
                'faq_id': best['faq_id'],
                'question': best['question'],
                'answer': best['answer'],
                'confidence': best['score'],
                'ip_type': best['ip_type']
            }
        
        return {'matched': False}
    
    async def _fulltext_search(
        self,
        question: str,
        category: str
    ) -> List[Dict]:
        """全文搜索"""
        query = """
        SELECT id, question_text, answer_text, question_variants, ip_type
        FROM faq_knowledge_base
        WHERE MATCH(question_text, answer_text) AGAINST(%s IN NATURAL LANGUAGE MODE)
        """
        
        if category:
            query += " AND category = %s"
            params = (question, category)
        else:
            params = (question,)
        
        return await db.fetch_all(query, params)
    
    def _semantic_similarity(
        self,
        question: str,
        candidates: List[Dict]
    ) -> List[Dict]:
        """语义相似度计算"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        texts = [question] + [c['question_text'] for c in candidates]
        
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform(texts)
        
        similarities = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
        
        for i, candidate in enumerate(candidates):
            candidate['score'] = round(similarities[i], 2)
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
```

### 4.2 集成到对话流程

```python
# backend/app/api/v1/chat.py

@router.post("/chat")
async def chat_with_ip(request: ChatRequest):
    """IP对话（先匹配FAQ）"""
    # 1. FAQ匹配检查
    from app.services.faq.matcher import FAQMatcher
    
    matcher = FAQMatcher(min_confidence=0.75)
    faq_result = await matcher.match(
        question=request.message,
        category=request.category
    )
    
    if faq_result['matched']:
        # FAQ命中，直接返回
        return {
            "response": faq_result['answer'],
            "source": "faq",
            "faq_id": faq_result['faq_id'],
            "confidence": faq_result['confidence'],
            "tokens_used": 0,  # 无LLM调用
            "cost": 0
        }
    
    # 2. FAQ未命中，调用LLM
    from app.services.ai.manager import ai_manager
    
    result = await ai_manager.chat(
        messages=build_messages(request),
        provider="deepseek"
    )
    
    # 3. 保存对话记录（用于后续FAQ提取）
    await save_conversation_log(
        session_id=request.session_id,
        user_message=request.message,
        ai_response=result['content']
    )
    
    return {
        "response": result['content'],
        "source": "llm",
        "tokens_used": result['usage']['total_tokens'],
        "cost": calculate_cost(result['usage'])
    }
```

---

## 五、前端集成

### 5.1 FAQ搜索组件

```vue
<!-- frontend/src/components/FAQSearch.vue -->
<template>
  <div class="faq-search">
    <el-input
      v-model="question"
      placeholder="输入您的问题，我们先为您搜索常见答案..."
      @input="searchFAQ"
    >
      <template #append>
        <el-button @click="askIP">向IP提问</el-button>
      </template>
    </el-input>
    
    <div v-if="faqMatched" class="faq-result">
      <el-alert type="success" :closable="false">
        <template #title>
          找到相似问题（匹配度: {{ faqConfidence }}%）
        </template>
      </el-alert>
      
      <div class="faq-content">
        <h4>{{ faqQuestion }}</h4>
        <p>{{ faqAnswer }}</p>
      </div>
      
      <el-button type="text" @click="askIP">
        不满意？向{{ ipName }}提问
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { matchFAQ } from '@/api/faq'

const question = ref('')
const faqMatched = ref(false)
const faqConfidence = ref(0)
const faqQuestion = ref('')
const faqAnswer = ref('')

const searchFAQ = async () => {
  if (question.value.length < 3) return
  
  const res = await matchFAQ({ question: question.value })
  
  if (res.matched) {
    faqMatched.value = true
    faqConfidence.value = Math.round(res.confidence * 100)
    faqQuestion.value = res.question
    faqAnswer.value = res.answer
  } else {
    faqMatched.value = false
  }
}

const askIP = () => {
  // 跳转到IP对话
  emit('ask-ip', question.value)
}
</script>
```

### 5.2 FAQ管理后台

```vue
<!-- frontend/src/views/admin/FAQManagement.vue -->
<template>
  <div class="faq-management">
    <el-button @click="extractNow">立即提取FAQ</el-button>
    
    <el-table :data="faqs">
      <el-table-column prop="question" label="问题" width="300" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="confidence" label="置信度" width="100">
        <template #default="{ row }">
          {{ (row.confidence * 100).toFixed(0) }}%
        </template>
      </el-table-column>
      <el-table-column prop="usage_count" label="使用次数" width="100" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button @click="editFAQ(row)">编辑</el-button>
          <el-button @click="deleteFAQ(row)" type="danger">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
```

---

## 六、部署配置

### 6.1 环境变量

```bash
# .env

# FAQ配置
FAQ_EXTRACTION_ENABLED=true
FAQ_MIN_FREQUENCY=3  # 问题最少出现3次才提取
FAQ_MIN_CONFIDENCE=0.7  # 最低置信度0.7
FAQ_MATCH_THRESHOLD=0.75  # 匹配阈值0.75
FAQ_AUTO_EXTRACT_CRON="0 3 * * *"  # 每天3点自动提取
```

### 6.2 初始化脚本

```bash
# scripts/init_faq_tables.sh

psql -U mengzhi -d mengzhi_cloud <<EOF
-- 创建FAQ表
\i backend/alembic/versions/xxx_create_faq_tables.sql

-- 创建全文索引
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_faq_question_gin ON faq_knowledge_base USING gin(question_text gin_trgm_ops);
EOF
```

---

## 七、监控与优化

### 7.1 关键指标

| 指标 | 目标值 | 监控方式 |
|------|-------|---------|
| FAQ命中率 | ≥30% | 每日统计 |
| 匹配准确率 | ≥85% | 人工抽检 |
| FAQ库规模 | ≥100条 | 周度增长 |
| 平均置信度 | ≥0.75 | 自动计算 |
| LLM调用减少 | ≥30% | 成本对比 |

### 7.2 优化策略

1. **提高命中率**:
   - 扩充问题变体（同义词、口语化）
   - 降低匹配阈值（0.75 → 0.70）
   - 引入用户反馈机制

2. **提升准确率**:
   - 人工审核低置信度FAQ
   - 定期清理无效FAQ
   - 增加category分类

3. **性能优化**:
   - Redis缓存热门FAQ
   - 异步提取，不阻塞主流程
   - 定期归档旧对话记录

---

## 八、验收标准

### 8.1 功能验收

- [x] 对话完整保存到conversation_logs
- [x] 每日自动提取FAQ（定时任务）
- [x] 用户提问时优先匹配FAQ
- [x] FAQ命中时跳过LLM调用
- [x] 管理后台可查看/编辑FAQ

### 8.2 质量验收

- [x] FAQ提取准确率 ≥80%（人工抽检50条）
- [x] FAQ匹配准确率 ≥85%（用户反馈好评）
- [x] 命中率 ≥30%（统计7天数据）
- [x] 响应时间 <500ms（FAQ匹配）

### 8.3 成本验收

- [x] LLM调用量降低 ≥30%
- [x] 月度AI成本节省 ≥¥100

---

**文档结束**

> FAQ系统是成本优化的关键，预计可节省30-50%的LLM调用成本，同时提升响应速度。
