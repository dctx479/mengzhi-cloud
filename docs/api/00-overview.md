# API 文档

## 概览

AI赋能云平台提供RESTful API，支持产品浏览、AI对话、内容生成等功能。

**基础URL**: `http://localhost:3000/api`

## 认证方式

所有需要认证的API使用JWT Bearer Token认证：

```
Authorization: Bearer <your_token>
```

## API分类

- [认证API](./01-authentication.md) - 用户登录、注册、个人信息管理
- [产品API](./02-products.md) - 产品浏览、搜索、分类、评价
- [对话API](./03-chat.md) - AI对话、消息管理、文件上传
- [内容生成API](./04-content-generation.md) - AI内容生成、模板管理、批量任务
- [用户中心API](./05-user-center.md) - 订单、配额、设置、安全
- [错误码](./06-error-codes.md) - 错误码说明

## 通用响应格式

### 成功响应
```json
{
  "data": {},
  "message": "success"
}
```

### 错误响应
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 分页参数

大多数列表API支持分页：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | number | 1 | 页码 |
| pageSize | number | 20 | 每页数量 |

## 速率限制

- 未认证用户: 100次/小时
- 已认证用户: 1000次/小时
- AI对话: 50次/小时
- 内容生成: 100次/小时

## 版本历史

- v1.0.0 (2024-01) - 初始版本
