#!/bin/bash
# Docker环境重建脚本
# 用途: 清理并重建完整的Docker环境（应用+监控+日志）

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Docker环境重建脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数: 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 切换到backend目录
cd "$(dirname "$0")/.." || exit 1

print_info "当前目录: $(pwd)"
echo ""

# Step 1: 停止所有容器
print_info "Step 1/6: 停止所有运行中的容器..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true
docker-compose -f docker-compose.test.yml down 2>/dev/null || true
print_info "✓ 容器已停止"
echo ""

# Step 2: 清理孤儿容器和网络
print_info "Step 2/6: 清理孤儿容器和未使用的网络..."
docker-compose -f docker-compose.yml down --remove-orphans 2>/dev/null || true
docker-compose -f docker-compose.monitoring.yml down --remove-orphans 2>/dev/null || true
docker network prune -f 2>/dev/null || true
print_info "✓ 清理完成"
echo ""

# Step 3: 询问是否清理数据卷
echo -e "${YELLOW}是否清理数据卷？(将删除所有数据库和日志数据) [y/N]${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    print_warn "清理数据卷中..."
    docker volume rm backend_mysql_data 2>/dev/null || true
    docker volume rm backend_redis_data 2>/dev/null || true
    docker volume rm backend_es_data 2>/dev/null || true
    docker volume rm backend_prometheus_data 2>/dev/null || true
    docker volume rm backend_grafana_data 2>/dev/null || true
    print_info "✓ 数据卷已清理"
else
    print_info "保留现有数据卷"
fi
echo ""

# Step 4: 重建镜像
print_info "Step 3/6: 重建Docker镜像（强制无缓存构建）..."
docker-compose -f docker-compose.yml build --no-cache backend
docker-compose -f docker-compose.test.yml build --no-cache test-runner 2>/dev/null || true
print_info "✓ 镜像构建完成"
echo ""

# Step 5: 拉取最新的第三方镜像
print_info "Step 4/6: 拉取最新的第三方镜像..."
docker-compose -f docker-compose.yml pull mysql redis nginx 2>/dev/null || true
docker-compose -f docker-compose.monitoring.yml pull 2>/dev/null || true
print_info "✓ 镜像拉取完成"
echo ""

# Step 6: 启动应用服务
print_info "Step 5/6: 启动应用服务..."
docker-compose -f docker-compose.yml up -d
print_info "等待服务健康检查..."
sleep 10

# 检查服务状态
print_info "检查服务状态:"
docker-compose -f docker-compose.yml ps
echo ""

# Step 7: 启动监控服务
print_info "Step 6/6: 启动监控和日志服务..."
docker-compose -f docker-compose.monitoring.yml up -d
print_info "等待监控服务启动..."
sleep 15

# 检查监控服务状态
print_info "检查监控服务状态:"
docker-compose -f docker-compose.monitoring.yml ps
echo ""

# Step 8: 健康检查
print_info "执行健康检查..."
echo ""

# 检查Backend
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    print_info "✓ Backend: 健康 (http://localhost:8001)"
else
    print_error "✗ Backend: 不健康"
fi

# 检查MySQL
if docker exec ai-platform-mysql mysqladmin ping -h localhost -u root -p123456 2>/dev/null | grep -q "alive"; then
    print_info "✓ MySQL: 运行中 (localhost:3309)"
else
    print_error "✗ MySQL: 未运行"
fi

# 检查Redis
if docker exec ai-platform-redis redis-cli -a redispass ping 2>/dev/null | grep -q "PONG"; then
    print_info "✓ Redis: 运行中 (localhost:6381)"
else
    print_error "✗ Redis: 未运行"
fi

# 检查Prometheus
if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
    print_info "✓ Prometheus: 健康 (http://localhost:9090)"
else
    print_error "✗ Prometheus: 不健康"
fi

# 检查Grafana
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    print_info "✓ Grafana: 健康 (http://localhost:3000)"
else
    print_error "✗ Grafana: 不健康"
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health | grep -q "cluster_name"; then
    print_info "✓ Elasticsearch: 运行中 (http://localhost:9200)"
else
    print_error "✗ Elasticsearch: 未运行"
fi

# 检查Kibana
if curl -s http://localhost:5601/api/status | grep -q "available"; then
    print_info "✓ Kibana: 可用 (http://localhost:5601)"
else
    print_error "✗ Kibana: 不可用"
fi

echo ""
print_info "=========================================="
print_info "Docker环境重建完成！"
print_info "=========================================="
echo ""
print_info "访问地址:"
echo "  - 应用API: http://localhost:8001"
echo "  - Nginx代理: http://localhost:8082"
echo "  - Grafana监控: http://localhost:3000 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Kibana日志: http://localhost:5601"
echo "  - Alertmanager: http://localhost:9093"
echo ""
print_info "查看日志:"
echo "  docker-compose -f docker-compose.yml logs -f backend"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f"
echo ""
print_info "停止服务:"
echo "  docker-compose -f docker-compose.yml down"
echo "  docker-compose -f docker-compose.monitoring.yml down"
echo ""
