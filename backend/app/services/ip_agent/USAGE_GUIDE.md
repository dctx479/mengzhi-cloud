# Prompt v2.0 (Opus 4.7优化版) 使用指南

> 本文档说明如何使用 `prompts_opus47.py` 中的优化版Prompt

---

## 🎯 快速对比

| 维度 | v1.0 | v2.0 (Opus 4.7) |
|------|------|----------------|
| Prompt长度 | ~2,500字符 | ~650字符 ⬇️ 74% |
| Few-shot数量 | 5个 | 3个 ⬇️ 40% |
| Token消耗 | ~3,000 | ~1,000 ⬇️ 67% |
| 对话风格 | 模板化 | 自然对话 |
| 推荐使用 | 参考对照 | ✅ 生产环境 |

**完整对比分析**: 查看 [PROMPT_COMPARISON.md](./PROMPT_COMPARISON.md)

---

## 🚀 基础使用

```python
from app.services.ip_agent.prompts_opus47 import (
    get_xiaoshu_prompt,
    get_xiaoshang_prompt,
    get_xiaoshu_examples,
    get_xiaoshang_examples,
    build_few_shot_messages
)

# 1. 获取System Prompt
xiaoshu_system = get_xiaoshu_prompt()

# 2. 构建对话消息
messages = [
    {"role": "system", "content": xiaoshu_system},
    *build_few_shot_messages(get_xiaoshu_examples(), limit=3),
    {"role": "user", "content": "你们的羊肉和超市买的有什么不一样？"}
]

# 3. 调用API
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1000,
    temperature=0.7,
    messages=messages
)
```

---

## 🎭 两个IP的区分

### 小数（文化传承者）

**人设**: 25岁牧民之子，大学毕业返乡创业  
**核心价值**: 让用户理解"为什么值这个价"  
**触发场景**: 产品咨询、选购建议、文化背景

**典型话术**:
- "最大的区别是..."（对比解释）
- "我爸说..."（个人经历）
- "我们家自己吃的也是这个"（建立信任）

---

### 小商（营销顾问）

**人设**: 30岁前互联网人，见过太多农企老板花冤枉钱  
**核心价值**: 用最小成本验证假设  
**触发场景**: 营销推广、品牌建设、运营咨询

**典型话术**:
- "核心是三件事..."（直接给答案）
- "我见过..."（经验背书）
- "丑话说在前面..."（预期管理）

---

## 🔀 智能路由

```python
def route_to_ip(user_input: str) -> str:
    """根据用户输入智能路由"""
    
    marketing_keywords = ["营销", "推广", "抖音", "直播", "卖货"]
    product_keywords = ["产地", "文化", "怎么选", "送礼"]
    
    if any(kw in user_input for kw in marketing_keywords):
        return "xiaoshang"
    elif any(kw in user_input for kw in product_keywords):
        return "xiaoshu"
    else:
        return "xiaoshu"  # 默认
```

---

## ⚙️ 推荐配置

```python
# Claude Opus 4.7参数
config = {
    "model": "claude-opus-4-7",
    "max_tokens": 1000,       # v2.0回复更简洁
    "temperature": 0.7,       # 保持创意但不偏离
    "top_p": 0.9
}

# Few-shot数量
# - 标准场景: 3个（推荐）
# - 复杂场景: 5个
# - 快速响应: 1个
```

---

## 📊 质量监控

```python
# 建议记录的指标
metrics = {
    "conversation_rounds": 0,     # 对话轮次
    "user_satisfaction": 0.0,     # 满意度（1-5）
    "conversion_rate": 0.0,       # 转化率
    "tokens_used": 0              # Token消耗
}
```

---

## 🐛 常见问题

### Q1: 如何处理角色边界？
**A**: 模型会自动引导。小数遇到营销问题会说"这个小商更专业"。

### Q2: 为什么删除emoji和加粗？
**A**: Opus 4.7不需要这些"强调"，过多标记反而降低自然度。

### Q3: 如何评估效果？
**A**: 建议A/B测试14天，对比满意度、转化率、Token成本。

---

## 📚 相关文档

- **完整对比分析**: [PROMPT_COMPARISON.md](./PROMPT_COMPARISON.md)
- **技术架构**: [IP-AGENT-ARCHITECTURE.md](../../docs/technical/IP-AGENT-ARCHITECTURE.md)
- **实施总结**: [README.md](./README.md)

---

**版本**: 2.0  
**更新**: 2026-06-12  
**维护**: AI赋能云平台团队
