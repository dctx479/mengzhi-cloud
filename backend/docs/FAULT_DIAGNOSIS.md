# 故障诊断流程

## 版本信息
- **版本**: v1.0
- **创建日期**: 2026-01-24
- **适用范围**: AI Platform 智能运维系统

## 一、故障诊断概述

### 1.1 诊断目标

- **快速定位**: 在 5 分钟内定位故障根因
- **准确分析**: 故障根因分析准确率 > 90%
- **自动化**: 80% 的故障可自动诊断
- **知识沉淀**: 诊断结果自动记录到知识库

### 1.2 诊断流程

```
告警触发 → 故障分类 → 信息收集 → 根因分析 → 生成诊断报告 → 推荐修复方案
```

## 二、故障分类与诊断

### 2.1 服务故障

#### 2.1.1 服务不可用 (ServiceDown)

**告警信息**:
```
AlertName: ServiceDown
Severity: Critical
Description: Backend service is down for more than 1 minute
Instance: ai-platform-backend:8000
```

**诊断步骤**:

**Step 1: 检查容器状态**
```bash
# 查看容器是否运行
docker ps -a | grep backend

# 检查容器日志
docker logs --tail 100 backend

# 检查容器重启次数
docker inspect backend | jq '.[0].RestartCount'
```

**可能原因**:
- 容器已停止或崩溃
- OOM (Out of Memory) 被 Kill
- 启动失败 (依赖服务不可用)

**Step 2: 检查进程状态**
```bash
# 进入容器检查进程
docker exec backend ps aux | grep uvicorn

# 检查端口监听
docker exec backend netstat -tlnp | grep 8000
```

**可能原因**:
- 进程启动失败
- 进程崩溃退出
- 端口被占用

**Step 3: 检查健康检查端点**
```bash
# 访问健康检查端点
curl -f http://localhost:8000/health

# 检查就绪检查
curl -f http://localhost:8000/ready
```

**可能原因**:
- 数据库连接失败
- Redis 连接失败
- 依赖服务不可用

**Step 4: 检查网络连通性**
```bash
# 检查容器网络
docker network inspect ai-platform_default

# 测试容器间通信
docker exec backend ping -c 3 postgres
docker exec backend ping -c 3 redis

# 检查 DNS 解析
docker exec backend nslookup postgres
```

**可能原因**:
- 网络配置错误
- DNS 解析失败
- 防火墙规则阻止

**诊断决策树**:
```
ServiceDown Alert
    |
    ├─ 容器未运行?
    │   ├─ Yes → 检查容器退出日志
    │   │   ├─ OOMKilled → 内存不足,需要增加内存
    │   │   ├─ ExitCode 1 → 启动失败,检查应用日志
    │   │   └─ ExitCode 137 → 被强制终止,检查系统日志
    │   │
    │   └─ No → 容器运行正常,继续检查
    │
    ├─ 进程未运行?
    │   ├─ Yes → 检查应用日志
    │   │   ├─ 数据库连接失败 → 检查数据库服务
    │   │   ├─ Redis 连接失败 → 检查 Redis 服务
    │   │   └─ 配置错误 → 检查环境变量和配置文件
    │   │
    │   └─ No → 进程运行正常,继续检查
    │
    ├─ 端口未监听?
    │   ├─ Yes → 检查端口配置
    │   │   ├─ 端口被占用 → 杀掉占用进程或更换端口
    │   │   └─ 监听地址错误 → 修改为 0.0.0.0
    │   │
    │   └─ No → 端口监听正常,继续检查
    │
    ├─ 健康检查失败?
    │   ├─ Yes → 检查依赖服务
    │   │   ├─ 数据库不可达 → 检查网络和数据库状态
    │   │   ├─ Redis 不可达 → 检查网络和 Redis 状态
    │   │   └─ 健康检查逻辑错误 → 修复健康检查代码
    │   │
    │   └─ No → 健康检查正常,继续检查
    │
    └─ 网络不可达?
        ├─ Yes → 检查网络配置
        │   ├─ DNS 解析失败 → 检查 /etc/hosts 或 DNS 服务
        │   ├─ 网络隔离 → 检查 Docker 网络配置
        │   └─ 防火墙阻止 → 检查 iptables 规则
        │
        └─ No → 其他未知原因,需要深入分析
```

