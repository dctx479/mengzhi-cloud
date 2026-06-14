# 蒙智云开发路线图（12周详细计划）
## Development Roadmap v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**项目周期**: Week 1 (2026-06-11) ~ Week 12 (2026-09-03)

---

## Sprint 1: IP智能体MVP（Week 1-2）

### 目标
上线小数/小商双IP智能体基础对话功能，实现可切换、有特色的AI对话体验。

### 工作分解

#### 后端开发（6天）

**Day 1-2: IP Agent核心架构**
```
✓ 创建 backend/app/services/ip_agent/ 目录
✓ prompt_templates.py - Prompt模板库
  ├─ XIAOSHU_SYSTEM_PROMPT（小数人设）
  ├─ XIAOSHANG_SYSTEM_PROMPT（小商人设）
  ├─ BRAND_STORY_TEMPLATE（品牌故事模板）
  └─ CULTURAL_TRACING_TEMPLATE（文化溯源模板）

✓ configs.py - IP配置
  ├─ IPConfig数据类
  ├─ XIAOSHU_CONFIG（温度0.8）
  └─ XIAOSHANG_CONFIG（温度0.6）
```

**Day 3-4: Agent实现**
```
✓ xiaoshu_agent.py
  ├─ XiaoshuAgent类
  ├─ generate_response() - 对话生成
  ├─ generate_brand_story() - 品牌故事
  ├─ generate_cultural_tracing() - 文化溯源
  └─ _generate_mock_response() - 开发阶段Mock

✓ xiaoshang_agent.py
  ├─ XiaoshangAgent类
  ├─ generate_response() - 对话生成
  ├─ generate_live_script() - 直播脚本
  └─ generate_content_for_platform() - 平台适配

✓ ip_router.py
  ├─ IPRouter类
  ├─ route() - 意图路由
  └─ switch_ip() - IP切换
```

**Day 5-6: API接口**
```
✓ backend/app/api/v1/ip_router.py
  ├─ POST /api/v1/ip/chat - 对话接口
  ├─ POST /api/v1/ip/switch - 切换IP
  ├─ POST /api/v1/ip/brand-story - 品牌故事生成
  └─ GET /api/v1/ip/history/:session_id - 历史记录

✓ 数据库模型
  ├─ backend/app/models/ip_conversations.py
  └─ Alembic迁移脚本
```

#### 前端开发（4天）

**Day 1-2: 对话页面UI**
```
✓ frontend/src/views/ip/IPChat.vue
  ├─ IP选择栏（小数/小商切换）
  ├─ 欢迎卡片（快捷问题）
  ├─ 消息列表组件
  └─ 输入区域（支持Ctrl+Enter发送）
```

**Day 3-4: API对接与状态管理**
```
✓ frontend/src/api/ip.ts
  ├─ chat() - 对话接口
  ├─ switch() - 切换IP
  └─ getHistory() - 历史记录

✓ frontend/src/stores/ip.ts（Pinia状态管理）
  ├─ currentIP: 'xiaoshu' | 'xiaoshang'
  ├─ messages: Message[]
  ├─ sessionId: string
  └─ actions: sendMessage(), clearChat()
```

#### 测试与联调（2天）

**Day 1: 功能测试**
```
测试用例
├─ TC-IP-01: 小数对话 - 输入"推荐羊肉" → 验证草原文化元素
├─ TC-IP-02: 小商对话 - 输入"直播脚本" → 验证营销话术
├─ TC-IP-03: IP切换 - 小数→小商 → 验证提示语+上下文保留
├─ TC-IP-04: 历史记录 - 刷新页面 → 验证对话恢复
└─ TC-IP-05: 并发测试 - 10用户同时对话 → 验证无串话
```

**Day 2: Bug修复与优化**
```
✓ 修复已知Bug
✓ 响应时间优化（<2s）
✓ UI交互细节打磨
✓ 撰写Sprint 1总结文档
```

### 交付物

- [x] 小数/小商双IP对话功能（Web端）
- [x] 对话历史持久化
- [x] API文档（Swagger）
- [x] Sprint 1演示视频（3分钟）

### 验收标准

| 标准 | 目标 | 实际 |
|-----|------|------|
| IP切换响应时间 | <1s | [待测] |
| 对话响应时间 | <2s | [待测] |
| 小数回复草原文化元素出现率 | ≥80% | [待测] |
| 小商回复营销建议出现率 | ≥80% | [待测] |
| 对话历史恢复成功率 | 100% | [待测] |

---

## Sprint 2: 知识图谱基础（Week 3-4）

### 目标
建立产品-文化关联的知识图谱基础设施，实现文化溯源查询。

### 工作分解

