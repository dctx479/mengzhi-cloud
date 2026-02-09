# Makefile - 后端测试命令集
# 使用: make test, make coverage, etc.

.PHONY: help install test test-verbose test-auth test-product test-chat test-models coverage coverage-html clean lint format

help:
	@echo "后端单元测试命令集"
	@echo "=================="
	@echo ""
	@echo "主要命令:"
	@echo "  make install         - 安装测试依赖"
	@echo "  make test            - 运行所有测试"
	@echo "  make test-verbose    - 运行所有测试（详细输出）"
	@echo "  make test-auth       - 运行认证相关测试"
	@echo "  make test-product    - 运行产品相关测试"
	@echo "  make test-chat       - 运行对话相关测试"
	@echo "  make test-models     - 运行模型相关测试"
	@echo "  make coverage        - 生成覆盖率报告"
	@echo "  make coverage-html   - 生成HTML覆盖率报告"
	@echo "  make clean           - 清理测试生成的文件"
	@echo "  make lint            - 代码检查"
	@echo "  make format          - 代码格式化"
	@echo ""

install:
	@echo "安装测试依赖..."
	pip install -r requirements-test.txt

test:
	@echo "运行所有测试..."
	pytest tests/ -v --tb=short

test-verbose:
	@echo "运行所有测试（详细输出）..."
	pytest tests/ -vv -s --tb=long

test-auth:
	@echo "运行认证相关测试..."
	pytest tests/test_auth*.py -v --tb=short

test-product:
	@echo "运行产品相关测试..."
	pytest tests/test_product*.py -v --tb=short

test-chat:
	@echo "运行对话相关测试..."
	pytest tests/test_chat*.py -v --tb=short

test-models:
	@echo "运行模型相关测试..."
	pytest tests/test_models.py -v --tb=short

test-fast:
	@echo "运行快速测试（跳过慢速测试）..."
	pytest tests/ -v -m "not slow" --tb=short

coverage:
	@echo "生成覆盖率报告..."
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml

coverage-html:
	@echo "生成HTML覆盖率报告..."
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "覆盖率报告已生成: coverage_html/index.html"

clean:
	@echo "清理测试生成的文件..."
	rm -rf .pytest_cache __pycache__ .coverage coverage_html coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	@echo "运行代码检查..."
	flake8 app/ tests/ --max-line-length=100

format:
	@echo "格式化代码..."
	black app/ tests/
	isort app/ tests/

# 默认目标
.DEFAULT_GOAL := help