**诊断脚本**:
```python
# scripts/diagnose_service_down.py

import subprocess
import json
import requests
from typing import Dict, Optional

def diagnose_service_down(container_name: str = "backend") -> Dict:
    """诊断服务不可用故障"""
    result = {
        "fault_type": "ServiceDown",
        "root_cause": None,
        "diagnosis_steps": [],
        "recommendations": []
    }

    # Step 1: 检查容器状态
    container_status = check_container_status(container_name)
    result["diagnosis_steps"].append({
        "step": 1,
        "action": "检查容器状态",
        "result": container_status
    })

    if not container_status["running"]:
        result["root_cause"] = f"容器未运行: {container_status['status']}"
        result["recommendations"].append("执行 docker restart " + container_name)
        return result

    # Step 2: 检查进程状态
    process_status = check_process_status(container_name)
    result["diagnosis_steps"].append({
        "step": 2,
        "action": "检查进程状态",
        "result": process_status
    })

    if not process_status["running"]:
        result["root_cause"] = "服务进程未运行"
        result["recommendations"].append("检查应用日志: docker logs " + container_name)
        return result

    # Step 3: 检查端口监听
    port_status = check_port_listening(container_name, 8000)
    result["diagnosis_steps"].append({
        "step": 3,
        "action": "检查端口监听",
        "result": port_status
    })

    if not port_status["listening"]:
        result["root_cause"] = "端口未监听"
        result["recommendations"].append("检查端口配置和占用情况")
        return result

    # Step 4: 检查健康检查
    health_status = check_health_endpoint(container_name)
    result["diagnosis_steps"].append({
        "step": 4,
        "action": "检查健康检查",
        "result": health_status
    })

    if not health_status["healthy"]:
        result["root_cause"] = f"健康检查失败: {health_status['error']}"
        result["recommendations"].append("检查依赖服务: 数据库, Redis, 外部API")
        return result

    # Step 5: 检查网络连通性
    network_status = check_network_connectivity(container_name)
    result["diagnosis_steps"].append({
        "step": 5,
        "action": "检查网络连通性",
        "result": network_status
    })

    if not network_status["reachable"]:
        result["root_cause"] = "网络不可达"
        result["recommendations"].append("检查 Docker 网络配置和 DNS 解析")
        return result

    # 未找到根因
    result["root_cause"] = "未知原因,需要深入分析"
    result["recommendations"].append("联系运维人员进行人工排查")

    return result

def check_container_status(container_name: str) -> Dict:
    """检查容器状态"""
    cmd = f"docker inspect {container_name}"
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if output.returncode != 0:
        return {"running": False, "status": "not_found"}

    data = json.loads(output.stdout)[0]
    state = data["State"]

    return {
        "running": state["Running"],
        "status": state["Status"],
        "exit_code": state.get("ExitCode"),
        "error": state.get("Error"),
        "oom_killed": state.get("OOMKilled", False),
        "restart_count": data["RestartCount"]
    }

def check_process_status(container_name: str) -> Dict:
    """检查进程状态"""
    cmd = f"docker exec {container_name} ps aux | grep uvicorn | grep -v grep"
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    return {
        "running": output.returncode == 0,
        "process": output.stdout.strip() if output.returncode == 0 else None
    }

def check_port_listening(container_name: str, port: int) -> Dict:
    """检查端口监听"""
    cmd = f"docker exec {container_name} netstat -tlnp | grep :{port}"
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    return {
        "listening": output.returncode == 0,
        "details": output.stdout.strip() if output.returncode == 0 else None
    }

def check_health_endpoint(container_name: str) -> Dict:
    """检查健康检查端点"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return {
            "healthy": response.status_code == 200,
            "status_code": response.status_code,
            "body": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

def check_network_connectivity(container_name: str) -> Dict:
    """检查网络连通性"""
    services = ["postgres", "redis"]
    results = {}

    for service in services:
        cmd = f"docker exec {container_name} ping -c 1 -W 1 {service}"
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        results[service] = output.returncode == 0

    return {
        "reachable": all(results.values()),
        "services": results
    }

if __name__ == "__main__":
    result = diagnose_service_down()
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

#### 2.1.2 服务响应慢 (HighResponseTime)

**告警信息**:
```
AlertName: HighResponseTime
Severity: Warning
Description: P90 response time > 2s
Current Value: 3.5s
```

**诊断步骤**:

**Step 1: 分析慢请求**
```bash
# 查看 Prometheus 慢请求统计
curl 'http://localhost:9090/api/v1/query?query=http_request_duration_seconds{quantile="0.9"}'

