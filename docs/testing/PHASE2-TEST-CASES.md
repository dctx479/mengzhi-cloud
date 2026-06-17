# 核心模块测试用例（Phase 2 增强）

**版本**: v1.0  
**更新日期**: 2026-06-17  
**覆盖范围**: 文化元素 / IP 智能体 / 批量内容生成 / 告警 / 计费 / 对账

---

## 1. 文化元素系统

### 1.1 单元测试

**`backend/tests/test_cultural_elements.py`**

| ID | 用例 | 输入 | 期望 |
|---|---|---|---|
| CE-001 | 列出文化元素 | `GET /cultural/elements?page=1&page_size=20` | 返回 20 条，包含元数据 |
| CE-002 | 按 ID 查询 | `GET /cultural/elements/12` | 返回完整字段 |
| CE-003 | 按地域筛选 | `GET /cultural/graph/elements/by-region/锡林郭勒` | 仅返回该地域元素 |
| CE-004 | 智能匹配 | `POST /cultural/match {keywords: ["草原","羊肉"]}` | Top-5 相关元素 + 评分 |
| CE-005 | 知识图谱统计 | `GET /cultural/graph/statistics` | 节点数、边数、密度 |

### 1.2 集成测试

**`backend/tests/test_cultural_integration.py`**

| ID | 用例 | 流程 |
|---|---|---|
| CE-INT-001 | 产品创建触发采集 | 创建产品 → 检查自动触发采集任务 → 任务完成 → 元素入库 |
| CE-INT-002 | 人工审核工作流 | 触发采集 → 任务进入 pending → admin 领取 → 审核通过 → 元素激活 |

---

## 2. IP 智能体

### 2.1 单元测试

**`backend/tests/test_ip_agent.py`**

| ID | 用例 | 输入 | 期望 |
|---|---|---|---|
| IP-001 | 路由：小数 | "推荐一下羊肉" | XIAOSHU |
| IP-002 | 路由：小商 | "怎么直播带货" | XIAOSHANG |
| IP-003 | 路由：默认 | "你好" | XIAOSHU (默认) |
| IP-004 | 对话历史加权 | 近 3 轮都是小数 | XIAOSHU (+2) |
| IP-005 | 流式响应 | `POST /ip-chat/stream` | SSE 事件流 + done 帧含 cultural_elements |

### 2.2 集成测试

| ID | 用例 | 流程 |
|---|---|---|
| IP-INT-001 | 流式对话完整流程 | 登录 → 发起流式 → 接收所有 chunk → 累计 done 帧 → 验证文化元素非空 |
| IP-INT-002 | 非流式对话 | `POST /ip-chat/message` → 返回完整文本 + metadata |
| IP-INT-003 | 对话历史持久化 | 多轮对话 → 下一轮历史正确加载 |

---

## 3. 批量内容生成

### 3.1 单元测试（已存在 18 个）

**`backend/test_batch_content.py`**

| ID | 用例 | 验证 |
|---|---|---|
| BC-001 | 创建任务 | task_uuid 返回 + status=pending |
| BC-002 | 启动任务 | status=running + heartbeat 更新 |
| BC-003 | 列表查询 | 支持 status 筛选 |
| BC-004 | 任务详情 | results 数组正确 |
| BC-005 | 协作式取消 | 已生成内容保留 + status=cancelled |
| BC-006 | 重试失败 | retry_count += 1 + 重新执行失败项 |
| BC-007 | TXT 导出（流式）| StreamingResponse 分块正确 |
| BC-008 | DOCX 导出 | 文件可下载 + 格式正确 |
| BC-009 | PDF 导出 | 文件可下载 |
| BC-010 | 批量导出 | ZIP 包含所有任务 |
| BC-011 | 僵尸清理 | 启动时清理 > 5min 无心跳的 running |
| BC-012 | 并发：100 条 | Semaphore(10) + 100/批分块，< 30s 完成 |
| BC-013 | 配额不足 | 创建任务前预检 → 402 拒绝 |
| BC-014 | 配额回滚 | 任务失败时回滚扣减 |
| BC-015 | MagicMock vs AsyncMock | BackgroundTasks 必须用 AsyncMock |
| BC-016 | 任务状态机 | pending → running → completed/partial |
| BC-017 | retry_count 追踪 | 多次重试累加正确 |
| BC-018 | last_heartbeat_at | 每 30s 更新 |

---

## 4. 告警通知系统

### 4.1 单元测试

**`backend/tests/test_alerts.py`** (新增)

| ID | 用例 | 输入 | 期望 |
|---|---|---|---|
| AL-001 | 频率限制 | 同 level+title 连续 2 次 | 第二次仅 logger.debug |
| AL-002 | 优雅降级（凭证缺失）| ALERT_EMAIL_USERNAME="" | 返回 {email: False}，不抛错 |
| AL-003 | 渠道分派（channels 参数）| channels=["email"] | 仅 email 触发 |
| AL-004 | 输入校验（超长截断）| title 长度 2000 | 截断至 1000 字符 |
| AL-005 | 阿里云签名正确性 | 固定参数 | HMAC-SHA1 签名与官方文档一致 |
| AL-006 | 钉钉签名（可选）| 不配置 ALERT_DINGTALK_SECRET | 不签名，URL 无 sign 参数 |
| AL-007 | 钉钉签名（启用）| 配置 SECRET | URL 含 timestamp + sign |
| AL-008 | SMS 仅 ERROR/CRITICAL | level=warning | 不发短信 |
| AL-009 | @手机号透传 | extra={at_mobiles: [...]} | payload 含 at.atMobiles |

### 4.2 集成测试

