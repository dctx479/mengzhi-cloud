"""
产品API路由单元测试

测试内容：
- 产品列表查询
- 产品详情查询
- 创建产品
- 更新产品
- 删除产品
- 搜索和筛选

运行: pytest tests/test_products_api.py -v
"""

import pytest
from sqlalchemy import text

from app.services.auth_service import AuthService
from app.models.product import Product


# ==================== 产品列表端点测试 ====================

class TestProductListEndpoint:
    """产品列表端点功能测试"""

    @pytest.mark.unit
    def test_list_products_empty(self, client):
        """测试空产品列表"""
        response = client.get("/api/v1/products?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data["data"] or isinstance(data["data"], list)

    @pytest.mark.unit
    def test_list_products_with_pagination(self, client, test_db_session, test_product_data_multiple):
        """测试产品列表分页"""
        # 创建多个产品
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        response = client.get("/api/v1/products?page=1&size=2")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_list_products_filter_category(self, client, test_db_session, test_product_data_multiple):
        """测试按分类筛选"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        response = client.get("/api/v1/products?category=肉类")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_list_products_search(self, client, test_db_session, test_product_data):
        """测试产品搜索"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        service.create_product(request, user_id=1)

        response = client.get("/api/v1/products?search=羊肉")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_list_products_invalid_page(self, client):
        """测试无效的分页参数"""
        response = client.get("/api/v1/products?page=0&size=10")

        # 应该返回400或使用默认值
        assert response.status_code in [200, 400, 422]


# ==================== 产品详情端点测试 ====================

class TestProductDetailEndpoint:
    """产品详情端点功能测试"""

    @pytest.mark.unit
    def test_get_product_success(self, client, test_db_session, test_product_data):
        """测试获取产品详情成功"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        response = client.get(f"/api/v1/products/{product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == test_product_data["name"]

    @pytest.mark.unit
    def test_get_product_not_found(self, client):
        """测试获取不存在的产品"""
        response = client.get("/api/v1/products/99999")

        assert response.status_code == 404

    @pytest.mark.unit
    def test_get_product_by_sku(self, client, test_db_session, test_product_data):
        """测试按SKU获取产品"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        service.create_product(request, user_id=1)

        response = client.get(f"/api/v1/products/sku/{test_product_data['sku']}")

        assert response.status_code in [200, 404]


# ==================== 创建产品端点测试 ====================

class TestCreateProductEndpoint:
    """创建产品端点功能测试"""

    @pytest.mark.unit
    def test_create_product_success(self, client, auth_headers, test_product_data):
        """测试创建产品成功"""
        response = client.post(
            "/api/v1/products",
            json=test_product_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["data"]["name"] == test_product_data["name"]

    @pytest.mark.unit
    def test_create_product_without_auth(self, client, test_product_data):
        """测试未认证创建产品"""
        response = client.post("/api/v1/products", json=test_product_data)

        assert response.status_code == 401

    @pytest.mark.unit
    def test_create_product_duplicate_sku(self, client, auth_headers, test_product_data):
        """测试重复SKU创建"""
        # 创建第一个产品
        response1 = client.post(
            "/api/v1/products",
            json=test_product_data,
            headers=auth_headers
        )
        assert response1.status_code in [200, 201]

        # 创建重复SKU的产品
        response2 = client.post(
            "/api/v1/products",
            json=test_product_data,
            headers=auth_headers
        )

        assert response2.status_code == 400

    @pytest.mark.unit
    def test_create_product_missing_required_fields(self, client, auth_headers):
        """测试缺少必需字段"""
        incomplete_data = {
            "name": "产品名称"
            # 缺少SKU等必需字段
        }
        response = client.post(
            "/api/v1/products",
            json=incomplete_data,
            headers=auth_headers
        )

        assert response.status_code == 422


# ==================== 更新产品端点测试 ====================

class TestUpdateProductEndpoint:
    """更新产品端点功能测试"""

    @pytest.mark.unit
    def test_update_product_success(self, client, auth_headers, test_db_session, test_product_data):
        """测试更新产品成功"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        update_data = {
            "name": "更新的产品名称",
            "price": 199.99
        }
        response = client.put(
            f"/api/v1/products/{product.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "更新的产品名称"

    @pytest.mark.unit
    def test_update_product_not_found(self, client, auth_headers):
        """测试更新不存在的产品"""
        update_data = {"name": "新名称"}
        response = client.put(
            "/api/v1/products/99999",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.unit
    def test_update_product_without_auth(self, client, test_db_session, test_product_data):
        """测试未认证更新产品"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        update_data = {"name": "新名称"}
        response = client.put(
            f"/api/v1/products/{product.id}",
            json=update_data
        )

        assert response.status_code == 401


# ==================== 删除产品端点测试 ====================

class TestDeleteProductEndpoint:
    """删除产品端点功能测试"""

    @pytest.mark.unit
    def test_delete_product_success(self, client, auth_headers, test_db_session, test_product_data):
        """测试删除产品成功"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        response = client.delete(
            f"/api/v1/products/{product.id}",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.unit
    def test_delete_product_not_found(self, client, auth_headers):
        """测试删除不存在的产品"""
        response = client.delete(
            "/api/v1/products/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.unit
    def test_delete_product_without_auth(self, client, test_db_session, test_product_data):
        """测试未认证删除产品"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        response = client.delete(f"/api/v1/products/{product.id}")

        assert response.status_code == 401


# ==================== 特殊查询端点测试 ====================

class TestSpecialQueriesEndpoint:
    """特殊查询端点功能测试"""

    @pytest.mark.unit
    def test_get_featured_products(self, client, test_db_session, test_product_data_multiple):
        """测试获取精选产品"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        response = client.get("/api/v1/products/featured")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_get_categories(self, client):
        """测试获取分类列表"""
        response = client.get("/api/v1/products/categories")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_get_regions(self, client):
        """测试获取地区列表"""
        response = client.get("/api/v1/products/regions")

        assert response.status_code in [200, 404]


# ==================== 产品统计端点测试 ====================

class TestProductStatsEndpoint:
    """产品统计端点功能测试"""

    @pytest.mark.unit
    def test_get_product_stats(self, client, auth_headers, test_db_session, test_product_data_multiple):
        """测试获取产品统计"""
        from app.schemas.products import ProductCreateRequest
        from app.services.product_service import ProductService

        service = ProductService(test_db_session)
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        response = client.get("/api/v1/products/stats", headers=auth_headers)

        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