#### 数据库设计（2天）

**Day 1: Schema设计**
```sql
-- backend/migrations/versions/xxx_add_knowledge_graph.py

CREATE TABLE cultural_elements (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_mongolian VARCHAR(100),
    type VARCHAR(20) NOT NULL,  -- festival/skill/story/food/custom/craft
    description TEXT,
    origin_region VARCHAR(100),
    related_products JSONB,
    hot_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE origin_culture_relation (
    id BIGSERIAL PRIMARY KEY,
    origin_id INT NOT NULL,
    culture_id BIGINT NOT NULL,
    relation_type VARCHAR(50),
    weight DECIMAL(3,2) DEFAULT 1.0,
    evidence TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE product_culture_trace (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL,
    culture_id BIGINT NOT NULL,
    relation_path JSONB,
    story_content TEXT,
    trace_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Day 2: 数据初始化**
```sql
-- 录入15个内蒙古文化元素
INSERT INTO cultural_elements (name, type, description) VALUES
('那达慕', 'festival', '蒙古族传统盛会，包括摔跤、赛马、射箭'),
('敖包祭祀', 'festival', '蒙古族传统祭天祈福仪式'),
('白月节', 'festival', '蒙古族新年'),
('手把肉', 'food', '蒙古族传统羊肉吃法'),
('奶茶文化', 'food', '蒙古族日常饮品'),
...（共15条）
```

#### 后端服务（4天）

**Day 3-4: 知识图谱服务**
```python
# backend/app/services/knowledge_graph_service.py

class KnowledgeGraphService:
    def get_cultural_elements(
        self, 
        element_type: str = None,
        keyword: str = None
    ) -> List[Dict]:
        """查询文化元素"""
        pass
    
    def get_product_cultural_trace(
        self, 
        product_id: int
    ) -> Dict:
        """获取产品文化溯源报告"""
        # 产品 → 产地 → 文化元素 → 故事
        pass
    
    def recommend_cultural_elements(
        self,
        product_id: int
    ) -> List[Dict]:
        """为产品推荐文化元素"""
        pass
    
    def build_marketing_content(
        self,
        product_id: int
    ) -> str:
        """基于知识图谱自动构建品牌故事"""
        pass
```

**Day 5-6: API接口**
```python
# backend/app/api/v1/knowledge_router.py

@router.get("/api/v1/knowledge/cultures")
async def get_cultures(type: str = None):
    """获取文化元素列表"""
    pass

@router.get("/api/v1/knowledge/trace/{product_id}")
async def get_product_trace(product_id: int):
    """获取产品文化溯源"""
    pass

@router.post("/api/v1/knowledge/recommend")
async def recommend_cultures(product_id: int):
    """推荐文化元素"""
    pass
```

#### 前端开发（4天）

**Day 7-8: 文化溯源页面**
```vue
<!-- frontend/src/views/knowledge/CulturalTracing.vue -->

<template>
  <div class="cultural-tracing">
    <!-- 产品选择 -->
    <n-select v-model="selectedProduct" :options="products" />
    
    <!-- 溯源报告 -->
    <div v-if="traceReport" class="trace-report">
      <!-- 产品信息卡片 -->
      <product-info-card :data="traceReport.product" />
      
      <!-- 产地信息卡片 -->
      <origin-info-card :data="traceReport.origin" />
      
      <!-- 文化关联（步骤条） -->
      <n-steps :current="currentStep">
        <n-step title="产地起源" />
        <n-step title="历史传承" />
        <n-step title="技艺非遗" />
        <n-step title="地理标志" />
      </n-steps>
      
      <!-- 文化元素列表 -->
      <culture-list :items="traceReport.cultures" />
      
      <!-- 品牌故事 -->
      <brand-story-card :content="traceReport.story" />
    </div>
  </div>
</template>
```

**Day 9-10: API对接与调试**
```typescript
// frontend/src/api/knowledge.ts

