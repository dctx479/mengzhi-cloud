# 前端设计规范
## Frontend Design Guide v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**技术栈**: Vue 3 + TypeScript + Element Plus + Vite

---

## 一、设计原则

### 1.1 核心原则

- **草原文化融合**: 配色/图标/交互体现草原元素
- **简洁高效**: 减少学习成本，3步内完成核心操作
- **响应式设计**: 支持桌面/平板/手机
- **无障碍友好**: 符合WCAG 2.1 AA标准

### 1.2 设计语言

**关键词**: 辽阔、温暖、自然、可信赖

---

## 二、视觉设计

### 2.1 配色方案

**主色调（草原绿）**:
```css
--primary-color: #4CAF50;       /* 草原绿 */
--primary-light: #81C784;       /* 浅绿 */
--primary-dark: #388E3C;        /* 深绿 */
```

**辅助色（天空蓝）**:
```css
--secondary-color: #2196F3;     /* 天空蓝 */
--secondary-light: #64B5F6;
--secondary-dark: #1976D2;
```

**中性色**:
```css
--text-primary: #212121;        /* 主文本 */
--text-secondary: #757575;      /* 次要文本 */
--text-disabled: #BDBDBD;       /* 禁用文本 */
--divider: #E0E0E0;             /* 分割线 */
--background: #FAFAFA;          /* 背景色 */
--surface: #FFFFFF;             /* 卡片背景 */
```

**功能色**:
```css
--success: #4CAF50;             /* 成功 */
--warning: #FF9800;             /* 警告 */
--error: #F44336;               /* 错误 */
--info: #2196F3;                /* 信息 */
```

### 2.2 字体规范

**字体家族**:
```css
font-family: 
  'PingFang SC', 
  'Microsoft YaHei', 
  'Helvetica Neue', 
  Arial, 
  sans-serif;
```

**字号体系**:
| 级别 | 大小 | 用途 | 行高 |
|-----|------|------|------|
| H1 | 28px | 页面标题 | 40px |
| H2 | 24px | 区块标题 | 32px |
| H3 | 20px | 卡片标题 | 28px |
| Body-L | 16px | 正文大号 | 24px |
| Body | 14px | 正文 | 22px |
| Body-S | 12px | 辅助文本 | 20px |

### 2.3 间距规范

**基础单位**: 8px

```css
--spacing-xs: 4px;    /* 0.5x */
--spacing-s: 8px;     /* 1x */
--spacing-m: 16px;    /* 2x */
--spacing-l: 24px;    /* 3x */
--spacing-xl: 32px;   /* 4x */
--spacing-xxl: 48px;  /* 6x */
```

### 2.4 圆角规范

```css
--radius-s: 4px;      /* 按钮/输入框 */
--radius-m: 8px;      /* 卡片 */
--radius-l: 12px;     /* 模态框 */
--radius-round: 50%;  /* 圆形头像 */
```

### 2.5 阴影规范

```css
--shadow-s: 0 2px 4px rgba(0,0,0,0.08);      /* 按钮悬停 */
--shadow-m: 0 4px 8px rgba(0,0,0,0.12);      /* 卡片 */
--shadow-l: 0 8px 16px rgba(0,0,0,0.16);     /* 模态框 */
```

---

## 三、组件设计

### 3.1 按钮规范

**主按钮**:
```vue
<el-button type="primary" size="default">
  生成品牌故事
</el-button>
```

**尺寸规范**:
- Large: 40px高，16px内边距
- Default: 32px高，12px内边距
- Small: 24px高，8px内边距

**状态**:
- 正常: primary-color
- 悬停: primary-dark + shadow-s
- 激活: primary-dark + 内阴影
- 禁用: opacity 0.4 + 禁止点击

### 3.2 表单规范

**输入框**:
```vue
<el-input 
  v-model="productName"
  placeholder="请输入产品名称"
  clearable
/>
```

**必填标识**:
```vue
<el-form-item label="产品名称" required>
  <el-input v-model="form.name" />
</el-form-item>
```

**错误提示**:
```vue
<el-form-item 
  label="产品名称" 
  :error="errors.name"
>
  <el-input v-model="form.name" />
</el-form-item>
```

### 3.3 卡片规范

**基础卡片**:
```vue
<el-card class="product-card" shadow="hover">
  <template #header>
    <div class="card-header">
      <span>锡林郭勒羊肉</span>
      <el-tag type="success">热销</el-tag>
    </div>
  </template>
  <div class="card-content">
    <img src="..." alt="产品图片" />
    <p class="description">草原散养...</p>
  </div>
</el-card>
```

**卡片间距**: 16px
**卡片内边距**: 20px
**卡片圆角**: 8px

