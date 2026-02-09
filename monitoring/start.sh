#!/bin/bash
# 监控系统快速启动脚本

set -e

echo "=========================================="
echo "  支付系统监控告警系统 - 快速启动"
echo "=========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未安装 Docker Compose"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/prometheus data/grafana data/alertmanager

# 设置权限
echo "🔐 设置目录权限..."
chmod -R 777 data/

echo ""
echo "🚀 启动监控服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "  监控系统启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000"
echo "  - Alertmanager:  http://localhost:9093"
echo ""
echo "Grafana 默认登录:"
echo "  用户名: admin"
echo "  密码:   admin123"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""
echo "=========================================="