# 查看应用日志中的慢请求
docker logs backend | grep "slow request"
```

**Step 2: 检查数据库查询**
```sql
-- 查看慢查询日志
SELECT * FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 查看当前执行的查询
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
ORDER BY duration DESC;
```

**Step 3: 检查 Redis 性能**
```bash
# 连接 Redis
docker exec redis redis-cli

# 查看慢日志
SLOWLOG GET 10

# 查看当前连接数
INFO clients

# 查看命令统计
INFO commandstats
```

**Step 4: 检查系统资源**
```bash
# 查看 CPU 使用率
docker stats backend --no-stream

# 查看 IO 等待
docker exec backend iostat -x 1 5

# 查看网络延迟
docker exec backend ping -c 10 external-api.com
```

**根因分析**:
- 数据库查询慢 (缺少索引, N+1 查询)
- Redis 慢 (大 key, 阻塞命令)
- 外部 API 调用慢
- CPU/IO 瓶颈
- 并发请求过多

### 2.2 资源故障

#### 2.2.1 CPU 使用率过高 (HighCPUUsage)

**告警信息**:
```
AlertName: HighCPUUsage
Severity: Warning
Description: CPU usage > 80%
Current Value: 92%
```

**诊断步骤**:

**Step 1: 识别高 CPU 进程**
```bash
# 查看容器 CPU 使用率
docker stats --no-stream

# 查看进程 CPU 占用
docker exec backend top -bn1 | head -20

# 查看线程 CPU 占用
docker exec backend top -Hbn1 | head -20
```

**Step 2: 分析 CPU 占用原因**
```bash
# 生成火焰图 (需要安装 perf)
docker exec backend perf record -F 99 -p <pid> -g -- sleep 30
docker exec backend perf script | flamegraph.pl > flamegraph.svg

# 分析 Python 应用 (使用 py-spy)
docker exec backend py-spy top --pid <pid>
docker exec backend py-spy record -o profile.svg --pid <pid> -- sleep 30
```

**Step 3: 检查是否有死循环/死锁**
```python
# 使用 Python 调试工具
import pdb
import traceback

# 打印所有线程堆栈
import sys
import threading
for th in threading.enumerate():
    print(th)
    traceback.print_stack(sys._current_frames()[th.ident])
```

**Step 4: 检查请求量**
```bash
# 查询当前 QPS
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])'

# 查看并发连接数
docker exec backend netstat -an | grep ESTABLISHED | wc -l
```

**根因判断**:
```
如果 top 显示某个进程 CPU 100%:
    检查是否有死循环 → 代码 bug
    检查是否有大量计算 → 优化算法或异步处理

如果 CPU 使用分散在多个进程:
    检查 QPS 是否突增 → 流量洪峰,需要扩容
    检查是否有定时任务 → 优化定时任务执行时间

如果 CPU iowait 高:
    检查磁盘 IO → 磁盘性能瓶颈
    检查网络 IO → 网络带宽不足
