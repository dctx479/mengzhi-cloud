# 内存泄漏故障排查手册

## 概述

### 问题描述
应用运行过程中内存使用持续增长,长时间不释放,最终导致OOM (Out of Memory) Kill或系统性能严重下降。

### 影响范围
- **影响级别**: Warning → Critical → System Crash
- **影响用户**: 逐渐增加,最终全部用户
- **业务影响**: 响应缓慢 → 频繁重启 → 服务不可用
- **系统影响**: 可能导致宿主机内存耗尽
- **优先级**: 高优先级,需要持续跟踪

### 典型场景
- Python对象引用未释放
- 缓存无限增长
- 数据库连接泄漏
- 文件句柄未关闭
- 第三方库内存泄漏

---

## 症状识别

### 监控告警

**Warning级别**:
```
AlertName: HighMemoryUsage
Severity: Warning
Description: Memory usage > 85% for 5 minutes
Current Value: 88%
Trend: Increasing
```

**Critical级别**:
```
AlertName: CriticalMemoryUsage
Severity: Critical
Description: Memory usage > 95%
Current Value: 97%
Trend: Rapidly increasing
```

**OOM事件**:
```
AlertName: ContainerOOMKilled
Severity: Critical
Description: Container killed due to OOM
Exit Code: 137
OOMKilled: true
```

### 用户表现
- 早期: 无明显感知
- 中期: 请求偶尔超时
- 晚期: 服务频繁重启,无法使用

### Grafana 大盘特征
- "Memory Usage" 持续上升趋势 (📈)
- "Container Restarts" 计数增加
- "GC Time" 显著增加
- "Available Memory" 持续下降

### 内存泄漏判断标准

```mermaid
graph LR
    A[监控内存趋势] --> B{持续增长?}
    B -->|是| C{重启后归零?}
    B -->|否| Z[正常波动]

    C -->|是| D{再次增长?}
    C -->|否| Z2[配置不足]

    D -->|是| E[确认内存泄漏]
    D -->|否| Z3[偶发事件]

    E --> F[定位泄漏源]
