#!/bin/bash
# 简化的Docker环境检查

echo "=== Docker环境快速检查 ==="
echo ""

# 1. 检查Docker
echo "1. Docker状态:"
docker --version
echo ""

# 2. 验证配置
echo "2. 验证docker-compose配置:"
docker-compose -f docker-compose.dev.yml config --quiet && echo "✅ 配置有效" || echo "❌ 配置无效"
echo ""

# 3. 列出现有镜像
echo "3. 现有Docker镜像:"
docker images | grep agri || echo "暂无项目镜像"
echo ""

# 4. 列出运行中的容器
echo "4. 运行中的容器:"
docker ps --filter "name=agri" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "暂无运行中的容器"
echo ""

echo "=== 检查完成 ==="
echo ""
echo "下一步操作:"
echo "  构建镜像: docker-compose -f docker-compose.dev.yml build"
echo "  启动服务: docker-compose -f docker-compose.dev.yml up -d"
echo "  查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.dev.yml down"
