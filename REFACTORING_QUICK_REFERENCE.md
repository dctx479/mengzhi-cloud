# 认证模块重构 - 快速参考指南

## 新增的私有方法总览

### register() 相关方法
1. `_validate_register_input(request)` - 验证输入参数
2. `_check_existing_user(request)` - 检查用户唯一性
3. `_create_enterprise_if_needed(request)` - 创建企业
4. `_create_user_record(request, enterprise_id)` - 创建用户记录

### login() 相关方法
1. `_find_user(identifier)` - 查找用户
2. `_validate_credentials(user, password)` - 验证密码
3. `_generate_login_tokens(user, device_id, ip_address)` - 生成Token
4. `_update_successful_login(user_id)` - 更新登录信息

## 文件修改总结

| 文件 | 修改内容 | 影响 |
|------|---------|------|
| auth_service.py | +8个私有方法 (263行) | 零 breaking change |
| auth.py register | -113行 | 功能不变 |
| auth.py login | -52行 | 功能不变 |

## 错误处理对应表

### 注册错误
- Email/Phone 都缺 -> _validate_register_input()
- 用户名已存在 -> _check_existing_user()
- 邮箱已存在 -> _check_existing_user()
- 手机已存在 -> _check_existing_user()
- 营业执照已存在 -> _create_enterprise_if_needed()

### 登录错误
- 用户不存在 -> _find_user()
- 密码错误 -> _validate_credentials()
- 账号被锁定 -> check_account_status()
- 登录失败5次 -> _validate_credentials()

## 测试写法示例

```python
def test_validate_register_input():
    auth_service = AuthService(db)
    with pytest.raises(ValidationError):
        auth_service._validate_register_input(bad_request)

def test_find_user():
    user = auth_service._find_user("testuser")
    assert user is not None
```

## 扩展功能建议

1. SMS 一键登录 -> 新增 _create_user_from_sms()
2. OAuth 登录 -> 新增 _find_or_create_oauth_user()
3. 社交登录 -> 新增 _sync_social_user()

## 部署清单

- [ ] 部署 auth_service.py
- [ ] 部署 auth.py
- [ ] 运行集成测试
- [ ] 验证登录/注册
- [ ] (可选) 新增单元测试

---
版本: 1.0 | 更新: 2026-01-23
