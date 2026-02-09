"""
产品服务单元测试

测试内容：
- 产品CRUD操作
- 搜索和筛选
- 分页功能
- SKU唯一性验证
- 统计信息

运行: pytest tests/test_product_service.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.product_service import ProductService
from app.models.product import Product, ProductStatus
from app.core.errors import BusinessException, ErrorCode


# ==================== 产品创建测试 ====================

class TestProductCreation:
    """产品创建功能测试"""

    @pytest.mark.unit
    def test_create_product_success(self, test_db_session, test_product_data):
        """测试成功创建产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        assert product is not None
        assert product.name == test_product_data["name"]
        assert product.sku == test_product_data["sku"]
        assert product.price == test_product_data["price"]

    @pytest.mark.unit
    def test_create_product_duplicate_sku(self, test_db_session, test_product_data):
        """测试SKU重复创建失败"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        request = ProductCreateRequest(**test_product_data)

        # 创建第一个产品
        service.create_product(request, user_id=1)

        # 尝试创建重复SKU的产品
        with pytest.raises(BusinessException) as exc_info:
            service.create_product(request, user_id=1)

        assert exc_info.value.code == ErrorCode.RECORD_ALREADY_EXISTS

    @pytest.mark.unit
    def test_create_product_missing_fields(self, test_db_session):
        """测试缺少必需字段"""
        service = ProductService(test_db_session)

        incomplete_data = {
            "name": "产品名称",
            # 缺少SKU等必需字段
        }

        from app.schemas.products import ProductCreateRequest

        # 应该验证失败
        with pytest.raises(Exception):  # Pydantic ValidationError
            request = ProductCreateRequest(**incomplete_data)

    @pytest.mark.unit
    def test_create_product_with_all_fields(self, test_db_session, test_product_data):
        """测试创建包含所有字段的产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        # 验证所有字段都被设置
        assert product.cultural_tags == test_product_data["cultural_tags"]
        assert product.is_featured == test_product_data["is_featured"]
        assert product.origin_story == test_product_data["origin_story"]


# ==================== 产品查询测试 ====================

class TestProductRetrieval:
    """产品查询功能测试"""

    @pytest.mark.unit
    def test_get_product_by_id_success(self, test_db_session, test_product_data):
        """测试按ID获取产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        request = ProductCreateRequest(**test_product_data)
        created_product = service.create_product(request, user_id=1)

        # 获取产品
        retrieved_product = service.get_product_by_id(created_product.id)

        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.name == test_product_data["name"]

    @pytest.mark.unit
    def test_get_product_by_id_not_found(self, test_db_session):
        """测试获取不存在的产品"""
        service = ProductService(test_db_session)

        with pytest.raises(BusinessException) as exc_info:
            service.get_product_by_id(99999)

        assert exc_info.value.code == ErrorCode.RECORD_NOT_FOUND

    @pytest.mark.unit
    def test_get_product_by_sku_success(self, test_db_session, test_product_data):
        """测试按SKU获取产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        request = ProductCreateRequest(**test_product_data)
        service.create_product(request, user_id=1)

        # 按SKU获取
        product = service.get_product_by_sku(test_product_data["sku"])

        assert product is not None
        assert product.sku == test_product_data["sku"]

    @pytest.mark.unit
    def test_get_product_by_sku_not_found(self, test_db_session):
        """测试按SKU获取不存在的产品"""
        service = ProductService(test_db_session)

        product = service.get_product_by_sku("NONEXISTENT")

        assert product is None


# ==================== 产品列表测试 ====================

class TestProductListing:
    """产品列表和筛选功能测试"""

    @pytest.mark.unit
    def test_list_products_basic(self, test_db_session, test_product_data_multiple):
        """测试基本的产品列表查询"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 列出产品
        products, total = service.list_products(page=1, size=10)

        assert len(products) == 5
        assert total == 5

    @pytest.mark.unit
    def test_list_products_pagination(self, test_db_session, test_product_data_multiple):
        """测试产品列表分页"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 第一页
        products_page1, total = service.list_products(page=1, size=2)
        assert len(products_page1) == 2
        assert total == 5

        # 第二页
        products_page2, total = service.list_products(page=2, size=2)
        assert len(products_page2) == 2

        # 第三页
        products_page3, total = service.list_products(page=3, size=2)
        assert len(products_page3) == 1

    @pytest.mark.unit
    def test_list_products_search(self, test_db_session, test_product_data):
        """测试产品搜索功能"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建产品
        request = ProductCreateRequest(**test_product_data)
        service.create_product(request, user_id=1)

        # 按名称搜索
        products, total = service.list_products(search="羊肉", page=1, size=10)
        assert total >= 1

        # 按SKU搜索
        products, total = service.list_products(search="PROD-001", page=1, size=10)
        assert total >= 1

    @pytest.mark.unit
    def test_list_products_filter_category(self, test_db_session, test_product_data_multiple):
        """测试按分类筛选"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 筛选肉类产品
        products, total = service.list_products(category="肉类", page=1, size=10)
        assert len(products) > 0
        for product in products:
            assert product.category == "肉类"

    @pytest.mark.unit
    def test_list_products_filter_featured(self, test_db_session, test_product_data_multiple):
        """测试筛选精选产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 筛选精选产品
        products, total = service.list_products(is_featured=True, page=1, size=10)
        assert len(products) > 0
        for product in products:
            assert product.is_featured is True

    @pytest.mark.unit
    def test_list_products_sorting(self, test_db_session, test_product_data_multiple):
        """测试产品排序"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 按创建时间降序
        products_desc, _ = service.list_products(
            sort_by="created_at",
            sort_order="desc",
            page=1,
            size=10
        )

        # 按创建时间升序
        products_asc, _ = service.list_products(
            sort_by="created_at",
            sort_order="asc",
            page=1,
            size=10
        )

        # 验证顺序不同
        assert products_desc[0].id != products_asc[0].id