| ID | 用例 | 流程 |
|---|---|---|
| AL-INT-001 | SMTP 邮件（mock）| mock smtplib → 验证 send_message 调用 |
| AL-INT-002 | 钉钉 HTTP（mock）| mock httpx → 验证 URL + payload |
| AL-INT-003 | 阿里云 HTTP（mock）| mock httpx → 验证签名 + params |

### 4.3 ai/monitor.py 兼容性

| ID | 用例 | 期望 |
|---|---|---|
| AL-MON-001 | `Monitor.send_alert(alert)` 签名兼容 | 调用方零修改 |
| AL-MON-002 | `_send_email_alert` 已移除 | 不再调用旧的本地方法 |
| AL-MON-003 | 渠道映射 `WEBHOOK → dingtalk` | 委托到 alert_manager 时正确映射 |

---

## 5. 计费方案自动绑定

### 5.1 单元测试（新增 4 个）

**`backend/tests/test_billing_engine.py`**

| ID | 用例 | 输入 | 期望 |
|---|---|---|---|
| BE-001 | 个人用户匹配 personal | user.enterprise_id=None + personal 方案 | 返回 personal 方案 |
| BE-002 | 企业用户匹配 enterprise | user.enterprise_id=1 + enterprise 方案 | 返回 enterprise 方案 |
| BE-003 | 无对应方案回退 default | 无 applicable_to 匹配 | 返回 is_default=True 方案 |
| BE-004 | 试用期检测 | user.created_at = 30 天前 + TRIAL_PERIOD_DAYS=14 | logger.info 标记 |
| BE-005 | 用户不存在 | user_id=999999 | 返回 default + warning log |

### 5.2 配额预警集成测试

| ID | 用例 | 流程 |
|---|---|---|
| QT-INT-001 | 企业配额预警 | 配额耗尽 → 查询 admin → NotificationService.notify_quota_alert → mock email/sms |
| QT-INT-002 | 用户配额预警 | 同上，无 enterprise_id |
| QT-INT-003 | 联系方式缺失 | admin 无 email → logger.info + 跳过邮件（不抛错）|

---

## 6. SLA + 对账框架

### 6.1 SLA 告警集成

**`backend/tests/test_sla_monitor.py`** (新增)

| ID | 用例 | 验证 |
|---|---|---|
| SLA-001 | severity=LOW → level=info | severity→level 映射 |
| SLA-002 | severity=MEDIUM → level=warning | 同上 |
| SLA-003 | severity=HIGH → level=error | 同上 |
| SLA-004 | severity=CRITICAL → level=critical | 同上 |
| SLA-005 | fire-and-forget | 事件循环活跃时 asyncio.create_task |
| SLA-006 | 同步上下文降级 | 无事件循环时 logger.warning |

### 6.2 对账单解析

**`backend/tests/test_bill_parsers.py`** (新增)

| ID | 用例 | 输入 | 期望 |
|---|---|---|---|
| BP-001 | WechatBillParser 解析示例 CSV | wechat_sample.csv | ≥5 条 RemoteTransaction |
| BP-002 | AlipayBillParser 解析示例 CSV | alipay_sample.csv | ≥5 条 RemoteTransaction |
| BP-003 | 字段映射：transaction_id | CSV "微信订单号"列 | 正确填充 |
| BP-004 | 字段映射：amount（含退款）| 订单金额-退款金额 | 净额正确 |
| BP-005 | 单行失败不影响整体 | 故意破坏第 3 行 | 该行跳过 + 其他行正常 |
| BP-006 | 编码自适应 | GBK 文件 | 自动识别 GBK |
| BP-007 | 文件大小超限 | 60MB 文件 | raise ValueError |
| BP-008 | 路径安全 | file_path 含 ".." | raise ValueError |

### 6.3 对账单下载器

| ID | 用例 | 验证 |
|---|----|---|
| BF-001 | Wechat Mock 模式 | API_KEY="" → 返回 wechat_sample.csv 路径 |
| BF-002 | Alipay Mock 模式 | 同上 |
| BF-003 | 真实模式触发 | API_KEY 非空 → logger.warning "would call real API" |
| BF-004 | query_transaction Mock | 返回 "SUCCESS" |

### 6.4 补单/查询/手动

| ID | 用例 | 验证 |
|---|---|---|
| RC-001 | _supplement_local_payment 成功 | 创建 Payment + 更新 Order + RESOLVED |
| RC-002 | _supplement_local_payment 失败 | db.rollback + 返回错误描述 |
| RC-003 | _query_remote_status | 调用对应 fetcher.query_transaction |
| RC-004 | _manual_supplement_transaction 成功 | 同 RC-001 + remark 标记 |
| RC-005 | _manual_supplement_transaction 缺 transaction_id | 返回错误描述，不抛错 |

---

## 7. 测试运行

```bash
cd backend
python -m pytest tests/test_cultural_elements.py -v
python -m pytest tests/test_ip_agent.py -v
python -m pytest tests/test_alerts.py -v
python -m pytest tests/test_billing_engine.py -v
python -m pytest tests/test_sla_monitor.py -v
python -m pytest tests/test_bill_parsers.py -v
python test_batch_content.py -v
```

---

## 8. 覆盖率目标

| 模块 | 当前 | 目标 |
|---|---|---|
| 告警系统 | - | 80% |
| 计费引擎 | 已有 | 85% |
| SLA 监控 | - | 75% |
| 对账服务 | - | 70% |
| IP 智能体 | 已有 | 90% |
| 文化元素 | 已有 | 85% |
| 批量生成 | 已有 | 85% |

---

## 9. 相关文档

- 测试策略: `docs/project-planning/09-TESTING-STRATEGY.md`
- 测试计划: `docs/testing/test-plan.md`
- 测试用例模板: `docs/testing/test-cases.md`
- 集成测试: `docs/testing/integration-test-cases.md`