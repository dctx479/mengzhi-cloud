# FE-009 技术文档

## 架构概览

```
┌─────────────────────────────────────────────────┐
│         Views (页面层)                          │
│  ContentStudio.vue                              │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│    Components (组件层)                          │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │Template  │Config    │Results   │Batch     │ │
│  │Selector  │Panel     │Panel     │Task      │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
│  ┌──────────┬──────────┐                       │
│  │History   │Statistics│                       │
│  │Panel     │Panel     │                       │
│  └──────────┴──────────┘                       │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│    Stores (状态管理层)                          │
│  useContentGenerationStore (Pinia)             │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│    API Service (API层)                         │
│  content-generation.ts                         │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
             Backend API Endpoints
```

---

## 文件结构

```
frontend/
├── src/
│   ├── types/
│   │   └── content-generation.ts      # 类型定义
│   │
│   ├── api/
│   │   └── content-generation.ts      # API服务
│   │
│   ├── stores/
│   │   └── content-generation.ts      # Pinia Store
│   │
│   ├── components/
│   │   ├── TemplateSelector.vue       # 模板选择器
│   │   ├── ConfigPanel.vue            # 配置面板
│   │   ├── ResultsPanel.vue           # 结果展示
│   │   ├── BatchTaskManager.vue       # 任务管理
│   │   ├── HistoryPanel.vue           # 历史记录
│   │   └── StatisticsPanel.vue        # 统计分析
│   │
│   ├── views/
│   │   └── ContentStudio.vue          # 主页面
│   │
│   ├── router/
│   │   └── index.ts                   # 路由配置
│   │
│   └── ...其他文件
│
└── tests/
    └── content-generation.test.ts     # 测试文件
```

---

## 核心类型定义

### ContentTemplate
```typescript
interface ContentTemplate {
  id: string                          // 模板ID
  category: TemplateCategory          // 模板分类
  name: string                        // 模板名称
  description: string                 // 描述
  sample: string                      // 样本输出
  difficulty: DifficultyLevel         // 难度等级
  usage_count: number                 // 使用次数
  parameters?: Record<string, any>    // 参数
  prompt?: string                     // LLM Prompt
  created_at: string                  // 创建时间
  updated_at: string                  // 更新时间
}
```

### GenerationConfig
```typescript
interface GenerationConfig {
  product_ids: string[]               // 产品ID列表
  template_id: string                 // 模板ID
  count: number                       // 生成数量
  style: ContentStyle                 // 文案风格
  word_count: number                  // 字数限制
  target_audience: TargetAudience[]   // 目标受众
  keywords: string[]                  // 关键词
  avoid_words: string                 // 避免词汇
  temperature: number                 // 创意温度
}
```

### GenerationResult
```typescript
interface GenerationResult {
  id: string                          // 结果ID
  template_id: string                 // 模板ID
  product_id: string                  // 产品ID
  content: string                     // 生成内容
  word_count: number                  // 字数
  rating: number                      // 评分
  edited: boolean                     // 是否编辑过
  created_at: string                  // 创建时间
  updated_at: string                  // 更新时间
}
```

---

## Store 详解

### 状态 (State)

```typescript
// 模板相关
templates: ContentTemplate[]          // 所有模板
selectedTemplate: ContentTemplate     // 选中的模板
templatesLoading: boolean             // 加载中状态
templatesError: string | null         // 错误信息

// 配置相关
config: GenerationConfig              // 生成配置

// 结果相关
results: GenerationResult[]           // 生成结果
generating: boolean                   // 生成中状态
progress: number                      // 生成进度
generationError: string | null        // 生成错误

// 任务相关
batchTasks: BatchTask[]               // 批量任务列表
tasksLoading: boolean                 // 任务加载中
currentTask: BatchTask | null         // 当前任务

// 配置保存
savedConfigs: SavedConfig[]           // 保存的配置
configsLoading: boolean               // 配置加载中
```

### 计算属性 (Computed)

```typescript
// 当前选中的分类
selectedCategory: TemplateCategory

// 按分类过滤的模板
filteredTemplates: ContentTemplate[]

// 所有模板分类
templateCategories: Array<{id, name, icon, count}>

// 是否有结果
hasResults: boolean

// 总字数
totalWordCount: number
```

### 关键方法 (Actions)

```typescript
// 模板操作
async fetchTemplates()                // 获取所有模板
selectTemplate(template)              // 选择模板
selectCategory(category)              // 按分类获取模板

// 配置操作
updateConfig(newConfig)               // 更新配置
addKeyword(keyword)                   // 添加关键词
removeKeyword(keyword)                // 删除关键词
resetConfig()                         // 重置配置

// 内容生成
async generateContent()               // 生成内容
async regenerateResult(result)        // 重新生成
updateResult(resultId, content)       // 更新结果
rateResult(resultId, rating)          // 评分

// 批量任务
async fetchBatchTasks()               // 获取任务列表
async cancelBatchTask(taskId)         // 取消任务
async exportResults(format, taskId)   // 导出结果

// 配置保存
async saveConfiguration(name)         // 保存配置
async fetchSavedConfigs()             // 获取保存的配置
async loadSavedConfig(configId)       // 加载配置
```

