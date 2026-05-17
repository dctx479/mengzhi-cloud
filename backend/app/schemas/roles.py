"""
角色和权限相关的Pydantic Schema

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# ==================== Permission Schemas ====================

class PermissionBase(BaseModel):
    """权限基础Schema"""
    resource: str = Field(..., max_length=50, description="资源名称，如：product、user、chat")
    action: str = Field(..., max_length=20, description="操作名称，如：create、read、update、delete")
    name: str = Field(..., max_length=100, description="权限显示名称")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")

    @field_validator('resource')
    @classmethod
    def validate_resource(cls, v):
        """验证资源名称格式"""
        if not v.islower() or not v.replace('_', '').isalnum():
            raise ValueError('资源名称必须是小写字母和下划线组成')
        return v

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """验证操作名称"""
        valid_actions = {'create', 'read', 'update', 'delete', 'list', 'export', 'import', 'manage'}
        if v not in valid_actions:
            raise ValueError(f'操作名称必须是以下之一: {", ".join(valid_actions)}')
        return v


class PermissionCreate(PermissionBase):
    """创建权限Schema"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限Schema"""
    name: Optional[str] = Field(None, max_length=100, description="权限显示名称")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")


class PermissionResponse(PermissionBase):
    """权限响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="权限ID")
    created_at: datetime = Field(..., description="创建时间")


# ==================== Role Schemas ====================

class RoleBase(BaseModel):
    """角色基础Schema"""
    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    code: str = Field(..., min_length=2, max_length=50, description="角色代码")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证角色代码格式"""
        if not v.isupper() or not v.replace('_', '').isalnum():
            raise ValueError('角色代码必须是大写字母和下划线组成')
        return v


class RoleCreate(RoleBase):
    """创建角色Schema"""
    permission_ids: Optional[List[int]] = Field(default_factory=list, description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色Schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")


class RoleResponse(RoleBase):
    """角色响应Schema（不含权限详情）"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="角色ID")
    is_system: bool = Field(..., description="是否系统角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class RoleWithPermissions(RoleResponse):
    """角色响应Schema（含权限详情）"""
    permissions: List[PermissionResponse] = Field(default_factory=list, description="权限列表")


# ==================== User Role Assignment Schemas ====================

class UserRoleAssignment(BaseModel):
    """用户角色分配Schema"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")

    @field_validator('role_ids')
    @classmethod
    def validate_unique_roles(cls, v):
        """确保角色ID唯一"""
        if len(v) != len(set(v)):
            raise ValueError('角色ID列表中存在重复')
        return v


class RolePermissionAssignment(BaseModel):
    """角色权限分配Schema"""
    permission_ids: List[int] = Field(..., min_length=1, description="权限ID列表")

    @field_validator('permission_ids')
    @classmethod
    def validate_unique_permissions(cls, v):
        """确保权限ID唯一"""
        if len(v) != len(set(v)):
            raise ValueError('权限ID列表中存在重复')
        return v


# ==================== Query Schemas ====================

class RoleListQuery(BaseModel):
    """角色列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, max_length=50, description="搜索关键词（名称或代码）")
    is_system: Optional[bool] = Field(None, description="是否系统角色")


class PermissionListQuery(BaseModel):
    """权限列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    resource: Optional[str] = Field(None, max_length=50, description="资源筛选")
    action: Optional[str] = Field(None, max_length=20, description="操作筛选")


__all__ = [
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "UserRoleAssignment",
    "RolePermissionAssignment",
    "RoleListQuery",
    "PermissionListQuery",
]
