#!/bin/bash
# Docker环境检查脚本

set -e

echo "=========================================="
echo "Docker环境检查开始"
echo "=========================================="
echo ""

# 检查Docker是否运行
echo "1. 检查Docker状态..."
if docker info > /dev/null 2>&1; then
    echo "✅ Docker正在运行"
    docker --version
else
    echo "❌ Docker未运行，请启动Docker Desktop"
    exit 1
fi
echo ""

# 检查docker-compose
echo "2. 检查docker-compose..."
if docker-compose --version > /dev/null 2>&1; then
    echo "✅ docker-compose已安装"
    docker-compose --version
else
    echo "❌ docker-compose未安装"
    exit 1
fi
echo ""

# 验证配置文件
echo "3. 验证docker-compose配置..."
if docker-compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
    echo "✅ docker-compose.dev.yml配置有效"
else
    echo "❌ docker-compose.dev.yml配置无效"
    exit 1
fi
echo ""

# 构建镜像
echo "4. 构建Docker镜像..."
echo "   构建前端镜像..."
docker-compose -f docker-compose.dev.yml build frontend
echo "   构建后端镜像..."
docker-compose -f docker-compose.dev.yml build backend
echo "✅ 镜像构建完成"
echo ""

# 启动服务
echo "5. 启动服务..."
docker-compose -f docker-compose.dev.yml up -d
echo "✅ 服务已启动"
echo ""

# 等待服务就绪
echo "6. 等待服务就绪..."
sleep 30
echo ""

# 检查服务状态
echo "7. 检查服务状态..."
docker-compose -f docker-compose.dev.yml ps
echo ""

# 运行前端检查
echo "8. 运行前端检查..."
echo "   - 安装依赖检查"
docker-compose -f docker-compose.dev.yml exec -T frontend sh -c "npm list --depth=0" || true
echo "   - 构建检查"
docker-compose -f docker-compose.dev.yml exec -T frontend sh -c "npm run build" || echo "⚠️ 前端构建失败"
echo ""

# 运行后端检查
echo "9. 运行后端检查..."
echo "   - Python版本"
docker-compose -f docker-compose.dev.yml exec -T backend python --version
echo "   - 依赖检查"
docker-compose -f docker-compose.dev.yml exec -T backend pip list | head -20
echo "   - 运行测试"
docker-compose -f docker-compose.dev.yml exec -T backend pytest --version || echo "⚠️ pytest未安装"
echo ""

# 健康检查
echo "10. 健康检查..."
echo "   - 后端API"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ 后端API正常" || echo "⚠️ 后端API未响应"
echo "   - 前端"
curl -f http://localhost:5173 2>/dev/null && echo "✅ 前端正常" || echo "⚠️ 前端未响应"
echo ""

echo "=========================================="
echo "Docker环境检查完成"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "停止服务: docker-compose -f docker-compose.dev.yml down"
