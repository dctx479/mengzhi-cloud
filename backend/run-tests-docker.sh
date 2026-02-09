#!/bin/bash
# 运行Docker隔离的测试环境

set -e

echo "🧪 启动Docker测试环境..."
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 清理旧的测试容器
echo "🧹 清理旧的测试容器..."
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true

# 构建测试镜像
echo ""
echo "🔨 构建测试镜像..."
docker-compose -f docker-compose.test.yml build --no-cache

# 启动测试服务
echo ""
echo "🚀 启动测试服务..."
docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner

# 获取退出代码
TEST_EXIT_CODE=$?

# 清理
echo ""
echo "🧹 清理测试环境..."
docker-compose -f docker-compose.test.yml down -v

# 显示结果
echo ""
echo "================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 测试通过！${NC}"
    echo "📊 覆盖率报告已生成: coverage_html/index.html"
    echo ""
    echo "查看覆盖率报告:"
    echo "  - HTML: open coverage_html/index.html"
    echo "  - XML:  cat coverage.xml"
else
    echo -e "${RED}❌ 测试失败！退出代码: $TEST_EXIT_CODE${NC}"
fi

exit $TEST_EXIT_CODE
