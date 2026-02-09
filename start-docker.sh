#!/bin/bash
# Docker环境一键启动脚本

echo "🐳 启动Docker开发环境..."
echo ""

# 构建并启动
docker-compose -f docker-compose.dev.yml up -d --build

echo ""
echo "⏳ 等待服务启动..."
sleep 30

echo ""
echo "📊 服务状态:"
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "✅ 环境已启动！"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.dev.yml down"
