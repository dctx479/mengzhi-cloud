#!/bin/bash
# Docker环境一键启动脚本

set -e

echo "🐳 启动 Docker 部署环境..."
echo ""

# 如果根目录没有 .env.docker，从模板复制
if [ ! -f .env.docker ]; then
    echo "📋 未找到 .env.docker，从 .env.docker.example 复制..."
    cp .env.docker.example .env.docker
    echo "   已创建 .env.docker，请编辑其中的密钥后重新运行"
    echo ""
fi

# 构建并启动（生产模式）
docker compose up -d --build

echo ""
echo "⏳ 等待服务就绪..."
sleep 20

echo ""
echo "📊 服务状态:"
docker compose ps

echo ""
echo "✅ 部署完成！"
echo ""
echo "访问地址:"
echo "  前端:    http://localhost:${FRONTEND_PORT:-80}"
echo "  后端API: http://localhost:${BACKEND_PORT:-8000}"
echo "  API文档: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "常用命令:"
echo "  查看日志: docker compose logs -f"
echo "  停止服务: docker compose down"
echo "  重启服务: docker compose restart"
