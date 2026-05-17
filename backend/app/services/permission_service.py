"""
权限管理服务

提供RBAC系统的核心业务逻辑，包括：
- 角色CRUD操作
- 权限CRUD操作
- 用户-角色关联
- 角色-权限关联
- 默认角色和权限初始化

版本: 1.0
更新日期: 2026-01-17
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime
import logging

from app.models import (
    Role, Permission, User,
    role_permissions, user_roles
)
from app.core.errors import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class PermissionService:
    """权限管理服务"""

    def __init__(self, db: Session):
        """
        初始化权限服务

        参数:
            db: 数据库会话
        """
        self.db = db

    # ==================== 角色管理 ====================

    def create_role(
        self,
        name: str,
        code: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[int]] = None,
        is_system: bool = False
    ) -> Role:
        """
        创建角色

        参数:
            name: 角色名称
            code: 角色代码
            description: 角色描述
            permission_ids: 权限ID列表
            is_system: 是否系统角色

        返回:
            Role: 创建的角色对象

        异常:
            BusinessException: 角色代码或名称已存在
        """
        # 检查角色代码是否已存在
        existing = self.db.query(Role).filter(
            or_(Role.code == code, Role.name == name)
        ).first()
        if existing:
            if existing.code == code:
                raise BusinessException(ErrorCode.RESOURCE_ALREADY_EXISTS, "角色代码已存在")
            else:
                raise BusinessException(ErrorCode.RESOURCE_ALREADY_EXISTS, "角色名称已存在")

        # 创建角色
        role = Role(
            name=name,
            code=code,
            description=description,
            is_system=is_system
        )

        # 分配权限
        if permission_ids:
            permissions = self.db.query(Permission).filter(
                Permission.id.in_(permission_ids)
            ).all()
            role.permissions = permissions

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Created role: {code} (ID: {role.id})")
        return role

    def get_role(self, role_id: int) -> Optional[Role]:
        """
        获取角色详情（排除软删除记录）

        参数:
            role_id: 角色ID

        返回:
            Optional[Role]: 角色对象或None
        """
        return self.db.query(Role).filter(
            Role.id == role_id,
            Role.deleted_at.is_(None)
        ).first()

    def get_role_by_code(self, code: str) -> Optional[Role]:
        """
        根据代码获取角色

        参数:
            code: 角色代码

        返回:
            Optional[Role]: 角色对象或None
        """
        return self.db.query(Role).filter(
            Role.code == code,
            Role.deleted_at.is_(None)
        ).first()

    def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_system: Optional[bool] = None
    ) -> tuple[List[Role], int]:
        """
        获取角色列表

        参数:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            is_system: 是否系统角色

        返回:
            tuple[List[Role], int]: (角色列表, 总数)
        """
        query = self.db.query(Role).filter(Role.deleted_at.is_(None))

        # 关键词搜索
        if keyword:
            safe_keyword = keyword.replace("%", "\\%").replace("_", "\\_")
            query = query.filter(
                or_(
                    Role.name.like(f"%{safe_keyword}%"),
                    Role.code.like(f"%{safe_keyword}%")
                )
            )

        # 系统角色筛选
        if is_system is not None:
            query = query.filter(Role.is_system == is_system)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        roles = query.order_by(Role.created_at.desc()).offset(offset).limit(page_size).all()

        return roles, total

    def update_role(
        self,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Role:
        """
        更新角色

        参数:
            role_id: 角色ID
            name: 新名称
            description: 新描述

        返回:
            Role: 更新后的角色对象

        异常:
            BusinessException: 角色不存在或为系统角色
        """
        role = self.get_role(role_id)
        if not role:
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "角色不存在")

        # 系统角色不可修改名称和代码
        if role.is_system and name and name != role.name:
            raise BusinessException(ErrorCode.OPERATION_FORBIDDEN, "系统角色不可修改名称")

        if name:
            # 检查名称是否重复
            existing = self.db.query(Role).filter(
                and_(Role.name == name, Role.id != role_id)
            ).first()
            if existing:
                raise BusinessException(ErrorCode.RESOURCE_ALREADY_EXISTS, "角色名称已存在")
            role.name = name

        if description is not None:
            role.description = description

        role.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Updated role: {role.code} (ID: {role_id})")
        return role

    def delete_role(self, role_id: int) -> None:
        """
        删除角色

        参数:
            role_id: 角色ID

        异常:
            BusinessException: 角色不存在、为系统角色或仍有用户使用
        """
        role = self.get_role(role_id)
        if not role:
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "角色不存在")

        if role.is_system:
            raise BusinessException(ErrorCode.OPERATION_FORBIDDEN, "系统角色不可删除")

        # 检查是否有用户使用该角色
        user_count = self.db.query(user_roles).filter(
            user_roles.c.role_id == role_id
        ).count()
        if user_count > 0:
            raise BusinessException(
                ErrorCode.OPERATION_FORBIDDEN,
                f"该角色仍有 {user_count} 个用户使用，无法删除"
            )

        # 清理角色-权限关联，防止孤儿记录
        role.permissions = []
        self.db.flush()

        # 软删除
        role.deleted_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Deleted role: {role.code} (ID: {role_id})")

    # ==================== 权限管理 ====================

    def create_permission(
        self,
        resource: str,
        action: str,
        name: str,
        description: Optional[str] = None
    ) -> Permission:
        """
        创建权限

        参数:
            resource: 资源名称
            action: 操作名称
            name: 权限显示名称
            description: 权限描述

        返回:
            Permission: 创建的权限对象

        异常:
            BusinessException: 权限已存在
        """
        # 检查权限是否已存在
        existing = self.db.query(Permission).filter(
            and_(Permission.resource == resource, Permission.action == action)
        ).first()
        if existing:
            raise BusinessException(ErrorCode.RESOURCE_ALREADY_EXISTS, "权限已存在")

        # 创建权限
        permission = Permission(
            resource=resource,
            action=action,
            name=name,
            description=description
        )

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        logger.info(f"Created permission: {resource}:{action} (ID: {permission.id})")
        return permission

    def get_permission(self, permission_id: int) -> Optional[Permission]:
        """
        获取权限详情

        参数:
            permission_id: 权限ID

        返回:
            Optional[Permission]: 权限对象或None
        """
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def list_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        resource: Optional[str] = None,
        action: Optional[str] = None
    ) -> tuple[List[Permission], int]:
        """
        获取权限列表

        参数:
            page: 页码
            page_size: 每页数量
            resource: 资源筛选
            action: 操作筛选

        返回:
            tuple[List[Permission], int]: (权限列表, 总数)
        """
        query = self.db.query(Permission).filter(Permission.deleted_at.is_(None))

        if resource:
            query = query.filter(Permission.resource == resource)

        if action:
            query = query.filter(Permission.action == action)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        permissions = query.order_by(
            Permission.resource, Permission.action
        ).offset(offset).limit(page_size).all()

        return permissions, total

    # ==================== 角色-权限关联 ====================

    def assign_permissions_to_role(
        self,
        role_id: int,
        permission_ids: List[int]
    ) -> Role:
        """
        为角色分配权限（覆盖式）

        参数:
            role_id: 角色ID
            permission_ids: 权限ID列表

        返回:
            Role: 更新后的角色对象

        异常:
            BusinessException: 角色不存在或权限不存在
        """
        if not permission_ids:
            raise BusinessException(ErrorCode.INVALID_REQUEST, "权限列表不能为空")

        role = self.get_role(role_id)
        if not role:
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "角色不存在")
        # SECURITY FIX: 系统角色不可修改权限
        if role.is_system:
            raise BusinessException(ErrorCode.OPERATION_FORBIDDEN, "系统角色的权限不可修改")

        # 获取权限
        permissions = self.db.query(Permission).filter(
            Permission.id.in_(permission_ids)
        ).all()

        if len(permissions) != len(permission_ids):
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "部分权限不存在")

        # 覆盖式分配
        role.permissions = permissions
        role.updated_at = datetime.utcnow()
        self.db.flush()  # 确保关联表同步
        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Assigned {len(permissions)} permissions to role {role.code}")
        return role

    # ==================== 用户-角色关联 ====================

    def assign_roles_to_user(
        self,
        user_id: int,
        role_ids: List[int]
    ) -> User:
        """
        为用户分配角色（覆盖式）

        参数:
            user_id: 用户ID
            role_ids: 角色ID列表

        返回:
            User: 更新后的用户对象

        异常:
            BusinessException: 用户不存在或角色不存在
        """
        if not role_ids:
            raise BusinessException(ErrorCode.INVALID_REQUEST, "角色列表不能为空")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "用户不存在")

        # SECURITY: 超级管理员保护 - 防止剥夺 admin 用户的 ADMIN 角色
        user_role_str = user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else None
        if user_role_str == "admin":
            admin_rbac_role = self.db.query(Role).filter(Role.code == "ADMIN").first()
            if admin_rbac_role and admin_rbac_role.id not in role_ids:
                raise BusinessException(
                    ErrorCode.OPERATION_FORBIDDEN,
                    "不能移除超级管理员的 ADMIN 角色"
                )

        # 获取角色（排除软删除）
        roles = self.db.query(Role).filter(
            Role.id.in_(role_ids),
            Role.deleted_at.is_(None)
        ).all()

        if len(roles) != len(role_ids):
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "部分角色不存在")

        # 覆盖式分配
        user.roles = roles
        self.db.flush()  # 确保关联表同步
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Assigned {len(roles)} roles to user {user.username}")
        return user

    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        获取用户的所有权限

        参数:
            user_id: 用户ID

        返回:
            List[Permission]: 权限列表（去重）
        """
        # 使用 joinedload 一次性加载 roles 和 permissions，避免 N+1 查询
        user = self.db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions)
        ).filter(User.id == user_id).first()
        if not user:
            return []

        # 收集所有权限（去重）
        permissions_dict = {}
        for role in user.roles:
            for perm in role.permissions:
                perm_key = f"{perm.resource}:{perm.action}"
                if perm_key not in permissions_dict:
                    permissions_dict[perm_key] = perm

        return list(permissions_dict.values())

    def check_user_permission(
        self,
        user_id: int,
        resource: str,
        action: str
    ) -> bool:
        """
        检查用户是否有指定权限

        参数:
            user_id: 用户ID
            resource: 资源名称
            action: 操作名称

        返回:
            bool: 是否有权限
        """
        # 使用 joinedload 避免 N+1 查询
        user = self.db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions)
        ).filter(User.id == user_id).first()
        if not user:
            return False

        return user.has_permission(resource, action)

    # ==================== 默认数据初始化 ====================

    @staticmethod
    def initialize_default_roles(db: Session) -> None:
        """
        初始化默认角色和权限

        参数:
            db: 数据库会话
        """
        logger.info("Initializing default roles and permissions...")

        # 检查是否已初始化
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            logger.info("Roles already initialized, skipping...")
            return

        # 定义默认权限
        default_permissions = [
            # 产品权限
            {"resource": "product", "action": "create", "name": "创建产品"},
            {"resource": "product", "action": "read", "name": "查看产品"},
            {"resource": "product", "action": "update", "name": "更新产品"},
            {"resource": "product", "action": "delete", "name": "删除产品"},
            {"resource": "product", "action": "list", "name": "产品列表"},
            {"resource": "product", "action": "export", "name": "导出产品"},

            # 用户权限
            {"resource": "user", "action": "create", "name": "创建用户"},
            {"resource": "user", "action": "read", "name": "查看用户"},
            {"resource": "user", "action": "update", "name": "更新用户"},
            {"resource": "user", "action": "delete", "name": "删除用户"},
            {"resource": "user", "action": "list", "name": "用户列表"},
            {"resource": "user", "action": "manage", "name": "管理用户"},

            # 对话权限
            {"resource": "chat", "action": "create", "name": "创建对话"},
            {"resource": "chat", "action": "read", "name": "查看对话"},
            {"resource": "chat", "action": "delete", "name": "删除对话"},
            {"resource": "chat", "action": "list", "name": "对话列表"},

            # 企业权限
            {"resource": "enterprise", "action": "create", "name": "创建企业"},
            {"resource": "enterprise", "action": "read", "name": "查看企业"},
            {"resource": "enterprise", "action": "update", "name": "更新企业"},
            {"resource": "enterprise", "action": "delete", "name": "删除企业"},
            {"resource": "enterprise", "action": "manage", "name": "管理企业"},

            # 内容生成权限
            {"resource": "content", "action": "create", "name": "生成内容"},
            {"resource": "content", "action": "read", "name": "查看内容"},
            {"resource": "content", "action": "export", "name": "导出内容"},

            # 角色权限（系统管理）
            {"resource": "role", "action": "create", "name": "创建角色"},
            {"resource": "role", "action": "read", "name": "查看角色"},
            {"resource": "role", "action": "update", "name": "更新角色"},
            {"resource": "role", "action": "delete", "name": "删除角色"},
            {"resource": "role", "action": "manage", "name": "管理角色"},
        ]

        # 创建权限
        permissions = []
        for perm_data in default_permissions:
            perm = Permission(**perm_data)
            permissions.append(perm)
            db.add(perm)

        db.commit()  # 先提交权限以获取ID
        for perm in permissions:  # 刷新所有权限以确保ID已生成
            db.refresh(perm)

        # 创建系统角色
        # 1. 超级管理员 - 拥有所有权限
        admin_role = Role(
            name="超级管理员",
            code="ADMIN",
            description="拥有系统所有权限",
            is_system=True
        )
        admin_role.permissions = permissions
        db.add(admin_role)

        # 2. 企业用户 - 企业相关权限
        enterprise_permissions = [p for p in permissions if p.resource in [
            "product", "chat", "content", "enterprise"
        ]]
        enterprise_role = Role(
            name="企业用户",
            code="ENTERPRISE",
            description="企业用户权限，可管理产品和内容",
            is_system=True
        )
        enterprise_role.permissions = enterprise_permissions
        db.add(enterprise_role)

        # 3. 个人用户 - 基础权限
        personal_permissions = [p for p in permissions if (
            p.resource in ["product", "chat", "content"] and
            p.action in ["read", "list", "create"]
        )]
        personal_role = Role(
            name="个人用户",
            code="PERSONAL",
            description="个人用户权限，可查看产品和使用AI对话",
            is_system=True
        )
        personal_role.permissions = personal_permissions
        db.add(personal_role)

        db.commit()

        logger.info(f"Initialized {len(permissions)} permissions and 3 default roles")


__all__ = ["PermissionService"]