---

## API 接口规范

### 请求头

所有请求自动添加:
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 响应格式

成功响应:
```typescript
{
  data: T,
  success: true
}
```

错误响应:
```typescript
{
  error: string,
  success: false,
  code: number
}
```

### 主要端点

#### 1. 模板操作

**获取所有模板**
```
GET /api/content-generation/templates
Response: ContentTemplate[]
```

**按分类获取**
```
GET /api/content-generation/templates?category=product
Response: ContentTemplate[]
```

**获取单个模板**
```
GET /api/content-generation/templates/:id
Response: ContentTemplate
```

#### 2. 内容生成

**生成内容**
```
POST /api/content-generation/generate
Body: GenerationRequest
Response: GenerationResponse[]

interface GenerationRequest {
  config: GenerationConfig
  batch_id?: string
}

interface GenerationResponse {
  id: string
  content: string
  metadata?: Record<string, any>
}
```

**WebSocket 流式生成**
```
WS /api/content-generation/stream/:taskId

Message Format:
{
  type: 'progress' | 'result' | 'complete' | 'error',
  data: {
    progress?: number,
    content?: string,
    error?: string
  }
}
```

#### 3. 任务管理

**获取任务列表**
```
GET /api/content-generation/tasks
Response: BatchTask[]
```

**获取任务详情**
```
GET /api/content-generation/tasks/:id
Response: BatchTask
```

**取消任务**
```
POST /api/content-generation/tasks/:id/cancel
Response: { success: boolean }
```

#### 4. 导出功能

**导出为 TXT**
```
GET /api/content-generation/tasks/:id/export/txt
Response: text/plain
```

**导出为 DOCX**
```
GET /api/content-generation/tasks/:id/export/docx
Response: application/vnd.openxmlformats
```

**导出为 PDF**
```
GET /api/content-generation/tasks/:id/export/pdf
Response: application/pdf
```

#### 5. 配置管理

**获取已保存配置**
```
GET /api/content-generation/configs
Response: SavedConfig[]
```

**保存配置**
```
POST /api/content-generation/configs
Body: { name: string, config: GenerationConfig }
Response: SavedConfig
```

**获取配置详情**
```
GET /api/content-generation/configs/:id
Response: SavedConfig
```

**删除配置**
```
DELETE /api/content-generation/configs/:id
Response: { success: boolean }
```

#### 6. 历史和统计

**获取历史记录**
```
GET /api/content-generation/history?limit=20&offset=0
Response: { data: HistoryRecord[], total: number }
```

**获取统计数据**
```
GET /api/content-generation/statistics
Response: {
  total_generated: number,
  success_rate: number,
  avg_time: number,
  avg_rating: number,
  top_templates: Array<{name, count, avg_rating}>,
  top_results: Array<{content, rating}>,
  daily_stats: Array<{date, count, success, avg_rating, total_words}>
}
```

---

## 组件通信

### 父子通信

```
ContentStudio.vue (父)
├── TemplateSelector.vue
│   └── 事件: selectTemplate(template)
│   └── Props: 无（使用Store）
│
├── ConfigPanel.vue
│   └── 事件: updateConfig(config)
│   └── Props: 无（使用Store）
│
├── ResultsPanel.vue
│   └── 事件: exportResults(format)
│   └── Props: 无（使用Store）
│
├── BatchTaskManager.vue
│   └── Props: 无（使用Store）
│
├── HistoryPanel.vue
│   └── Props: 无（使用Store）
│
└── StatisticsPanel.vue
    └── Props: 无（使用Store）
```

### 全局状态通信

所有组件通过 `useContentGenerationStore()` 通信：

```typescript
// 在组件中
const contentStore = useContentGenerationStore()

// 访问状态
contentStore.results
contentStore.config
contentStore.generating

// 调用方法
await contentStore.generateContent()
contentStore.updateConfig({...})
```

---

## 事件流

### 生成内容流程

```
1. TemplateSelector
   ↓ selectTemplate(template)
   ↓ contentStore.selectTemplate()

2. ConfigPanel
   ↓ updateConfig(newConfig)
   ↓ contentStore.updateConfig()
   ↓ 点击生成按钮

3. ContentGenerationStore
   ↓ generateContent()
   ↓ API 调用

4. ResultsPanel
   ↓ 接收 contentStore.results 更新
   ↓ 显示进度和结果
   ↓ 用户操作（编辑、评分、导出）

5. 更新 Store
   ↓ 状态变化反应到其他组件
```

---

## 错误处理

### 全局错误捕获

```typescript
// Store 中的错误处理
try {
  const response = await contentAPI.generateContent(request)
  results.value = response
  progress.value = 100
} catch (err) {
  generationError.value =
    err instanceof Error ? err.message : 'Failed to generate'
  generating.value = false
}
```