### 3.4 对话气泡

**用户消息**:
```vue
<div class="message user">
  <div class="message-content">
    推荐一款羊肉
  </div>
  <el-avatar :src="userAvatar" />
</div>
```

**AI消息**:
```vue
<div class="message ai">
  <el-avatar :src="ipAvatar" />
  <div class="message-content">
    <div class="ip-name">小数</div>
    <div class="text">咱们草原上的羊肉...</div>
    <div class="suggestions">
      <el-button size="small" text>
        这款有什么特点？
      </el-button>
    </div>
  </div>
</div>
```

**样式**:
```css
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message.user .message-content {
  background: var(--primary-color);
  color: white;
  border-radius: 12px 12px 0 12px;
}

.message.ai .message-content {
  background: var(--surface);
  border: 1px solid var(--divider);
  border-radius: 12px 12px 12px 0;
}
```

---

## 四、页面布局

### 4.1 整体布局

```
┌─────────────────────────────────────────┐
│  顶部导航栏 (Header: 64px)              │
├───────┬─────────────────────────────────┤
│       │                                 │
│ 侧边栏│        主内容区                 │
│ 200px │     (Main Content)              │
│       │                                 │
│       │                                 │
└───────┴─────────────────────────────────┘
```

**响应式断点**:
- Desktop: ≥1200px
- Tablet: 768px - 1199px
- Mobile: <768px

### 4.2 顶部导航栏

**结构**:
```vue
<el-header class="navbar" height="64px">
  <div class="navbar-left">
    <img src="/logo.png" alt="蒙智云" class="logo" />
    <span class="brand-name">蒙智云</span>
  </div>
  
  <div class="navbar-center">
    <el-menu mode="horizontal" :default-active="activeMenu">
      <el-menu-item index="1">IP对话</el-menu-item>
      <el-menu-item index="2">营销工具</el-menu-item>
      <el-menu-item index="3">产品管理</el-menu-item>
    </el-menu>
  </div>
  
  <div class="navbar-right">
    <el-badge :value="3" class="notification">
      <el-icon><Bell /></el-icon>
    </el-badge>
    <el-dropdown>
      <el-avatar :src="userAvatar" />
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item>个人中心</el-dropdown-item>
          <el-dropdown-item divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</el-header>
```

### 4.3 侧边栏

**菜单结构**:
```vue
<el-aside width="200px" class="sidebar">
  <el-menu :default-active="activeMenu">
    <el-menu-item index="1">
      <el-icon><ChatDotRound /></el-icon>
      <span>IP对话</span>
    </el-menu-item>
    
    <el-sub-menu index="2">
      <template #title>
        <el-icon><Document /></el-icon>
        <span>营销工具</span>
      </template>
      <el-menu-item index="2-1">品牌故事</el-menu-item>
      <el-menu-item index="2-2">直播脚本</el-menu-item>
      <el-menu-item index="2-3">内容适配</el-menu-item>
    </el-sub-menu>
    
    <el-menu-item index="3">
      <el-icon><Goods /></el-icon>
      <span>产品管理</span>
    </el-menu-item>
    
    <el-menu-item index="4">
      <el-icon><DataLine /></el-icon>
      <span>数据看板</span>
    </el-menu-item>
  </el-menu>
</el-aside>
```

### 4.4 IP对话页面

**布局**:
```vue
<div class="chat-container">
  <!-- 左侧：IP切换 + 历史会话 -->
  <aside class="chat-sidebar" style="width: 280px;">
    <div class="ip-selector">
      <el-radio-group v-model="currentIP">
        <el-radio-button label="xiaoshu">
          <el-avatar src="/xiaoshu.png" size="small" />
          小数
        </el-radio-button>
        <el-radio-button label="xiaoshang">
          <el-avatar src="/xiaoshang.png" size="small" />
          小商
        </el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="session-history">
      <div class="session-item" v-for="session in sessions">
        <span class="session-title">产品咨询</span>
        <span class="session-time">2小时前</span>
      </div>
    </div>
  </aside>
  
  <!-- 中间：对话区 -->
  <main class="chat-main">
    <div class="message-list" ref="messageList">
      <MessageItem 
        v-for="msg in messages" 
        :key="msg.id"
        :message="msg"
      />
    </div>
    
    <div class="chat-input">
      <el-input 
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入消息..."
        @keydown.enter.ctrl="sendMessage"
      />
      <el-button type="primary" @click="sendMessage">
        发送 (Ctrl+Enter)
      </el-button>
    </div>
  </main>
  
  <!-- 右侧：上下文信息 -->
  <aside class="chat-context" style="width: 320px;">
    <el-card header="当前产品">
      <div class="context-product">
        <img src="..." alt="产品" />
        <div>
          <h4>锡林郭勒羊肉</h4>
          <p>产地：锡林郭勒</p>
        </div>
      </div>
    </el-card>
    
    <el-card header="相关文化">
      <el-tag 
        v-for="culture in cultures"
        :key="culture"
        class="culture-tag"
      >
        {{ culture }}
      </el-tag>
    </el-card>
  </aside>
</div>
```