export const knowledgeAPI = {
  getCultures(type?: string) {
    return http.get('/api/v1/knowledge/cultures', { params: { type } })
  },
  
  getProductTrace(productId: number) {
    return http.get(`/api/v1/knowledge/trace/${productId}`)
  },
  
  recommendCultures(productId: number) {
    return http.post('/api/v1/knowledge/recommend', { product_id: productId })
  }
}
```

#### 测试与优化（2天）

**Day 11: 功能测试**
```
测试用例
├─ TC-KG-01: 文化元素查询 - 查询所有节日类 → 返回那达慕等3个
├─ TC-KG-02: 产品溯源 - 查询羊肉溯源 → 返回完整链路
├─ TC-KG-03: 文化推荐 - 新产品推荐 → 返回3个相关文化元素
└─ TC-KG-04: 故事生成 - 自动拼接 → 语句通顺，≥300字
```

**Day 12: 数据质量优化**
```
✓ 检查15个文化元素描述完整性
✓ 优化产地-文化关联权重
✓ 完善品牌故事生成逻辑
✓ 性能优化（查询<500ms）
```

### 交付物

- [x] 15个文化元素录入
- [x] 产品文化溯源功能
- [x] 溯源可视化页面
- [x] 知识图谱API文档

### 验收标准

| 标准 | 目标 | 实际 |
|-----|------|------|
| 文化元素数量 | ≥15个 | [待验] |
| 溯源查询响应时间 | <500ms | [待测] |
| 故事生成质量 | 人工评审≥8/10 | [待评] |
| 前端页面加载 | <2s | [待测] |

---

## Sprint 3: 营销工具集（Week 5-6）

### 目标
完善品牌故事生成和直播脚本生成功能，形成完整营销工具集。

### 工作分解

#### 后端开发（5天）

**Day 1-2: 品牌故事生成增强**
```python
# 集成知识图谱到品牌故事生成

def generate_enhanced_brand_story(product_id: int):
    # 1. 查询产品信息
    product = get_product(product_id)
    
    # 2. 查询文化溯源
    trace = kg_service.get_product_cultural_trace(product_id)
    
    # 3. 构建增强Prompt
    prompt = f"""
    【产品信息】
    产品：{product.name}
    产地：{trace['origin']['name']}
    
    【文化背景】
    {' | '.join([c['name'] for c in trace['cultures']])}
    
    【故事要求】
    融入草原文化元素，突出产品特色，300-500字。
    """
    
    # 4. 调用LLM生成
    story = xiaoshu_agent.generate_response(prompt)
    
    # 5. 保存到品牌故事库
    save_brand_story(product_id, story)
    
    return story
```

**Day 3-5: 直播脚本生成**
```python
# backend/app/services/live_script_service.py

class LiveScriptService:
    def generate_script(
        self,
        product_id: int,
        platform: str,  # douyin/xiaohongshu/shipinhao
        duration: int = 5,
        style: str = "热情"
    ) -> Dict:
        """
        生成直播脚本
        
        Returns:
            {
                "script": [
                    {
                        "phase": "开场",
                        "start": "0:00",
                        "end": "0:30",
                        "scene": "草原空镜",
                        "script": "老铁们好！..."
                    },
                    ...
                ],
                "bgm_suggestions": [...],
                "shooting_tips": [...]
            }
        """
        # 调用小商Agent生成
        return xiaoshang_agent.generate_live_script(
            product_name=product.name,
            price=product.price,
            platform=platform,
            duration=duration,
            style=style
        )
```

#### 前端开发（5天）

**Day 6-7: 品牌故事生成页面**
```vue
<!-- frontend/src/views/marketing/BrandStoryGenerator.vue -->

<template>
  <div class="brand-story-generator">
    <!-- 产品选择 -->
    <n-form-item label="选择产品">
      <n-select v-model="form.productId" :options="productOptions" />
    </n-form-item>
    
    <!-- 自定义参数（可选） -->
    <n-collapse>
      <n-collapse-item title="高级选项">
        <n-form-item label="目标人群">
          <n-input v-model="form.targetAudience" />
        </n-form-item>
        <n-form-item label="核心卖点">
          <n-dynamic-tags v-model="form.sellingPoints" />
        </n-form-item>
      </n-collapse-item>
    </n-collapse>
    
    <!-- 生成按钮 -->
    <n-button type="primary" @click="generate" :loading="generating">
      生成品牌故事
    </n-button>
    
    <!-- 结果展示 -->
    <div v-if="story" class="story-result">
      <n-card title="生成的品牌故事">
        <div class="story-content">{{ story.content }}</div>
        <template #footer>
          <n-space>
            <n-button @click="copyStory">复制</n-button>
            <n-button @click="saveStory">保存</n-button>
            <n-button @click="regenerate">重新生成</n-button>
          </n-space>
        </template>
      </n-card>
    </div>
  </div>
</template>
```

**Day 8-10: 直播脚本生成页面**
```vue
<!-- frontend/src/views/marketing/LiveScriptGenerator.vue -->