```

#### 2.2.2 内存使用率过高 (HighMemoryUsage)

**告警信息**:
```
AlertName: HighMemoryUsage
Severity: Warning
Description: Memory usage > 85%
Current Value: 91%
```

**诊断步骤**:

**Step 1: 检查内存使用情况**
```bash
# 查看容器内存使用
docker stats backend --no-stream

# 查看系统内存
free -h

# 查看进程内存占用
docker exec backend ps aux --sort=-%mem | head -20
```

**Step 2: 分析内存泄漏**
```python
# 使用 memory_profiler
from memory_profiler import profile

@profile
def my_function():
    # 分析内存使用

# 使用 tracemalloc
import tracemalloc
tracemalloc.start()

# 运行代码

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

**Step 3: 检查缓存使用**
```bash
# 检查 Redis 内存
docker exec redis redis-cli INFO memory

# 查看 Redis 大 key
docker exec redis redis-cli --bigkeys

# 查看应用内存缓存
# (需要应用暴露内存统计接口)
curl http://localhost:8000/debug/memory
```

**Step 4: 检查数据库连接池**
```python
# 检查数据库连接数
from sqlalchemy import text
engine.execute(text("SELECT count(*) FROM pg_stat_activity"))

# 检查连接池状态
print(engine.pool.status())
```

**根因判断**:
```
内存持续增长,不释放:
    → 内存泄漏,检查代码中的循环引用、未关闭的文件句柄

内存突增后稳定:
    → 缓存或数据集过大,考虑限制缓存大小

内存周期性波动:
    → 正常的 GC 行为,可以调整 GC 参数优化
```

### 2.3 数据库故障

#### 2.3.1 数据库连接耗尽 (DatabaseConnectionPoolExhausted)

**诊断步骤**:
```sql
-- 查看当前连接数
SELECT count(*) FROM pg_stat_activity;

-- 查看连接池状态
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- 查看长时间空闲的连接
SELECT pid, usename, application_name, state, state_change
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '5 minutes';

-- 杀掉空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '5 minutes';
```

#### 2.3.2 查询响应慢 (SlowQuery)

**诊断步骤**:
```sql
-- 查看慢查询
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 分析查询执行计划
EXPLAIN ANALYZE <slow_query>;

-- 检查索引使用情况
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- 检查表大小
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

## 三、诊断工具

### 3.1 快速诊断脚本

```bash
#!/bin/bash
# scripts/quick-diagnose.sh

# 快速诊断脚本,收集所有诊断信息

OUTPUT_DIR="/tmp/diagnosis-$(date +%Y%m%d-%H%M%S)"
mkdir -p $OUTPUT_DIR

echo "开始收集诊断信息..."

# 1. 容器状态
docker ps -a > $OUTPUT_DIR/containers.txt
docker stats --no-stream > $OUTPUT_DIR/container-stats.txt

# 2. 系统资源
top -bn1 > $OUTPUT_DIR/top.txt
free -h > $OUTPUT_DIR/memory.txt
df -h > $OUTPUT_DIR/disk.txt
iostat -x 1 5 > $OUTPUT_DIR/iostat.txt

# 3. 网络状态
netstat -tulnp > $OUTPUT_DIR/netstat.txt
ss -s > $OUTPUT_DIR/socket-summary.txt

# 4. 应用日志
docker logs --tail 500 backend > $OUTPUT_DIR/backend.log
docker logs --tail 500 postgres > $OUTPUT_DIR/postgres.log
docker logs --tail 500 redis > $OUTPUT_DIR/redis.log

# 5. Prometheus 指标
curl 'http://localhost:9090/api/v1/query?query=up' > $OUTPUT_DIR/prometheus-up.json
curl 'http://localhost:9090/api/v1/query?query=http_request_duration_seconds' > $OUTPUT_DIR/prometheus-latency.json

# 6. 数据库状态
docker exec postgres psql -U ai_platform -c "SELECT * FROM pg_stat_activity;" > $OUTPUT_DIR/pg_stat_activity.txt
docker exec postgres psql -U ai_platform -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;" > $OUTPUT_DIR/pg_slow_queries.txt

