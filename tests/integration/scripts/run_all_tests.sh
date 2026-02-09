#!/bin/bash

# 集成测试执行脚本
# 功能：执行所有集成测试并生成报告

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TESTS_DIR="$PROJECT_ROOT/tests/integration"
REPORTS_DIR="$PROJECT_ROOT/tests/reports"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}集成测试执行脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 创建报告目录
mkdir -p "$REPORTS_DIR"

# 检查后端服务
check_backend() {
    echo -e "${YELLOW}检查后端服务...${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务运行正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 后端服务未运行${NC}"
        echo -e "${YELLOW}请先启动后端服务: cd backend && uvicorn app.main:app --reload${NC}"
        return 1
    fi
}

# 检查前端服务
check_frontend() {
    echo -e "${YELLOW}检查前端服务...${NC}"
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务运行正常${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 前端服务未运行（部分测试可能跳过）${NC}"
        return 0  # 前端不是必须的
    fi
}

# 检查Python依赖
check_python_deps() {
    echo -e "${YELLOW}检查Python依赖...${NC}"
    if python -c "import httpx" 2>/dev/null; then
        echo -e "${GREEN}✓ Python依赖已安装${NC}"
        return 0
    else
        echo -e "${RED}✗ 缺少Python依赖${NC}"
        echo -e "${YELLOW}安装依赖: pip install httpx${NC}"
        return 1
    fi
}

# 执行API集成测试
run_api_tests() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}执行API集成测试${NC}"
    echo -e "${BLUE}========================================${NC}"

    cd "$TESTS_DIR/scripts"

    if python test_api_integration.py; then
        echo -e "${GREEN}✓ API集成测试通过${NC}"
        return 0
    else
        echo -e "${RED}✗ API集成测试失败${NC}"
        return 1
    fi
}

# 执行认证流程测试
run_auth_tests() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}执行认证流程测试${NC}"
    echo -e "${BLUE}========================================${NC}"

    cd "$TESTS_DIR/scripts"

    if python test_auth_flow.py; then
        echo -e "${GREEN}✓ 认证流程测试通过${NC}"
        return 0
    else
        echo -e "${RED}✗ 认证流程测试失败${NC}"
        return 1
    fi
}

# 执行内容生成测试
run_content_tests() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}执行内容生成测试${NC}"
    echo -e "${BLUE}========================================${NC}"

    cd "$TESTS_DIR/scripts"

    if [ -f "test_content_generation.py" ]; then
        if python test_content_generation.py; then
            echo -e "${GREEN}✓ 内容生成测试通过${NC}"
            return 0
        else
            echo -e "${RED}✗ 内容生成测试失败${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ 内容生成测试脚本不存在，跳过${NC}"
        return 0
    fi
}

# 生成测试报告
generate_report() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}生成测试报告${NC}"
    echo -e "${BLUE}========================================${NC}"

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    REPORT_FILE="$REPORTS_DIR/integration_test_report_${TIMESTAMP}.txt"

    {
        echo "======================================"
        echo "集成测试报告"
        echo "======================================"
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "测试环境:"
        echo "  - 后端: http://localhost:8000"
        echo "  - 前端: http://localhost:5173"
        echo ""
        echo "测试结果:"
        echo "  - API集成测试: $API_TEST_RESULT"
        echo "  - 认证流程测试: $AUTH_TEST_RESULT"
        echo "  - 内容生成测试: $CONTENT_TEST_RESULT"
        echo ""
        echo "详细结果请查看:"
        echo "  $REPORTS_DIR"
        echo "======================================"
    } > "$REPORT_FILE"

    echo -e "${GREEN}✓ 测试报告已生成: $REPORT_FILE${NC}"
    cat "$REPORT_FILE"
}

# 主函数
main() {
    # 检查环境
    if ! check_backend; then
        exit 1
    fi

    check_frontend

    if ! check_python_deps; then
        exit 1
    fi

    # 执行测试
    API_TEST_RESULT="未执行"
    AUTH_TEST_RESULT="未执行"
    CONTENT_TEST_RESULT="未执行"

    FAILED=0

    if run_api_tests; then
        API_TEST_RESULT="通过"
    else
        API_TEST_RESULT="失败"
        FAILED=$((FAILED + 1))
    fi

    if run_auth_tests; then
        AUTH_TEST_RESULT="通过"
    else
        AUTH_TEST_RESULT="失败"
        FAILED=$((FAILED + 1))
    fi

    if run_content_tests; then
        CONTENT_TEST_RESULT="通过"
    else
        CONTENT_TEST_RESULT="失败"
        FAILED=$((FAILED + 1))
    fi

    # 生成报告
    generate_report

    # 总结
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}测试执行完成${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ 所有测试通过${NC}"
        exit 0
    else
        echo -e "${RED}✗ $FAILED 个测试失败${NC}"
        exit 1
    fi
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --help, -h     显示帮助信息"
            echo "  --api-only     仅执行API测试"
            echo "  --auth-only    仅执行认证测试"
            echo ""
            exit 0
            ;;
        --api-only)
            check_backend || exit 1
            check_python_deps || exit 1
            run_api_tests
            exit $?
            ;;
        --auth-only)
            check_backend || exit 1
            check_python_deps || exit 1
            run_auth_tests
            exit $?
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
    shift
done

# 执行主函数
main