### 组件级别错误处理

```typescript
// 在组件中显示错误
<div v-if="contentStore.generationError" class="error">
  {{ contentStore.generationError }}
</div>
```

### 常见错误码

```
400 - Bad Request (参数错误)
401 - Unauthorized (未认证)
403 - Forbidden (禁止访问)
404 - Not Found (资源不存在)
429 - Too Many Requests (限流)
500 - Server Error (服务器错误)
```

---

## 性能优化

### 1. 组件优化

**懒加载**:
```typescript
// 路由懒加载
const ContentStudio = () => import('@/views/ContentStudio.vue')
```

**异步组件**:
```typescript
import { defineAsyncComponent } from 'vue'
const TemplateSelector = defineAsyncComponent(
  () => import('@/components/TemplateSelector.vue')
)
```

### 2. 状态管理优化

**选择性订阅**:
```typescript
// 只订阅需要的状态
const results = computed(() => store.results)
```

**避免深度观察**:
```typescript
// 不要观察整个对象，只观察必要的属性
watch(() => store.config.count, (newVal) => {
  // 只在count变化时执行
})
```

### 3. 网络优化

**请求去重**:
API 层自动处理相同请求的去重。

**缓存**:
可考虑添加本地缓存模板数据。

**分页**:
历史记录和统计使用分页加载。

---

## 测试指南

### 运行测试

```bash
# 运行所有测试
npm test

# 运行特定文件的测试
npm test -- content-generation.test.ts

# 运行带覆盖率
npm run test:coverage

# 运行 UI 模式
npm run test:ui
```

### 测试覆盖

```
TemplateSelector Component
  ✓ 应该渲染模板分类
  ✓ 应该选择模板
  ✓ 应该按分类过滤

ConfigPanel Component
  ✓ 应该渲染配置表单
  ✓ 应该更新配置
  ✓ 应该管理关键词
  ✓ 应该验证产品选择

ResultsPanel Component
  ✓ 应该显示结果
  ✓ 应该编辑内容
  ✓ 应该评分结果
  ✓ 应该删除结果

Store Tests
  ✓ 初始化状态
  ✓ 模板操作
  ✓ 配置管理
  ✓ 结果操作

集成测试
  ✓ 完整生成流程
  ✓ 错误处理
```

---

## 部署检查清单

- [x] 所有文件已创建
- [x] 路由已配置
- [x] API 接口已定义
- [x] 类型定义完整
- [x] 状态管理就绪
- [x] 组件交互完成
- [x] 样式已应用
- [x] 测试已编写
- [x] 错误处理已实现
- [x] 文档已完成

### 部署前检查

```bash
# 1. 类型检查
npm run build

# 2. 运行测试
npm test

# 3. 代码质量检查
npm run lint

# 4. 预览构建
npm run preview
```

---

## 扩展建议

### 1. 添加数据持久化

```typescript
// 使用 localStorage 缓存配置
const persistConfig = () => {
  localStorage.setItem('contentStudioConfig',
    JSON.stringify(config.value))
}

const loadConfig = () => {
  const saved = localStorage.getItem('contentStudioConfig')
  if (saved) config.value = JSON.parse(saved)
}
```

### 2. 实现实时协作

```typescript
// WebSocket 支持多用户实时编辑
const collaborationWs = new WebSocket(...)
collaborationWs.onmessage = (event) => {
  const update = JSON.parse(event.data)
  // 实时同步用户编辑
}
```

### 3. 集成更多服务

```typescript
// 集成分析服务
trackEvent('content_generated', {
  template_id: config.template_id,
  count: config.count,
  success: true
})

// 集成存储服务
await uploadResultsToCloud(results)
```

### 4. 优化 UI/UX

- 添加拖拽排序结果
- 实现结果对比功能
- 添加社交分享功能
- 实现暗黑主题

---

## 常见问题

### Q: 如何添加新的模板分类？

A: 修改 `types/content-generation.ts` 中的 `TemplateCategory` 类型，然后在 `TemplateSelector.vue` 中添加对应的图标和标签。

### Q: 如何修改 API 端点？

A: 编辑 `api/content-generation.ts` 中的 API 调用，或修改 `.env` 中的 `VITE_API_BASE`。

### Q: 如何添加新的导出格式？

A: 在 `api/content-generation.ts` 中添加新的导出方法，在 `ResultsPanel.vue` 中添加下拉菜单选项。

### Q: 如何实现自动保存？

A: 在 `ConfigPanel.vue` 中 watch `contentStore.config` 的变化，定期调用保存方法。

---

## 参考资源

- Vue 3 文档: https://vuejs.org
- Pinia 文档: https://pinia.vuejs.org
- Element Plus 文档: https://element-plus.org
- TypeScript 文档: https://www.typescriptlang.org
- Vitest 文档: https://vitest.dev

