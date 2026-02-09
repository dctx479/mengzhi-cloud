"""
Pytest单元测试包

包含后端核心模块的完整单元测试
"""

__version__ = "1.0.0"
__author__ = "AI Platform Test Team"

# 导出测试模块
from . import conftest

__all__ = [
    "conftest",
]
