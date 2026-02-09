# DeepSeek API 配置指南

## 概述

本文档介绍如何在AI赋能云平台中配置DeepSeek API密钥和相关参数。DeepSeek是一个强大的AI模型服务，为平台提供智能对话和文本生成能力。

## 配置项说明

### 必需配置项

| 配置项 | 说明 | 示例值 | 环境要求 |
|--------|------|--------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | `sk-xxxxxxxxxxxxxxxx` | 生产环境必需 |
| `DEEPSEEK_API_BASE` | API基础URL | `https://api.deepseek.com` | 所有环境 |
| `DEEPSEEK_MODEL` | 使用的模型名称 | `deepseek-chat` | 所有环境 |

### 可选配置项

| 配置项 | 说明 | 默认值 | 范围 |
|--------|------|--------|------|
| `DEEPSEEK_TIMEOUT` | API请求超时时间（秒） | `120` | 5-300 |
| `DEEPSEEK_STREAM_TIMEOUT` | 流式响应超时时间（秒） | `300` | 10-600 |
| `DEEPSEEK_MAX_RETRIES` | 最大重试次数 | `3` | 0-10 |
| `DEEPSEEK_MAX_TOKENS` | 最大token数 | `4096` | 1-32768 |
| `DEEPSEEK_TEMPERATURE` | 温度参数（控制随机性） | `0.7` | 0.0-2.0 |
| `DEEPSEEK_TOP_P` | Top-p参数（核采样） | `0.9` | 0.0-1.0 |

## 获取API密钥

1. 访问 [DeepSeek平台](https://platform.deepseek.com/api_keys)
2. 注册账号并登录
3. 在API密钥页面创建新的密钥
4. 复制生成的密钥（格式：`sk-xxxxxxxxxxxxxxxx`）

## 环境配置

### 开发环境 (.env.development)

```bash
# DeepSeek API配置
# 开发环境可以使用测试密钥或占位符
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
DEEPSEEK_STREAM_TIMEOUT=120
DEEPSEEK_MAX_RETRIES=3
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TOP_P=0.9
```

### 生产环境 (.env.production)

```bash
# DeepSeek API配置
# 生产环境必须使用真实的API密钥
DEEPSEEK_API_KEY=sk-your-actual-production-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60
DEEPSEEK_STREAM_TIMEOUT=300
DEEPSEEK_MAX_RETRIES=3
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TOP_P=0.9
```

### 测试环境 (.env)

```bash
# DeepSeek API配置
# 测试环境使用Mock或测试密钥
DEEPSEEK_API_KEY=test-api-key
DEEPSEEK_API_BASE=https://api.test.example.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=5
DEEPSEEK_STREAM_TIMEOUT=10
DEEPSEEK_MAX_RETRIES=1
DEEPSEEK_MAX_TOKENS=1024
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TOP_P=0.9
```

## 配置验证

系统会自动验证DeepSeek API配置的有效性：

### 生产环境验证规则

1. **API密钥必需性**：生产环境必须提供有效的API密钥
2. **格式验证**：API密钥必须以 `sk-` 开头
3. **长度验证**：API密钥长度不能少于20个字符
4. **占位符检查**：不能使用默认的占位符密钥

### 开发/测试环境

- 允许使用占位符密钥
- 允许空密钥（会在日志中警告）
- 跳过严格的格式验证

## 参数调优建议

### 温度参数 (DEEPSEEK_TEMPERATURE)

- **0.0-0.3**：适合需要准确、一致回答的场景（如FAQ、技术文档）
- **0.4-0.7**：平衡创造性和准确性（推荐用于大多数场景）
- **0.8-1.0**：适合需要创造性的场景（如创意写作、头脑风暴）
- **1.0+**：高度随机，适合实验性场景

### Top-p参数 (DEEPSEEK_TOP_P)

- **0.1-0.5**：保守选择，输出更加确定
- **0.6-0.9**：平衡选择（推荐）
- **0.9-1.0**：允许更多样化的输出

### 最大Token数 (DEEPSEEK_MAX_TOKENS)

根据使用场景调整：
- **短回答**：512-1024
- **中等回答**：1024-2048
- **长回答**：2048-4096
- **长文档**：4096+

## 错误处理

### 常见错误及解决方案

1. **API密钥无效**
   ```
   错误：DeepSeek API密钥格式不正确
   解决：检查密钥是否以 sk- 开头，确认复制完整
   ```

2. **请求超时**
   ```
   错误：API请求超时
   解决：增加 DEEPSEEK_TIMEOUT 值，检查网络连接
   ```

3. **配额不足**
   ```
   错误：API配额已用完
   解决：检查DeepSeek账户余额，升级套餐
   ```

4. **模型不存在**
   ```
   错误：指定的模型不存在
   解决：检查 DEEPSEEK_MODEL 配置，使用支持的模型名称
   ```

## 监控和日志

### 配置日志级别

在不同环境中设置适当的日志级别：

- **开发环境**：`DEBUG` - 显示详细的API调用信息
- **生产环境**：`INFO` - 记录关键操作和错误
- **测试环境**：`WARNING` - 仅记录警告和错误

### 监控指标

建议监控以下指标：

1. **API调用成功率**
2. **平均响应时间**
3. **Token使用量**
4. **错误率和错误类型**
5. **配额使用情况**

## 安全注意事项

1. **密钥保护**
   - 不要在代码中硬编码API密钥
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥

2. **访问控制**
   - 限制API密钥的使用权限
   - 监控异常的API调用模式
   - 设置合理的速率限制

3. **数据隐私**
   - 不要发送敏感用户数据到API
   - 遵守数据保护法规
   - 实施数据脱敏措施

## 故障排除

### 检查配置

```bash
# 验证配置文件语法
python -c "from app.core.config import settings; print('配置加载成功')"

# 检查API连接
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}' \
     https://api.deepseek.com/v1/chat/completions
```

### 常用调试命令

```bash
# 查看当前配置
python -c "from app.core.config import settings; print(f'Model: {settings.DEEPSEEK_MODEL}, Timeout: {settings.DEEPSEEK_TIMEOUT}')"

# 测试API连接
python -c "
from app.core.config import settings
print(f'API Base: {settings.DEEPSEEK_API_BASE}')
print(f'API Key: {settings.DEEPSEEK_API_KEY[:10]}...' if settings.DEEPSEEK_API_KEY else 'No API Key')
"
```

## 更新历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-01-23 | 初始版本，包含基础配置说明 |

## 相关文档

- [DeepSeek官方文档](https://platform.deepseek.com/docs)
- [API参考](https://platform.deepseek.com/api-docs)
- [平台配置指南](./config-guide.md)
- [环境部署指南](./deployment-guide.md)