# 环境要求

## 硬件要求

### 最低配置（开发环境）
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB可用空间

### 推荐配置（生产环境）
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB+ SSD

## 软件要求

### 操作系统
- Linux (Ubuntu 20.04+, CentOS 7+)
- macOS 10.15+
- Windows 10/11 (WSL2推荐)

### 必需软件

#### Python
- **版本**: Python 3.11 或更高
- **验证**: `python --version` 或 `python3 --version`
- **安装**:
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3-pip

  # macOS
  brew install python@3.11

  # Windows
  # 从 https://www.python.org/downloads/ 下载安装
  ```

#### Node.js
- **版本**: Node.js 20.x LTS 或更高
- **验证**: `node --version`
- **安装**:
  ```bash
  # Ubuntu/Debian (使用NodeSource)
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs

  # macOS
  brew install node@20

  # Windows
  # 从 https://nodejs.org/ 下载安装
  ```

#### MySQL
- **版本**: MySQL 8.0 或更高
- **验证**: `mysql --version`
- **安装**:
  ```bash
  # Ubuntu/Debian
  sudo apt install mysql-server-8.0

  # macOS
  brew install mysql@8.0

  # Windows
  # 从 https://dev.mysql.com/downloads/mysql/ 下载安装
  ```

#### Redis
- **版本**: Redis 7.x 或更高
- **验证**: `redis-server --version`
- **安装**:
  ```bash
  # Ubuntu/Debian
  sudo apt install redis-server

  # macOS
  brew install redis

  # Windows
  # 使用 WSL2 或从 https://github.com/microsoftarchive/redis/releases 下载
  ```

### Docker部署（推荐）

如果使用Docker部署，只需安装：

#### Docker
- **版本**: Docker 20.10+
- **验证**: `docker --version`
- **安装**:
  ```bash
  # Ubuntu/Debian
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh

  # macOS/Windows
  # 安装 Docker Desktop: https://www.docker.com/products/docker-desktop
  ```

#### Docker Compose
- **版本**: Docker Compose 2.0+
- **验证**: `docker-compose --version`
- **安装**: Docker Desktop自带，Linux需单独安装
  ```bash
  # Linux
  sudo apt install docker-compose-plugin
  ```

## 网络要求

### 端口占用
确保以下端口未被占用：
- **3306**: MySQL数据库
- **6379**: Redis缓存
- **8000**: 后端API服务
- **5173**: 前端开发服务器（开发环境）
- **80**: Nginx/前端服务（生产环境）

### 外部服务访问
- **DeepSeek API**: 需要访问 `https://api.deepseek.com`
- **NPM Registry**: 需要访问 `https://registry.npmjs.org`
- **PyPI**: 需要访问 `https://pypi.org`

## 依赖版本矩阵

### Python依赖（requirements.txt）
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
sqlalchemy==2.0.25
pymysql==1.1.0
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
alembic==1.13.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4
numpy==1.24.0
pandas==2.0.3
```

### Node.js依赖（package.json）
```json
{
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.5.4",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "vite": "^5.0.11",
    "typescript": "^5.3.3",
    "vue-tsc": "^1.8.27"
  }
}
```

## 验证环境

运行以下脚本验证环境是否满足要求：

```bash
#!/bin/bash
echo "=== 环境检查 ==="

# Python
python3 --version || echo "❌ Python未安装"

# Node.js
node --version || echo "❌ Node.js未安装"
npm --version || echo "❌ NPM未安装"

# MySQL
mysql --version || echo "❌ MySQL未安装"

# Redis
redis-server --version || echo "❌ Redis未安装"

# Docker (可选)
docker --version || echo "⚠️  Docker未安装（可选）"
docker-compose --version || echo "⚠️  Docker Compose未安装（可选）"

echo "=== 检查完成 ==="
```

## 下一步

环境准备完成后，请继续：
- [本地开发部署](./local-development.md)
- [Docker部署](./docker-deployment.md)