<template>
  <div class="live-script-generator">
    <n-form :model="form">
      <!-- 产品选择 -->
      <n-form-item label="产品" required>
        <n-select v-model="form.productId" :options="products" />
      </n-form-item>
      
      <!-- 平台选择 -->
      <n-form-item label="平台" required>
        <n-radio-group v-model="form.platform">
          <n-radio value="douyin">抖音</n-radio>
          <n-radio value="xiaohongshu">小红书</n-radio>
          <n-radio value="shipinhao">视频号</n-radio>
        </n-radio-group>
      </n-form-item>
      
      <!-- 时长设置 -->
      <n-form-item label="时长（分钟）">
        <n-slider v-model:value="form.duration" :min="3" :max="10" />
      </n-form-item>
      
      <!-- 风格选择 -->
      <n-form-item label="主播风格">
        <n-select v-model="form.style" :options="styleOptions" />
      </n-form-item>
    </n-form>
    
    <!-- 生成按钮 -->
    <n-button type="primary" @click="generate" :loading="loading">
      生成脚本
    </n-button>
    
    <!-- 脚本展示（分镜表格） -->
    <div v-if="script" class="script-result">
      <n-card title="直播脚本">
        <n-data-table
          :columns="columns"
          :data="script.script"
          :pagination="false"
        />
        
        <!-- BGM建议 -->
        <n-divider />
        <div class="suggestions">
          <h4>BGM建议</h4>
          <n-space>
            <n-tag v-for="bgm in script.bgm_suggestions" :key="bgm">
              {{ bgm }}
            </n-tag>
          </n-space>
          
          <h4>拍摄建议</h4>
          <ul>
            <li v-for="tip in script.shooting_tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>
        
        <template #footer>
          <n-space>
            <n-button @click="exportScript">导出脚本</n-button>
            <n-button @click="saveScript">保存</n-button>
          </n-space>
        </template>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
const columns = [
  { title: '阶段', key: 'phase', width: 80 },
  { title: '时间', key: 'start', width: 80 },
  { title: '画面', key: 'scene', width: 150 },
  { title: '讲解内容', key: 'script', ellipsis: { tooltip: true } }
]
</script>
```

#### 测试与联调（2天）

**Day 11: 功能测试**
```
测试用例
├─ TC-MT-01: 品牌故事生成 - 选择产品 → 生成≥300字故事
├─ TC-MT-02: 故事质量评估 - 人工评审10个 → 通过率≥80%
├─ TC-MT-03: 直播脚本生成 - 抖音5分钟 → 包含开场/讲解/促单
├─ TC-MT-04: 脚本导出 - 导出为PDF → 格式正确
└─ TC-MT-05: 批量生成 - 同时生成5个 → 无阻塞
```

**Day 12: 优化与文档**
```
✓ 生成速度优化（<5s）
✓ 结果缓存机制
✓ 使用手册编写
✓ Sprint 3演示准备
```

### 交付物

- [x] 品牌故事生成工具
- [x] 直播脚本生成工具
- [x] 营销工具使用手册
- [x] 10个示例品牌故事

### 验收标准

| 标准 | 目标 | 实际 |
|-----|------|------|
| 品牌故事生成时间 | <5s | [待测] |
| 品牌故事质量评分 | ≥8/10 | [待评] |
| 直播脚本完整性 | 包含5个阶段 | [待验] |
| 用户操作便捷性 | ≤3步生成内容 | [待验] |

---

## Sprint 4-6 简要计划

### Sprint 4: 多平台内容适配（Week 7-8）

**核心任务**
- 实现抖音/小红书/公众号内容适配引擎
- 一键生成多平台内容
- 批量内容管理功能

**关键交付**
- 平台适配API
- 内容预览与编辑页面
- 批量发布工具

### Sprint 5: 效果监测看板（Week 9-10）

**核心任务**
- AI使用统计（对话数、生成数、Token消耗）
- 内容发布统计（按平台/时间）
- 成本分析Dashboard

**关键交付**
- 数据采集埋点
- 可视化看板（Echarts）
- 导出报表功能

### Sprint 6: 系统优化与交付（Week 11-12）

**核心任务**
- 性能优化（响应时间、并发能力）
- 全量功能测试
- 用户手册与部署文档
- 大创申报材料准备

**关键交付**
- 生产环境部署
- 完整技术文档
- 用户使用手册
- 项目演示视频

---

## 附录：每日工作模板

### Daily Standup记录表

**日期**: 2026-XX-XX  
**Sprint**: X  
**参与人**: [全员]

| 姓名 | 昨日完成 | 今日计划 | 遇到的问题 |
|-----|---------|---------|-----------|
| 张三 | IP Agent核心代码 | API接口开发 | LLM调用超时 |
| 李四 | 对话页面UI | API对接 | 无 |
| ... | ... | ... | ... |

**团队风险**: [无 / 有风险描述]  
**需要协调事项**: [无 / 需要协调的事项]

---

**文档结束**

> 本路线图每2周更新一次，请以最新版本为准。