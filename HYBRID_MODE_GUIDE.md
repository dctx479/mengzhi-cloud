# 🔄 混合模式运行指南

**模式**: Docker基础服务 + 本地后端开发
**优势**: 快速启动、灵活调试、避免容器内代码问题

---

## ✅ 当前Docker服务

| 服务 | 状态 | 端口 | 用途 |
|------|------|------|------|
| MySQL | ✅ 运行中 | 3306 | 数据库 |
| Redis | ✅ 运行中 | 6379 | 缓存 |
| 前端 | ✅ 运行中 | 5173 | Web界面 |

---

## 🚀 启动本地后端

### 1. 停止Docker后端容器

```bash
docker-compose -f docker-compose.dev.yml stop backend
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

创建或编辑 `backend/.env` 文件：

```bash
# 数据库配置（连接到Docker MySQL）
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform

# Redis配置（连接到Docker Redis）
REDIS_URL=redis://localhost:6379/0

# 应用配置
APP_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# API配置
API_V1_PREFIX=/api/v1
```

### 4. 修复导入错误（可选）

如果遇到导入错误，在 `backend/app/schemas/chat.py` 末尾添加：

```python
# 类别名（兼容旧代码）
ConversationCreate = UpdateConversationRequest
ConversationUpdate = UpdateConversationRequest
ChatStreamRequest = StreamMessageRequest
ChatNonStreamRequest = SendMessageRequest
ChatNonStreamResponse = SendMessageResponse
FeedbackRequest = AddFeedbackRequest
```

### 5. 启动后端服务

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**或使用Python直接运行**:
```bash
python -m uvicorn app.main:app --reload
```

---

## 🔗 服务访问地址

### 开发环境

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | Vue开发服务器 |
| 后端API | http://localhost:8000 | FastAPI应用 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| MySQL | localhost:3306 | 数据库 |
| Redis | localhost:6379 | 缓存 |

### 数据库连接

```bash
# MySQL
mysql -h 127.0.0.1 -P 3306 -u root -proot123 agri_platform

# Redis
redis-cli -p 6379
```

---

## 🛠️ 开发工作流

### 日常开发

1. **启动Docker服务**（如果未运行）
   ```bash
   docker-compose -f docker-compose.dev.yml up -d mysql redis frontend
   ```

2. **启动本地后端**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **开发代码**
   - 修改代码自动热重载
   - 查看实时日志
   - 使用IDE调试

4. **停止服务**
   ```bash
   # 停止本地后端: Ctrl+C
   # 停止Docker服务:
   docker-compose -f docker-compose.dev.yml stop
   ```

### 代码检查

```bash
# 类型检查
cd backend
mypy app/

# 代码规范
flake8 app/

# 运行测试
pytest

# 代码格式化
black app/
```

---

## 🐛 故障排查

### 后端无法连接数据库

**问题**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查MySQL是否运行
docker-compose -f docker-compose.dev.yml ps mysql

# 检查端口是否开放
netstat -an | grep 3306

# 重启MySQL
docker-compose -f docker-compose.dev.yml restart mysql
```

### 后端无法连接Redis

**问题**: `Error connecting to Redis`

**解决**:
```bash
# 检查Redis是否运行
docker-compose -f docker-compose.dev.yml ps redis

# 测试连接
redis-cli -p 6379 ping

# 重启Redis
docker-compose -f docker-compose.dev.yml restart redis
```

### 导入错误

**问题**: `ImportError: cannot import name 'X'`

**解决**:
1. 检查 schemas/chat.py 是否有该类
2. 添加类别名（见上文第4步）
3. 或修改导入语句使用正确的类名

### 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

## 📊 性能对比

| 方面 | 完整Docker | 混合模式 |
|------|------------|----------|
| 启动速度 | 慢（~30秒） | 快（~5秒） |
| 热重载 | 有时不稳定 | 稳定 |
| 调试 | 困难 | 容易 |
| 日志查看 | 需要docker logs | 直接在终端 |
| IDE支持 | 有限 | 完整 |
| 环境一致性 | 高 | 中 |

---

## 💡 最佳实践

### 开发阶段（推荐混合模式）
- ✅ 快速迭代
- ✅ 方便调试
- ✅ IDE完整支持

### 测试阶段（使用完整Docker）
- ✅ 环境一致
- ✅ 集成测试
- ✅ 接近生产环境

### 生产部署（使用Docker）
- ✅ 完全隔离
- ✅ 易于扩展
- ✅ 统一管理

---

## 🎯 快速命令参考

```bash
# 启动Docker基础服务
docker-compose -f docker-compose.dev.yml up -d mysql redis frontend

# 停止Docker后端
docker-compose -f docker-compose.dev.yml stop backend

# 启动本地后端
cd backend && uvicorn app.main:app --reload

# 查看Docker服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看Docker日志
docker-compose -f docker-compose.dev.yml logs -f mysql

# 重启Docker服务
docker-compose -f docker-compose.dev.yml restart mysql redis

# 停止所有Docker服务
docker-compose -f docker-compose.dev.yml down
```

---

## ✅ 验证混合模式

### 检查清单

- [ ] MySQL运行正常: `docker ps | grep mysql`
- [ ] Redis运行正常: `docker ps | grep redis`
- [ ] 前端可访问: http://localhost:5173
- [ ] 后端依赖已安装: `pip list | grep fastapi`
- [ ] 环境变量已配置: `cat backend/.env`
- [ ] 后端可启动: `uvicorn app.main:app --reload`
- [ ] API文档可访问: http://localhost:8000/docs

---

**混合模式配置完成！** 🎉

现在您可以在本地灵活开发后端，同时利用Docker提供的稳定基础服务。
