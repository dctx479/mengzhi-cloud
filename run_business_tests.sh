#!/bin/bash
# 业务流程测试执行脚本

echo "=========================================="
echo "业务流程自动化测试"
echo "=========================================="
echo ""

# 检查后端服务是否运行
echo "检查后端服务..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ 后端服务运行中"
else
    echo "✗ 后端服务未运行，请先启动后端服务"
    echo "  启动命令: cd backend && uvicorn app.main:app --reload"
    exit 1
fi

echo ""
echo "开始执行测试..."
echo ""

cd backend
python -m pytest tests/e2e/test_complete_flow.py -v -s --asyncio-mode=auto

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "测试报告: backend/TEST_REPORT.md"
