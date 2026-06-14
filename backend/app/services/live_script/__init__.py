"""
直播脚本生成器服务模块
"""

from .prompts_fusion import (
    get_live_script_prompt,
    get_live_script_examples,
    build_live_script_messages
)

__all__ = [
    "get_live_script_prompt",
    "get_live_script_examples",
    "build_live_script_messages"
]
