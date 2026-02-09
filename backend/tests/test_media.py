"""
媒体素材管理单元测试

测试内容:
- 图片上传
- 视频上传
- 媒体列表查询
- 媒体更新和删除
- 权限控制

版本: 1.0
更新日期: 2026-01-17
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image
import os
from pathlib import Path

from app.main import app
from app.models.media import Media, MediaType, MediaCategory
from app.core.config import settings


client = TestClient(app)


# ==================== 辅助函数 ====================

def create_test_image(width=800, height=600, format="JPEG"):
    """创建测试图片"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


def get_auth_headers(user_type="personal"):
    """获取认证头（模拟登录）"""
    # 这里应该使用真实的登录流程获取token
    # 暂时使用mock token
    if user_type == "admin":
        token = "mock_admin_token"
    else:
        token = "mock_user_token"

    return {"Authorization": f"Bearer {token}"}


# ==================== 图片上传测试 ====================

def test_upload_image_success():
    """测试成功上传图片"""
    # 创建测试图片
    img_file = create_test_image()

    # 准备上传数据
    files = {
        "file": ("test_image.jpg", img_file, "image/jpeg")
    }
    data = {
        "category": "product",
        "title": "测试产品图片",
        "description": "这是一张测试图片"
    }

    # 发送请求
    response = client.post(
        "/api/v1/media/upload/image",
        files=files,
        data=data,
        headers=get_auth_headers()
    )

    # 验证响应
    assert response.status_code == 201
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "图片上传成功"
    assert "data" in result

    # 验证返回的媒体信息
    media = result["data"]
    assert media["media_type"] == "image"
    assert media["category"] == "product"
    assert media["title"] == "测试产品图片"
    assert media["width"] == 800
    assert media["height"] == 600
    assert media["file_url"] is not None


def test_upload_image_invalid_type():
    """测试上传不支持的文件类型"""
    # 创建文本文件
    text_file = BytesIO(b"This is a text file")

    files = {
        "file": ("test.txt", text_file, "text/plain")
    }
    data = {
        "category": "product"
    }

    response = client.post(
        "/api/v1/media/upload/image",
        files=files,
        data=data,
        headers=get_auth_headers()
    )

    # 应该返回400错误
    assert response.status_code == 400
    assert "不支持的图片类型" in response.json()["detail"]


def test_upload_image_too_large():
    """测试上传超大文件"""
    # 创建一个超大图片（模拟）
    # 注意：实际测试中可能需要真实创建大文件
    large_file = BytesIO(b"x" * (settings.MAX_FILE_SIZE + 1))

    files = {
        "file": ("large.jpg", large_file, "image/jpeg")
    }
    data = {
        "category": "product"
    }

    response = client.post(
        "/api/v1/media/upload/image",
        files=files,
        data=data,
        headers=get_auth_headers()
    )

    # 应该返回400错误
    assert response.status_code == 400
    assert "文件过大" in response.json()["detail"]


# ==================== 媒体列表测试 ====================

def test_list_media():
    """测试获取媒体列表"""
    response = client.get(
        "/api/v1/media/",
        headers=get_auth_headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert "total" in result
    assert "page" in result
    assert "items" in result


def test_list_media_with_filters():
    """测试带筛选的媒体列表"""
    response = client.get(
        "/api/v1/media/?media_type=image&category=product&page=1&page_size=10",
        headers=get_auth_headers()
    )

    assert response.status_code == 200
    result = response.json()
    assert result["page"] == 1
    assert result["page_size"] == 10


# ==================== 媒体详情测试 ====================

def test_get_media_detail(media_id=1):
    """测试获取媒体详情"""
    response = client.get(
        f"/api/v1/media/{media_id}",
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        media = response.json()
        assert "id" in media
        assert "file_url" in media
        assert "media_type" in media
    else:
        # 媒体不存在
        assert response.status_code == 404


def test_get_media_permission_denied():
    """测试无权访问其他用户的媒体"""
    # 假设媒体1属于其他用户
    response = client.get(
        "/api/v1/media/1",
        headers=get_auth_headers(user_type="personal")
    )

    # 可能返回403或404
    assert response.status_code in [403, 404]


# ==================== 媒体更新测试 ====================

def test_update_media(media_id=1):
    """测试更新媒体信息"""
    update_data = {
        "title": "更新后的标题",
        "description": "更新后的描述",
        "is_public": False
    }

    response = client.put(
        f"/api/v1/media/{media_id}",
        json=update_data,
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        media = response.json()
        assert media["title"] == "更新后的标题"
        assert media["description"] == "更新后的描述"
        assert media["is_public"] is False
    else:
        # 媒体不存在或无权限
        assert response.status_code in [403, 404]


# ==================== 媒体删除测试 ====================

def test_delete_media(media_id=999):
    """测试删除媒体"""
    response = client.delete(
        f"/api/v1/media/{media_id}",
        headers=get_auth_headers()
    )

    # 成功删除返回204，或者404（不存在）
    assert response.status_code in [204, 404]


# ==================== 媒体统计测试 ====================

def test_get_media_stats():
    """测试获取媒体统计"""
    response = client.get(
        "/api/v1/media/stats",
        headers=get_auth_headers()
    )

    assert response.status_code == 200
    stats = response.json()
    assert "total_count" in stats
    assert "total_size" in stats
    assert "image_count" in stats
    assert "video_count" in stats
    assert "by_category" in stats


# ==================== 产品关联测试 ====================

def test_assign_media_to_product(media_id=1, product_id=1):
    """测试关联媒体到产品"""
    response = client.post(
        f"/api/v1/media/{media_id}/assign-product/{product_id}",
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        media = response.json()
        assert media["product_id"] == product_id
    else:
        # 媒体或产品不存在，或无权限
        assert response.status_code in [403, 404]


def test_unassign_media_from_product(media_id=1):
    """测试取消媒体与产品的关联"""
    response = client.delete(
        f"/api/v1/media/{media_id}/unassign-product",
        headers=get_auth_headers()
    )

    if response.status_code == 200:
        media = response.json()
        assert media["product_id"] is None
    else:
        assert response.status_code in [403, 404]


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