---

## 五、交互设计

### 5.1 加载状态

**骨架屏**（首次加载）:
```vue
<el-skeleton :rows="5" animated />
```

**Spinner**（短时加载）:
```vue
<el-icon class="is-loading"><Loading /></el-icon>
```

**进度条**（长时任务）:
```vue
<el-progress 
  :percentage="progress" 
  :status="status"
/>
```

### 5.2 空状态

```vue
<el-empty 
  description="还没有对话记录"
  :image-size="200"
>
  <el-button type="primary">
    开始对话
  </el-button>
</el-empty>
```

### 5.3 消息提示

**成功提示**:
```typescript
ElMessage.success('品牌故事生成成功！')
```

**错误提示**:
```typescript
ElMessage.error('生成失败，请稍后重试')
```

**确认对话**:
```typescript
ElMessageBox.confirm(
  '确定要删除这篇品牌故事吗？',
  '提示',
  {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }
)
```

### 5.4 动画效果

**页面切换**:
```css
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all 0.3s ease;
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
```

**消息滚动**:
```typescript
// 新消息自动滚动到底部
nextTick(() => {
  messageListRef.value.scrollTo({
    top: messageListRef.value.scrollHeight,
    behavior: 'smooth'
  })
})
```

---

## 六、响应式设计

### 6.1 移动端适配

**隐藏侧边栏**（<768px）:
```css
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -200px;
    transition: left 0.3s;
  }
  
  .sidebar.open {
    left: 0;
    z-index: 1000;
  }
}
```

**对话页面单列**:
```css
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .chat-sidebar,
  .chat-context {
    width: 100%;
  }
}
```

### 6.2 触摸优化

**按钮最小尺寸**: 44x44px（移动端）
**点击区域扩大**: padding增加

---

## 七、无障碍设计

### 7.1 语义化标签

```html
<nav aria-label="主导航">
  <ul role="menubar">
    <li role="menuitem">IP对话</li>
  </ul>
</nav>
```

### 7.2 键盘导航

**Tab顺序**: 逻辑顺序（从左到右，从上到下）
**焦点样式**: 明显的outline

```css
:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
```

### 7.3 颜色对比度

**文本对比度**: ≥4.5:1（正文）
**大号文本**: ≥3:1（≥18px）

---

## 八、性能优化

### 8.1 图片优化

- 使用WebP格式（fallback PNG/JPG）
- 懒加载: `<img loading="lazy" />`
- 响应式图片: `srcset`

### 8.2 代码分割

```typescript
// 路由懒加载
const IPChat = () => import('@/views/IPChat.vue')
const BrandStory = () => import('@/views/BrandStory.vue')
```

### 8.3 虚拟滚动

长列表使用虚拟滚动:
```vue
<el-virtual-list 
  :data="messages"
  :item-size="80"
  height="600px"
>
  <template #default="{ item }">
    <MessageItem :message="item" />
  </template>
</el-virtual-list>
```

---

## 九、设计资源

### 9.1 图标库

**Element Plus图标**: 优先使用
```vue
<el-icon><ChatDotRound /></el-icon>
```

**自定义图标**: 草原元素SVG
- 蒙古包
- 马头琴
- 敖包
- 哈达

### 9.2 插画

**场景插画**:
- 空状态插画（草原风景）
- 加载插画（羊群奔跑）
- 404页面（迷路的羊）

### 9.3 设计稿

**Figma设计稿**: [待补充链接]

包含:
- 所有页面高保真原型
- 组件库
- 设计规范标注

---

## 十、开发规范

### 10.1 组件命名

**文件名**: PascalCase
```
components/
  ├── IPChat/
  │   ├── MessageItem.vue
  │   ├── ChatInput.vue
  │   └── SessionList.vue
```

**组件名**:
```vue
<script setup lang="ts">
defineOptions({
  name: 'MessageItem'
})
</script>
```

### 10.2 样式管理

**Scoped样式**:
```vue
<style scoped lang="scss">
.message {
  &.user {
    flex-direction: row-reverse;
  }
}
</style>
```

**全局样式**: `styles/variables.scss`

### 10.3 TypeScript类型

```typescript
interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  timestamp: number
  suggestions?: string[]
}
```

---

**文档结束**

> 设计规范应随产品迭代持续优化，每个Sprint回顾一次用户反馈。
