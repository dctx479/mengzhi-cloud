"""
品牌故事生成器服务模块
"""

from .prompts_fusion import (
    get_brand_story_prompt,
    get_brand_story_examples,
    build_brand_story_messages
)

__all__ = [
    "get_brand_story_prompt",
    "get_brand_story_examples",
    "build_brand_story_messages"
]