# ==================== 产品更新测试 ====================

class TestProductUpdate:
    """产品更新功能测试"""

    @pytest.mark.unit
    def test_update_product_success(self, test_db_session, test_product_data):
        """测试成功更新产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest, ProductUpdateRequest

        # 创建产品
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        # 更新产品
        update_data = {
            "name": "更新的产品名称",
            "price": 199.99
        }
        update_request = ProductUpdateRequest(**update_data)
        updated_product = service.update_product(product.id, update_request, user_id=1)

        assert updated_product.name == "更新的产品名称"
        assert updated_product.price == 199.99
        # SKU不应改变
        assert updated_product.sku == test_product_data["sku"]

    @pytest.mark.unit
    def test_update_product_not_found(self, test_db_session):
        """测试更新不存在的产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductUpdateRequest

        update_request = ProductUpdateRequest(name="新名称")

        with pytest.raises(BusinessException):
            service.update_product(99999, update_request, user_id=1)

    @pytest.mark.unit
    def test_update_product_partial(self, test_db_session, test_product_data):
        """测试部分更新产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest, ProductUpdateRequest

        # 创建产品
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)
        original_stock = product.stock

        # 只更新价格
        update_data = {"price": 299.99}
        update_request = ProductUpdateRequest(**update_data)
        updated_product = service.update_product(product.id, update_request, user_id=1)

        assert updated_product.price == 299.99
        assert updated_product.stock == original_stock  # 库存不变


# ==================== 产品删除测试 ====================

class TestProductDeletion:
    """产品删除功能测试"""

    @pytest.mark.unit
    def test_delete_product_success(self, test_db_session, test_product_data):
        """测试成功删除产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建产品
        request = ProductCreateRequest(**test_product_data)
        product = service.create_product(request, user_id=1)

        # 删除产品
        result = service.delete_product(product.id)
        assert result is True

        # 验证产品已删除
        with pytest.raises(BusinessException):
            service.get_product_by_id(product.id)

    @pytest.mark.unit
    def test_delete_product_not_found(self, test_db_session):
        """测试删除不存在的产品"""
        service = ProductService(test_db_session)

        with pytest.raises(BusinessException):
            service.delete_product(99999)


# ==================== 特殊查询测试 ====================

class TestSpecialQueries:
    """特殊查询功能测试"""

    @pytest.mark.unit
    def test_get_featured_products(self, test_db_session, test_product_data_multiple):
        """测试获取精选产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取精选产品
        products = service.get_featured_products(limit=10)

        assert len(products) > 0
        for product in products:
            assert product.is_featured is True

    @pytest.mark.unit
    def test_get_products_by_category(self, test_db_session, test_product_data_multiple):
        """测试按分类获取产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取肉类产品
        products = service.get_products_by_category("肉类", limit=10)

        assert len(products) > 0
        for product in products:
            assert product.category == "肉类"

    @pytest.mark.unit
    def test_get_products_by_region(self, test_db_session, test_product_data_multiple):
        """测试按地区获取产品"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取内蒙古产品
        products = service.get_products_by_region("内蒙古", limit=10)

        assert len(products) > 0
        for product in products:
            assert product.region == "内蒙古"


# ==================== 统计功能测试 ====================

class TestProductStatistics:
    """产品统计功能测试"""

    @pytest.mark.unit
    def test_get_product_statistics(self, test_db_session, test_product_data_multiple):
        """测试获取产品统计"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取统计信息
        stats = service.get_product_statistics()

        assert stats["total"] == 5
        assert stats["active"] > 0
        assert stats["featured"] > 0
        assert "categories" in stats
        assert "regions" in stats

    @pytest.mark.unit
    def test_get_categories(self, test_db_session, test_product_data_multiple):
        """测试获取所有分类"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取分类
        categories = service.get_categories()

        assert len(categories) > 0
        assert "肉类" in categories or "乳制品" in categories

    @pytest.mark.unit
    def test_get_regions(self, test_db_session, test_product_data_multiple):
        """测试获取所有地区"""
        service = ProductService(test_db_session)

        from app.schemas.products import ProductCreateRequest

        # 创建多个产品
        for data in test_product_data_multiple:
            request = ProductCreateRequest(**data)
            service.create_product(request, user_id=1)

        # 获取地区
        regions = service.get_regions()

        assert len(regions) > 0
        assert "内蒙古" in regions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
