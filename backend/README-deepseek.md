# DeepSeek API 快速配置指南

## 🚀 快速开始

### 1. 获取API密钥
访问 [DeepSeek平台](https://platform.deepseek.com/api_keys) 获取API密钥

### 2. 配置环境变量

**开发环境** (`.env.development`):
```bash
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

**生产环境** (`.env.production`):
```bash
DEEPSEEK_API_KEY=sk-your-production-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60
DEEPSEEK_MAX_RETRIES=3
```

### 3. 验证配置

```bash
# 启动应用验证配置
python -c "from app.core.config import settings; print('✅ DeepSeek配置加载成功')"
```

## ⚙️ 核心配置项

| 配置项 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | ✅ | - | API密钥（sk-开头） |
| `DEEPSEEK_API_BASE` | ✅ | `https://api.deepseek.com` | API基础URL |
| `DEEPSEEK_MODEL` | ✅ | `deepseek-chat` | 模型名称 |
| `DEEPSEEK_TIMEOUT` | ❌ | `120` | 超时时间（秒） |
| `DEEPSEEK_MAX_RETRIES` | ❌ | `3` | 最大重试次数 |

## 🔧 高级配置

```bash
# 模型参数调优
DEEPSEEK_MAX_TOKENS=4096      # 最大输出长度
DEEPSEEK_TEMPERATURE=0.7      # 创造性 (0.0-2.0)
DEEPSEEK_TOP_P=0.9           # 多样性 (0.0-1.0)

# 性能优化
DEEPSEEK_STREAM_TIMEOUT=300   # 流式响应超时
DEEPSEEK_MAX_RETRIES=3        # 重试次数
```

## ⚠️ 注意事项

1. **生产环境**必须使用真实API密钥
2. API密钥格式：`sk-xxxxxxxxxxxxxxxx`
3. 不要在代码中硬编码密钥
4. 定期检查API配额使用情况

## 🐛 常见问题

**Q: API密钥验证失败？**
A: 检查密钥是否以`sk-`开头，确认复制完整

**Q: 请求超时？**
A: 增加`DEEPSEEK_TIMEOUT`值，检查网络连接

**Q: 配额不足？**
A: 登录DeepSeek平台检查账户余额

## 📚 详细文档

完整配置说明请参考：[DeepSeek配置详细指南](./deepseek-config.md)