# 7. Redis 状态
docker exec redis redis-cli INFO > $OUTPUT_DIR/redis-info.txt
docker exec redis redis-cli SLOWLOG GET 10 > $OUTPUT_DIR/redis-slowlog.txt

echo "诊断信息已保存到: $OUTPUT_DIR"
tar -czf $OUTPUT_DIR.tar.gz $OUTPUT_DIR
echo "打包文件: $OUTPUT_DIR.tar.gz"
```

### 3.2 诊断 API

```python
# app/api/v1/endpoints/diagnosis.py

from fastapi import APIRouter, HTTPException
from app.ops.diagnosis import DiagnosisEngine

router = APIRouter()

@router.post("/diagnose/service-down")
async def diagnose_service_down(container_name: str):
    """诊断服务不可用"""
    engine = DiagnosisEngine()
    result = await engine.diagnose_service_down(container_name)
    return result

@router.post("/diagnose/high-cpu")
async def diagnose_high_cpu(container_name: str):
    """诊断 CPU 使用率过高"""
    engine = DiagnosisEngine()
    result = await engine.diagnose_high_cpu(container_name)
    return result

@router.post("/diagnose/high-memory")
async def diagnose_high_memory(container_name: str):
    """诊断内存使用率过高"""
    engine = DiagnosisEngine()
    result = await engine.diagnose_high_memory(container_name)
    return result

@router.get("/diagnose/collect-info")
async def collect_diagnostic_info():
    """收集诊断信息"""
    engine = DiagnosisEngine()
    info = await engine.collect_diagnostic_info()
    return info
```

## 四、诊断报告模板

```markdown
# 故障诊断报告

## 基本信息
- 告警名称: ServiceDown
- 告警级别: Critical
- 告警时间: 2026-01-24 14:30:00
- 影响范围: Backend Service (全部用户)

## 故障现象
- Backend 服务不可用
- HTTP 请求返回 502 Bad Gateway
- Grafana 大盘显示服务下线

## 诊断过程

### Step 1: 检查容器状态
- 容器状态: Running
- 重启次数: 0
- 内存: 1.2GB / 2GB

### Step 2: 检查进程状态
- 进程运行: 否
- 错误信息: "Killed"

### Step 3: 检查应用日志
```
[2026-01-24 14:29:55] ERROR: MemoryError: Out of memory
[2026-01-24 14:29:56] INFO: Process terminated
```

## 根因分析
- **根本原因**: 内存不足 (OOM)
- **触发条件**: 处理大文件上传时,内存占用超过容器限制
- **影响时长**: 5 分钟

## 修复方案
- **临时修复**: 重启容器 (已执行)
- **永久修复**:
  1. 增加容器内存限制到 4GB
  2. 优化大文件处理逻辑,使用流式处理
  3. 添加内存监控告警

## 预防措施
- 添加 P1 告警: HighMemoryUsage (85%)
- 实施自动修复: 内存占用 > 90% 时自动重启
- 代码审查: 确保所有文件操作使用流式处理

## 后续行动
- [ ] 优化文件上传代码 (责任人: 开发团队, 期限: 2026-01-25)
- [ ] 增加内存限制 (责任人: 运维团队, 期限: 2026-01-24)
- [ ] 添加内存监控告警 (责任人: 运维团队, 期限: 2026-01-24)
```

## 五、总结

故障诊断的关键要素：

1. **系统化**: 遵循标准诊断流程,不遗漏关键步骤
2. **自动化**: 使用诊断脚本和 API,提高效率
3. **数据驱动**: 基于监控数据和日志,准确定位根因
4. **知识沉淀**: 记录诊断结果,持续优化诊断能力

通过智能诊断系统,可以实现：
- **快速响应**: 5 分钟内完成诊断
- **高准确率**: 90% 以上的根因分析准确率
- **自动化**: 80% 的故障自动诊断
