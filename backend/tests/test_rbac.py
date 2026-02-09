"""
RBAC权限系统测试

测试角色、权限管理和用户权限验证

版本: 1.0
更新日期: 2026-01-17
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import User, Role, Permission, UserType, UserStatus, UserRole
from app.services.permission_service import PermissionService
from app.core.errors import BusinessException, ErrorCode


class TestPermissionService:
    """权限服务测试"""

    def test_create_role(self, db: Session):
        """测试创建角色"""
        service = PermissionService(db)

        role = service.create_role(
            name="测试角色",
            code="TEST_ROLE",
            description="这是一个测试角色"
        )

        assert role.id is not None
        assert role.name == "测试角色"
        assert role.code == "TEST_ROLE"
        assert role.is_system is False

    def test_create_duplicate_role(self, db: Session):
        """测试创建重复角色"""
        service = PermissionService(db)

        # 创建第一个角色
        service.create_role(
            name="重复角色",
            code="DUPLICATE_ROLE"
        )

        # 尝试创建重复的角色代码
        with pytest.raises(BusinessException) as exc_info:
            service.create_role(
                name="另一个名字",
                code="DUPLICATE_ROLE"
            )

        assert exc_info.value.code == ErrorCode.RESOURCE_ALREADY_EXISTS

    def test_create_permission(self, db: Session):
        """测试创建权限"""
        service = PermissionService(db)

        permission = service.create_permission(
            resource="test_resource",
            action="create",
            name="创建测试资源"
        )

        assert permission.id is not None
        assert permission.resource == "test_resource"
        assert permission.action == "create"
        assert permission.name == "创建测试资源"

    def test_assign_permissions_to_role(self, db: Session):
        """测试为角色分配权限"""
        service = PermissionService(db)

        # 创建角色
        role = service.create_role(
            name="权限测试角色",
            code="PERM_TEST_ROLE"
        )

        # 创建权限
        perm1 = service.create_permission(
            resource="test", action="read", name="读取测试"
        )
        perm2 = service.create_permission(
            resource="test", action="create", name="创建测试"
        )

        # 分配权限
        updated_role = service.assign_permissions_to_role(
            role_id=role.id,
            permission_ids=[perm1.id, perm2.id]
        )

        assert len(updated_role.permissions) == 2
        assert updated_role.has_permission("test", "read")
        assert updated_role.has_permission("test", "create")

    def test_assign_roles_to_user(self, db: Session):
        """测试为用户分配角色"""
        service = PermissionService(db)

        # 创建用户
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            user_type=UserType.PERSONAL,
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 创建角色
        role = service.create_role(
            name="用户测试角色",
            code="USER_TEST_ROLE"
        )

        # 分配角色
        updated_user = service.assign_roles_to_user(
            user_id=user.id,
            role_ids=[role.id]
        )

        assert len(updated_user.roles) == 1
        assert updated_user.roles[0].code == "USER_TEST_ROLE"

    def test_user_has_permission(self, db: Session):
        """测试用户权限检查"""
        service = PermissionService(db)

        # 创建用户
        user = User(
            username="perm_test_user",
            email="permtest@example.com",
            password_hash="hashed_password",
            user_type=UserType.PERSONAL,
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 创建权限
        perm = service.create_permission(
            resource="product", action="read", name="查看产品"
        )

        # 创建角色并分配权限
        role = service.create_role(
            name="读者角色",
            code="READER_ROLE",
            permission_ids=[perm.id]
        )

        # 为用户分配角色
        service.assign_roles_to_user(
            user_id=user.id,
            role_ids=[role.id]
        )

        # 刷新用户以加载关系
        db.refresh(user)

        # 验证权限
        assert user.has_permission("product", "read") is True
        assert user.has_permission("product", "create") is False

    def test_get_user_permissions(self, db: Session):
        """测试获取用户所有权限"""
        service = PermissionService(db)

        # 创建用户
        user = User(
            username="multi_perm_user",
            email="multiperm@example.com",
            password_hash="hashed_password",
            user_type=UserType.PERSONAL,
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 创建多个权限
        perm1 = service.create_permission(
            resource="article", action="read", name="查看文章"
        )
        perm2 = service.create_permission(
            resource="article", action="create", name="创建文章"
        )
        perm3 = service.create_permission(
            resource="comment", action="read", name="查看评论"
        )

        # 创建两个角色
        role1 = service.create_role(
            name="作者角色",
            code="AUTHOR_ROLE",
            permission_ids=[perm1.id, perm2.id]
        )
        role2 = service.create_role(
            name="评论员角色",
            code="COMMENTER_ROLE",
            permission_ids=[perm3.id]
        )

        # 为用户分配两个角色
        service.assign_roles_to_user(
            user_id=user.id,
            role_ids=[role1.id, role2.id]
        )

        # 获取所有权限
        permissions = service.get_user_permissions(user.id)

        assert len(permissions) == 3
        permission_codes = [f"{p.resource}:{p.action}" for p in permissions]
        assert "article:read" in permission_codes
        assert "article:create" in permission_codes
        assert "comment:read" in permission_codes

    def test_delete_system_role(self, db: Session):
        """测试删除系统角色（应该失败）"""
        service = PermissionService(db)

        # 创建系统角色
        role = service.create_role(
            name="系统角色",
            code="SYSTEM_ROLE",
            is_system=True
        )

        # 尝试删除系统角色
        with pytest.raises(BusinessException) as exc_info:
            service.delete_role(role.id)

        assert exc_info.value.code == ErrorCode.OPERATION_FORBIDDEN

    def test_delete_role_with_users(self, db: Session):
        """测试删除有用户使用的角色（应该失败）"""
        service = PermissionService(db)

        # 创建用户
        user = User(
            username="role_delete_test",
            email="roledelete@example.com",
            password_hash="hashed_password",
            user_type=UserType.PERSONAL,
            status=UserStatus.ACTIVE,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()

        # 创建角色并分配给用户
        role = service.create_role(
            name="待删除角色",
            code="TO_DELETE_ROLE"
        )
        service.assign_roles_to_user(
            user_id=user.id,
            role_ids=[role.id]
        )

        # 尝试删除角色
        with pytest.raises(BusinessException) as exc_info:
            service.delete_role(role.id)

        assert exc_info.value.code == ErrorCode.OPERATION_FORBIDDEN

    def test_initialize_default_roles(self, db: Session):
        """测试初始化默认角色"""
        PermissionService.initialize_default_roles(db)

        # 检查系统角色是否创建
        admin_role = db.query(Role).filter(Role.code == "ADMIN").first()
        enterprise_role = db.query(Role).filter(Role.code == "ENTERPRISE").first()
        personal_role = db.query(Role).filter(Role.code == "PERSONAL").first()

        assert admin_role is not None
        assert admin_role.is_system is True
        assert len(admin_role.permissions) > 0

        assert enterprise_role is not None
        assert enterprise_role.is_system is True

        assert personal_role is not None
        assert personal_role.is_system is True

    def test_list_roles(self, db: Session):
        """测试角色列表查询"""
        service = PermissionService(db)

        # 创建多个角色
        service.create_role(name="角色A", code="ROLE_A")
        service.create_role(name="角色B", code="ROLE_B", is_system=True)
        service.create_role(name="角色C", code="ROLE_C")

        # 查询所有角色
        roles, total = service.list_roles(page=1, page_size=10)
        assert total == 3

        # 查询系统角色
        system_roles, total = service.list_roles(is_system=True)
        assert total == 1

        # 关键词搜索
        roles, total = service.list_roles(keyword="角色A")
        assert total == 1

    def test_list_permissions(self, db: Session):
        """测试权限列表查询"""
        service = PermissionService(db)

        # 创建多个权限
        service.create_permission("blog", "read", "读取博客")
        service.create_permission("blog", "create", "创建博客")
        service.create_permission("user", "read", "读取用户")

        # 查询所有权限
        permissions, total = service.list_permissions(page=1, page_size=10)
        assert total == 3

        # 按资源筛选
        permissions, total = service.list_permissions(resource="blog")
        assert total == 2

        # 按操作筛选
        permissions, total = service.list_permissions(action="read")
        assert total == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
