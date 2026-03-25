"""
权限控制中间件 - 已弃用

版本: 1.0
更新日期: 2026-03-25

NOTE: 所有权限检查函数已迁移至 app.api.deps 以保证集中管理和一致性。
此文件保留仅用于兼容性，所有导入应改为从 app.api.deps 导入。

推荐用法:
    from app.api.deps import (
        require_permission,
        require_admin,
        require_enterprise_admin,
        get_current_user,
        get_db
    )
"""

# 为了向后兼容，重新导出 deps.py 中的函数
from app.api.deps import (
    require_permission,
    require_admin,
    require_enterprise_admin,
)

__all__ = [
    "require_permission",
    "require_admin",
    "require_enterprise_admin",
]
