"""
产品服务层 - 优化版本

版本: 1.1
更新日期: 2026-01-17

改进：
- 添加缓存支持 (BUG-031)
- 优化N+1查询 (BUG-032)
- 添加完整的类型注解 (BUG-016)
"""

from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, text
from app.core.logging_config import logger
from app.core.cache_manager import cache
from app.core.constants import PRODUCT_CACHE_TTL, ALLOWED_SORT_FIELDS, ALLOWED_SORT_ORDERS

from app.models.product import Product
from app.models.user import User
from app.schemas.products import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductStatus
)
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError


class ProductService:
    """产品服务类

    提供产品相关的业务逻辑操作，包括：
    - CRUD操作
    - 列表查询和筛选
    - 搜索功能
    - 分页处理
    - 缓存管理
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    # ============ 创建 ============

    def create_product(self, request: ProductCreateRequest, user_id: int) -> Product:
        """创建产品

        Args:
            request: 产品创建请求
            user_id: 创建者ID

        Returns:
            创建的产品对象

        Raises:
            BusinessException: 产品名称已存在
        """
        # 检查产品名称是否已存在
        existing = self.db.query(Product).filter(Product.name == request.name).first()
        if existing:
            logger.warning(f"产品名称已存在: {request.name}")
            raise BusinessException(
                code=ErrorCode.RECORD_ALREADY_EXISTS,
                message=f"产品名称已存在: {request.name}"
            )

        try:
            # 创建产品对象（映射到实际模型字段）
            product = Product(
                name=request.name,
                short_name=request.short_name,
                category=request.category,
                sub_category=request.sub_category,
                description=request.description,
                origin_province=request.origin_province,
                origin_city=request.origin_city,
                origin_district=request.origin_district,
                origin_detail=request.origin_detail,
                cultural_tags=request.cultural_tags,
                cultural_story=request.cultural_story,
                historical_origin=request.historical_origin,
                certification_type=request.certification_type,
                certification_no=request.certification_no,
                status=request.status,
                created_by=user_id
            )

            # 保存到数据库
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)

            # 清除缓存
            cache.delete_pattern("products:*")

            logger.info(f"产品创建成功: {product.id} ({product.name})")
            return product

        except Exception as e:
            self.db.rollback()
            logger.error(f"产品创建失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_INSERT_FAILED,
                message="产品创建失败"
            )

    # ============ 读取 ============

    def get_product_by_id(self, product_id: int) -> Product:
        """根据ID获取产品

        Args:
            product_id: 产品ID

        Returns:
            产品对象

        Raises:
            BusinessException: 产品不存在
        """
        # 修复 N+1 查询：预加载 creator 关系
        product = self.db.query(Product).options(
            joinedload(Product.creator)
        ).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"产品不存在: {product_id}")
            raise RecordNotFoundError("产品")
        return product

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """根据名称获取产品

        Args:
            name: 产品名称

        Returns:
            产品对象或None
        """
        # 修复 N+1 查询：预加载 creator 关系
        return self.db.query(Product).options(
            joinedload(Product.creator)
        ).filter(Product.name == name).first()

    # ============ 列表和查询 ============

    def list_products(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        use_cache: bool = True
    ) -> Tuple[List[Product], int]:
        """列表查询产品 - 优化版本（包含缓存和N+1优化）

        Args:
            page: 页码（从1开始）
            size: 每页数量
            search: 搜索关键词（名称或SKU）
            category: 产品类别
            region: 产地区域
            status: 产品状态
            is_featured: 是否精选
            sort_by: 排序字段
            sort_order: 排序顺序
            use_cache: 是否使用缓存

        Returns:
            (产品列表, 总数)

        Raises:
            BusinessException: 查询失败
        """
        try:
            # 生成缓存键
            cache_key = f"products:{page}:{size}:{search}:{category}:{region}:{status}:{is_featured}:{sort_by}:{sort_order}"

            # 尝试从缓存获取（仅在无搜索条件时有效）
            if use_cache and not search:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"产品列表从缓存获取: page={page}, size={size}")
                    return cached_result['products'], cached_result['total']

            # 构建基础查询 (BUG-032修复: 使用joinedload预加载creator避免N+1查询)
            query = self.db.query(Product).options(
                joinedload(Product.creator)  # 预加载创建者信息
            )

            # 应用筛选条件
            filters: List[Any] = []

            # 搜索条件 (使用LIKE搜索产品名称和描述)
            if search:
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.cultural_story.ilike(search_term)
                    )
                )
                logger.debug(f"使用LIKE搜索: {search}")

            # 类别筛选
            if category:
                filters.append(Product.category == category)

            # 产地筛选（搜索省份或城市）
            if region:
                filters.append(
                    or_(
                        Product.origin_province.ilike(f"%{region}%"),
                        Product.origin_city.ilike(f"%{region}%")
                    )
                )

            # 状态筛选
            if status:
                # 将字符串状态转换为枚举
                from app.models.product import ProductStatus as ModelProductStatus
                try:
                    status_enum = ModelProductStatus(status)
                    filters.append(Product.status == status_enum)
                except ValueError:
                    logger.warning(f"无效的产品状态: {status}")

            # is_featured filter removed — column does not exist on Product model

            # 应用所有筛选条件
            if filters:
                query = query.filter(and_(*filters))

            # 获取总数（在排序前）
            total = query.count()

            # 验证排序参数（防止SQL注入）
            if sort_by not in ALLOWED_SORT_FIELDS:
                sort_by = "created_at"
            if sort_order.lower() not in ALLOWED_SORT_ORDERS:
                sort_order = "desc"

            # 应用排序
            sort_column = getattr(Product, sort_by, Product.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # 应用分页
            offset = (page - 1) * size
            products = query.offset(offset).limit(size).all()

            # 缓存结果（仅在无搜索条件时缓存，转为字典以便 JSON 序列化）
            if use_cache and not search:
                cache.set(
                    cache_key,
                    {'products': [p.to_dict() for p in products], 'total': total},
                    ttl_seconds=PRODUCT_CACHE_TTL
                )

            logger.info(f"产品列表查询成功: page={page}, size={size}, total={total}")
            return products, total

        except Exception as e:
            logger.error(f"产品列表查询失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_QUERY_FAILED,
                message="产品列表查询失败"
            )

    def get_featured_products(self, limit: int = 10) -> List[Product]:
        """获取精选产品（优化：添加缓存）

        Args:
            limit: 返回数量

        Returns:
            产品列表
        """
        cache_key = f"products:featured:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from app.models.product import ProductStatus as ModelProductStatus

            products = (
                self.db.query(Product)
                .options(joinedload(Product.creator))
                .filter(Product.status == ModelProductStatus.PUBLISHED)
                .order_by(desc(Product.created_at))
                .limit(limit)
                .all()
            )
            cache.set(cache_key, products, ttl_seconds=600)
            logger.info(f"获取精选产品: {len(products)}个")
            return products
        except Exception as e:
            logger.error(f"获取精选产品失败: {str(e)}")
            return []

    def get_products_by_category(self, category: str, limit: int = 10) -> List[Product]:
        """获取特定分类的产品（优化：添加缓存和预加载）

        Args:
            category: 产品类别
            limit: 返回数量

        Returns:
            产品列表
        """
        cache_key = f"products:category:{category}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from app.models.product import ProductStatus as ModelProductStatus

            products = (
                self.db.query(Product)
                .options(joinedload(Product.creator))
                .filter(
                    and_(
                        Product.category == category,
                        Product.status == ModelProductStatus.PUBLISHED
                    )
                )
                .order_by(desc(Product.created_at))
                .limit(limit)
                .all()
            )
            cache.set(cache_key, products, ttl_seconds=600)
            logger.info(f"获取分类产品: category={category}, count={len(products)}")
            return products
        except Exception as e:
            logger.error(f"获取分类产品失败: {str(e)}")
            return []

    def get_products_by_region(self, region: str, limit: int = 10) -> List[Product]:
        """获取特定地区的产品

        Args:
            region: 产地区域
            limit: 返回数量

        Returns:
            产品列表
        """
        try:
            from app.models.product import ProductStatus as ModelProductStatus

            # 修复 N+1 查询：预加载 creator 关系
            products = (
                self.db.query(Product)
                .options(joinedload(Product.creator))
                .filter(
                    and_(
                        or_(
                            Product.origin_province.ilike(f"%{region}%"),
                            Product.origin_city.ilike(f"%{region}%")
                        ),
                        Product.status == ModelProductStatus.PUBLISHED
                    )
                )
                .order_by(desc(Product.created_at))
                .limit(limit)
                .all()
            )
            logger.info(f"获取地区产品: region={region}, count={len(products)}")
            return products
        except Exception as e:
            logger.error(f"获取地区产品失败: {str(e)}")
            return []

    # ============ 更新 ============

    def update_product(
        self,
        product_id: int,
        request: ProductUpdateRequest,
        user_id: int
    ) -> Product:
        """更新产品

        Args:
            product_id: 产品ID
            request: 产品更新请求
            user_id: 更新者ID

        Returns:
            更新后的产品对象

        Raises:
            BusinessException: 产品不存在或更新失败
        """
        product = self.get_product_by_id(product_id)

        # 权限检查：只有创建者或管理员可以更新产品
        if product.created_by != user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            user_role = user.role.value if user and hasattr(user.role, 'value') else (str(user.role) if user else None)
            if user_role not in ('admin', 'super_admin'):
                logger.warning(f"用户{user_id}无权更新产品{product_id}（创建者={product.created_by}）")
                raise BusinessException(
                    code=ErrorCode.PERMISSION_DENIED,
                    message="无权更新此产品"
                )

        try:
            # 更新字段（仅更新提供的字段，映射到实际模型字段）
            update_data = request.dict(exclude_unset=True)

            # 字段映射
            field_mapping = {
                'cultural_description': 'cultural_story',
                'origin_story': 'historical_origin',
                'region': 'origin_province',
                'region_code': 'origin_city'
            }

            for field, value in update_data.items():
                if value is None:
                    continue

                # 映射字段名
                actual_field = field_mapping.get(field, field)

                if field == "status":
                    setattr(product, actual_field, value)
                elif hasattr(product, actual_field):
                    setattr(product, actual_field, value)

            # 重新将对象添加到会话（确保更改被跟踪）
            self.db.add(product)
            # 保存到数据库
            self.db.commit()
            self.db.refresh(product)

            # 清除缓存
            cache.delete_pattern("products:*")

            logger.info(f"产品更新成功: {product_id} ({product.name})")
            return product

        except Exception as e:
            self.db.rollback()
            logger.error(f"产品更新失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_UPDATE_FAILED,
                message="产品更新失败"
            )

    # ============ 删除 ============

    def delete_product(self, product_id: int) -> bool:
        """删除产品

        Args:
            product_id: 产品ID

        Returns:
            是否删除成功

        Raises:
            BusinessException: 产品不存在或删除失败
        """
        product = self.get_product_by_id(product_id)

        try:
            self.db.delete(product)
            self.db.commit()

            # 清除缓存
            cache.delete_pattern("products:*")

            logger.info(f"产品删除成功: {product_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"产品删除失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_DELETE_FAILED,
                message="产品删除失败"
            )

    # ============ 统计 ============

    def get_product_statistics(self) -> Dict[str, int]:
        """获取产品统计信息（优化：单次查询）

        Returns:
            统计数据字典
        """
        try:
            from app.models.product import ProductStatus as ModelProductStatus
            from sqlalchemy import func, case

            # 优化：使用单次聚合查询替代4次独立查询
            result = self.db.query(
                func.count(Product.id).label('total'),
                func.sum(case((Product.status == ModelProductStatus.PUBLISHED, 1), else_=0)).label('published'),
                func.count(func.distinct(Product.category)).label('categories'),
                func.count(func.distinct(Product.origin_province)).label('regions')
            ).first()

            return {
                "total": result.total or 0,
                "published": result.published or 0,
                "categories": result.categories or 0,
                "regions": result.regions or 0
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    def get_categories(self) -> List[str]:
        """获取所有产品类别（优化：添加缓存）

        Returns:
            类别列表
        """
        cache_key = "products:categories"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from app.models.product import ProductStatus as ModelProductStatus

            categories = (
                self.db.query(Product.category)
                .filter(Product.status == ModelProductStatus.PUBLISHED)
                .distinct()
                .order_by(Product.category)
                .all()
            )
            result = [cat[0] for cat in categories if cat[0]]
            cache.set(cache_key, result, ttl_seconds=1800)
            return result
        except Exception as e:
            logger.error(f"获取分类列表失败: {str(e)}")
            return []

    def get_regions(self) -> List[str]:
        """获取所有产地区域（优化：添加缓存）

        Returns:
            地区列表
        """
        cache_key = "products:regions"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from app.models.product import ProductStatus as ModelProductStatus

            regions = (
                self.db.query(Product.origin_province)
                .filter(Product.status == ModelProductStatus.PUBLISHED)
                .distinct()
                .order_by(Product.origin_province)
                .all()
            )
            result = [region[0] for region in regions if region[0]]
            cache.set(cache_key, result, ttl_seconds=1800)
            return result
        except Exception as e:
            logger.error(f"获取地区列表失败: {str(e)}")
            return []

    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """获取热门产品（按浏览次数排序）

        Args:
            limit: 返回数量

        Returns:
            产品列表
        """
        cache_key = f"products:popular:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from app.models.product import ProductStatus as ModelProductStatus

            products = (
                self.db.query(Product)
                .options(joinedload(Product.creator))
                .filter(Product.status == ModelProductStatus.PUBLISHED)
                .order_by(desc(Product.view_count), desc(Product.created_at))
                .limit(limit)
                .all()
            )
            cache.set(cache_key, [p.to_dict() for p in products], ttl_seconds=600)
            logger.info(f"获取热门产品: {len(products)}个")
            return products
        except Exception as e:
            logger.error(f"获取热门产品失败: {str(e)}")
            return []

