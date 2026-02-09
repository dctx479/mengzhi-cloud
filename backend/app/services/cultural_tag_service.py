"""
文化标签服务层

提供文化标签的业务逻辑处理，包括：
- 标签CRUD操作
- 标签搜索和筛选
- 标签推荐算法
- 产品标签关联管理
- 标签统计分析

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

from app.models.cultural_tag import CulturalTag, product_tags
from app.models.product import Product
from app.schemas.cultural_tags import (
    CulturalTagCreate,
    CulturalTagUpdate,
    CulturalTagListQuery,
    CulturalTagRecommendQuery
)
from app.core.errors import BusinessException, ErrorCode
from app.core.constants import TAG_CATEGORIES


class CulturalTagService:
    """文化标签服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD操作 ====================

    def create_tag(self, tag_data: CulturalTagCreate) -> CulturalTag:
        """创建文化标签

        Args:
            tag_data: 标签创建数据

        Returns:
            创建的标签对象

        Raises:
            BusinessException: 标签名称已存在
        """
        # 检查标签名称是否已存在
        existing_tag = self.db.query(CulturalTag).filter(
            CulturalTag.name == tag_data.name
        ).first()

        if existing_tag:
            raise BusinessException(
                code=ErrorCode.RECORD_ALREADY_EXISTS,
                message=f"标签名称 '{tag_data.name}' 已存在"
            )

        # 如果指定了父标签，验证父标签存在
        if tag_data.parent_id:
            parent_tag = self.get_tag_by_id(tag_data.parent_id)
            if not parent_tag:
                raise BusinessException(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message=f"父标签ID {tag_data.parent_id} 不存在"
                )

        # 创建标签
        tag = CulturalTag(**tag_data.dict())
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)

        logger.info(f"创建文化标签成功: id={tag.id}, name={tag.name}")
        return tag

    def get_tag_by_id(self, tag_id: int) -> CulturalTag:
        """根据ID获取标签

        Args:
            tag_id: 标签ID

        Returns:
            标签对象

        Raises:
            BusinessException: 标签不存在
        """
        tag = self.db.query(CulturalTag).filter(
            CulturalTag.id == tag_id
        ).first()

        if not tag:
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"标签ID {tag_id} 不存在"
            )

        return tag

    def list_tags(
        self,
        query: CulturalTagListQuery
    ) -> Tuple[List[CulturalTag], int]:
        """获取标签列表

        Args:
            query: 查询参数

        Returns:
            (标签列表, 总数)
        """
        # 构建查询
        q = self.db.query(CulturalTag)

        # 筛选条件
        if query.category:
            q = q.filter(CulturalTag.category == query.category)

        if query.is_active is not None:
            q = q.filter(CulturalTag.is_active == query.is_active)

        if query.keyword:
            # 搜索标签名称、描述和关键词
            keyword_pattern = f"%{query.keyword}%"
            q = q.filter(
                or_(
                    CulturalTag.name.like(keyword_pattern),
                    CulturalTag.description.like(keyword_pattern),
                    CulturalTag.keywords.like(keyword_pattern)
                )
            )

        # 总数
        total = q.count()

        # 排序：按使用次数降序，然后按创建时间降序
        q = q.order_by(desc(CulturalTag.usage_count), desc(CulturalTag.created_at))

        # 分页
        offset = (query.page - 1) * query.page_size
        tags = q.offset(offset).limit(query.page_size).all()

        return tags, total

    def update_tag(self, tag_id: int, tag_data: CulturalTagUpdate) -> CulturalTag:
        """更新标签

        Args:
            tag_id: 标签ID
            tag_data: 更新数据

        Returns:
            更新后的标签对象

        Raises:
            BusinessException: 标签不存在或名称冲突
        """
        tag = self.get_tag_by_id(tag_id)

        # 检查名称冲突
        if tag_data.name and tag_data.name != tag.name:
            existing_tag = self.db.query(CulturalTag).filter(
                CulturalTag.name == tag_data.name,
                CulturalTag.id != tag_id
            ).first()

            if existing_tag:
                raise BusinessException(
                    code=ErrorCode.RECORD_ALREADY_EXISTS,
                    message=f"标签名称 '{tag_data.name}' 已存在"
                )

        # 验证父标签
        if tag_data.parent_id:
            if tag_data.parent_id == tag_id:
                raise BusinessException(
                    code=ErrorCode.PARAM_VALUE_INVALID,
                    message="标签不能将自己设为父标签"
                )

            parent_tag = self.get_tag_by_id(tag_data.parent_id)
            if not parent_tag:
                raise BusinessException(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message=f"父标签ID {tag_data.parent_id} 不存在"
                )

        # 更新字段
        update_data = tag_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)

        self.db.commit()
        self.db.refresh(tag)

        logger.info(f"更新文化标签成功: id={tag.id}, name={tag.name}")
        return tag

    def delete_tag(self, tag_id: int) -> None:
        """删除标签

        如果标签被产品使用，则软删除（设置is_active=False）
        否则硬删除

        Args:
            tag_id: 标签ID

        Raises:
            BusinessException: 标签不存在
        """
        tag = self.get_tag_by_id(tag_id)

        # 检查是否有产品使用此标签
        product_count = self.db.query(func.count()).select_from(product_tags).filter(
            product_tags.c.tag_id == tag_id
        ).scalar()

        if product_count > 0:
            # 软删除：标记为不活跃
            tag.is_active = False
            self.db.commit()
            logger.info(f"软删除文化标签: id={tag.id}, name={tag.name}, 关联产品数={product_count}")
        else:
            # 硬删除
            self.db.delete(tag)
            self.db.commit()
            logger.info(f"硬删除文化标签: id={tag.id}, name={tag.name}")

    # ==================== 标签推荐 ====================

    def recommend_tags_by_product(
        self,
        product_id: int,
        limit: int = 10
    ) -> List[CulturalTag]:
        """基于产品推荐标签（协同过滤）

        算法：
        1. 找到同类产品（相同category或region）
        2. 统计这些产品常用的标签
        3. 排除当前产品已有的标签
        4. 按使用频率排序

        Args:
            product_id: 产品ID
            limit: 推荐数量

        Returns:
            推荐的标签列表
        """
        # 获取当前产品
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []

        # 获取当前产品已有的标签ID
        current_tag_ids = [tag.id for tag in product.tags]

        # 查找同类产品
        similar_products = self.db.query(Product).filter(
            and_(
                Product.id != product_id,
                or_(
                    Product.category == product.category,
                    Product.origin_province == product.origin_province
                )
            )
        ).limit(50).all()

        if not similar_products:
            # 如果没有同类产品，返回热门标签
            return self.get_popular_tags(limit)

        # 统计同类产品使用的标签及其频率
        tag_frequency = {}
        for similar_product in similar_products:
            for tag in similar_product.tags:
                if tag.id not in current_tag_ids and tag.is_active:
                    tag_frequency[tag.id] = tag_frequency.get(tag.id, 0) + 1

        # 按频率排序
        sorted_tag_ids = sorted(tag_frequency.keys(), key=lambda x: tag_frequency[x], reverse=True)

        # 获取标签对象
        recommended_tag_ids = sorted_tag_ids[:limit]
        if not recommended_tag_ids:
            return []

        tags = self.db.query(CulturalTag).filter(
            CulturalTag.id.in_(recommended_tag_ids)
        ).all()

        # 按推荐顺序排序
        tag_dict = {tag.id: tag for tag in tags}
        recommended_tags = [tag_dict[tag_id] for tag_id in recommended_tag_ids if tag_id in tag_dict]

        return recommended_tags

    def recommend_tags_by_keywords(
        self,
        keywords: str,
        limit: int = 10
    ) -> List[CulturalTag]:
        """基于关键词推荐标签

        Args:
            keywords: 关键词字符串
            limit: 推荐数量

        Returns:
            推荐的标签列表
        """
        if not keywords:
            return self.get_popular_tags(limit)

        # 分词（简单按空格和逗号分割）
        keyword_list = [k.strip() for k in keywords.replace(',', ' ').split() if k.strip()]

        if not keyword_list:
            return self.get_popular_tags(limit)

        # 构建搜索条件
        conditions = []
        for keyword in keyword_list:
            pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    CulturalTag.name.like(pattern),
                    CulturalTag.description.like(pattern),
                    CulturalTag.keywords.like(pattern)
                )
            )

        # 查询匹配的标签
        tags = self.db.query(CulturalTag).filter(
            CulturalTag.is_active == True,
            or_(*conditions)
        ).order_by(
            desc(CulturalTag.usage_count)
        ).limit(limit).all()

        return tags

    def get_popular_tags(self, limit: int = 10) -> List[CulturalTag]:
        """获取热门标签

        Args:
            limit: 返回数量

        Returns:
            热门标签列表
        """
        tags = self.db.query(CulturalTag).filter(
            CulturalTag.is_active == True
        ).order_by(
            desc(CulturalTag.usage_count),
            desc(CulturalTag.created_at)
        ).limit(limit).all()

        return tags

    # ==================== 产品标签关联管理 ====================

    def assign_tags_to_product(
        self,
        product_id: int,
        tag_ids: List[int]
    ) -> Product:
        """为产品分配标签

        Args:
            product_id: 产品ID
            tag_ids: 标签ID列表

        Returns:
            更新后的产品对象

        Raises:
            BusinessException: 产品或标签不存在
        """
        # 获取产品
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"产品ID {product_id} 不存在"
            )

        # 验证所有标签存在
        tags = self.db.query(CulturalTag).filter(
            CulturalTag.id.in_(tag_ids),
            CulturalTag.is_active == True
        ).all()

        if len(tags) != len(tag_ids):
            found_ids = {tag.id for tag in tags}
            missing_ids = set(tag_ids) - found_ids
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"标签ID {missing_ids} 不存在或未启用"
            )

        # 获取当前标签
        current_tag_ids = {tag.id for tag in product.tags}

        # 分别处理新增和移除的标签
        new_tag_ids = set(tag_ids) - current_tag_ids
        removed_tag_ids = current_tag_ids - set(tag_ids)

        # 更新usage_count
        if new_tag_ids:
            self.db.query(CulturalTag).filter(
                CulturalTag.id.in_(new_tag_ids)
            ).update(
                {CulturalTag.usage_count: CulturalTag.usage_count + 1},
                synchronize_session=False
            )

        if removed_tag_ids:
            self.db.query(CulturalTag).filter(
                CulturalTag.id.in_(removed_tag_ids)
            ).update(
                {CulturalTag.usage_count: func.greatest(CulturalTag.usage_count - 1, 0)},
                synchronize_session=False
            )

        # 更新产品标签关联
        product.tags = tags
        self.db.commit()
        self.db.refresh(product)

        logger.info(f"为产品分配标签: product_id={product_id}, tag_ids={tag_ids}")
        return product

    def remove_tag_from_product(
        self,
        product_id: int,
        tag_id: int
    ) -> Product:
        """从产品移除标签

        Args:
            product_id: 产品ID
            tag_id: 标签ID

        Returns:
            更新后的产品对象

        Raises:
            BusinessException: 产品或标签不存在
        """
        # 获取产品
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"产品ID {product_id} 不存在"
            )

        # 获取标签
        tag = self.get_tag_by_id(tag_id)

        # 检查产品是否有此标签
        if tag not in product.tags:
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"产品未关联标签ID {tag_id}"
            )

        # 移除标签
        product.tags.remove(tag)

        # 更新usage_count
        tag.decrement_usage()

        self.db.commit()
        self.db.refresh(product)

        logger.info(f"从产品移除标签: product_id={product_id}, tag_id={tag_id}")
        return product

    def get_product_tags(self, product_id: int) -> List[CulturalTag]:
        """获取产品的所有标签

        Args:
            product_id: 产品ID

        Returns:
            标签列表

        Raises:
            BusinessException: 产品不存在
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message=f"产品ID {product_id} 不存在"
            )

        return product.tags

    # ==================== 统计分析 ====================

    def get_tag_statistics(self) -> Dict[str, Any]:
        """获取标签统计信息

        Returns:
            统计数据字典
        """
        # 总标签数
        total_tags = self.db.query(func.count(CulturalTag.id)).scalar()

        # 启用标签数
        active_tags = self.db.query(func.count(CulturalTag.id)).filter(
            CulturalTag.is_active == True
        ).scalar()

        # 分类分布
        category_distribution = {}
        for category_info in TAG_CATEGORIES:
            code = category_info['code']
            count = self.db.query(func.count(CulturalTag.id)).filter(
                CulturalTag.category == code,
                CulturalTag.is_active == True
            ).scalar()
            category_distribution[code] = {
                "name": category_info['name'],
                "count": count
            }

        # 热门标签（Top 10）
        popular_tags = self.get_popular_tags(10)

        return {
            "total_tags": total_tags,
            "active_tags": active_tags,
            "category_distribution": category_distribution,
            "popular_tags": popular_tags
        }

    # ==================== 初始化数据 ====================

    @staticmethod
    def initialize_default_tags(db: Session) -> int:
        """初始化默认文化标签

        Args:
            db: 数据库会话

        Returns:
            创建的标签数量
        """
        default_tags = [
            # 地理标志
            {"name": "锡林郭勒羊肉", "category": "geo", "description": "锡林郭勒盟特产，国家地理标志产品，以肉质鲜嫩、无膻味著称", "keywords": "羊肉,地理标志,锡林郭勒,草原"},
            {"name": "科尔沁牛肉", "category": "geo", "description": "科尔沁草原特产牛肉，肉质细嫩、营养丰富", "keywords": "牛肉,地理标志,科尔沁,草原"},
            {"name": "呼伦贝尔牛奶", "category": "geo", "description": "呼伦贝尔草原优质奶源，天然纯净", "keywords": "牛奶,乳制品,呼伦贝尔,草原"},
            {"name": "鄂尔多斯羊绒", "category": "geo", "description": "鄂尔多斯高原特产羊绒，世界顶级品质", "keywords": "羊绒,地理标志,鄂尔多斯"},
            {"name": "阿拉善驼奶", "category": "geo", "description": "阿拉善盟特产驼奶，营养价值极高", "keywords": "驼奶,地理标志,阿拉善"},

            # 民族文化
            {"name": "蒙古族传统", "category": "ethnicity", "description": "蒙古族传统饮食文化的传承", "keywords": "蒙古族,传统,民族,文化"},
            {"name": "游牧文化", "category": "ethnicity", "description": "草原游牧民族的饮食文化", "keywords": "游牧,草原,文化,民族"},
            {"name": "蒙古族奶制品文化", "category": "ethnicity", "description": "蒙古族独特的奶制品文化传统", "keywords": "奶制品,蒙古族,传统,文化"},

            # 历史传承
            {"name": "马背民族", "category": "history", "description": "马背民族的饮食传统和历史", "keywords": "马背,民族,历史,传统"},
            {"name": "草原文化", "category": "history", "description": "千年草原文化的传承与发展", "keywords": "草原,文化,传承,历史"},
            {"name": "成吉思汗文化", "category": "history", "description": "与成吉思汗相关的历史文化传承", "keywords": "成吉思汗,历史,文化"},

            # 工艺特色
            {"name": "传统奶制品工艺", "category": "craft", "description": "蒙古族传统奶制品制作工艺", "keywords": "奶制品,工艺,传统,制作"},
            {"name": "风干肉制作", "category": "craft", "description": "传统风干肉制作技艺", "keywords": "风干肉,工艺,制作,传统"},
            {"name": "手工奶豆腐", "category": "craft", "description": "传统手工奶豆腐制作工艺", "keywords": "奶豆腐,手工,工艺,传统"},
            {"name": "奶茶熬制", "category": "craft", "description": "蒙古族传统奶茶熬制技艺", "keywords": "奶茶,熬制,工艺,传统"},

            # 节日习俗
            {"name": "那达慕", "category": "festival", "description": "蒙古族传统节日那达慕", "keywords": "那达慕,节日,传统,蒙古族"},
            {"name": "祭敖包", "category": "festival", "description": "蒙古族祭敖包习俗", "keywords": "敖包,祭祀,习俗,蒙古族"},
            {"name": "白月节", "category": "festival", "description": "蒙古族传统春节（查干萨日）", "keywords": "白月节,春节,节日,蒙古族"},

            # 营养价值
            {"name": "高蛋白", "category": "nutrition", "description": "富含优质蛋白质", "keywords": "蛋白质,营养,健康"},
            {"name": "低脂肪", "category": "nutrition", "description": "低脂肪健康食品", "keywords": "低脂,健康,营养"},
            {"name": "富含微量元素", "category": "nutrition", "description": "富含铁、锌等微量元素", "keywords": "微量元素,营养,健康"},
            {"name": "天然有机", "category": "nutrition", "description": "天然有机，无污染", "keywords": "有机,天然,健康"},

            # 文化故事
            {"name": "草原传说", "category": "story", "description": "草原上流传的美丽传说", "keywords": "传说,故事,草原,文化"},
            {"name": "游牧生活", "category": "story", "description": "游牧民族的生活故事", "keywords": "游牧,生活,故事"},
            {"name": "马背上的美食", "category": "story", "description": "马背民族的美食故事", "keywords": "美食,故事,马背"},
        ]

        created_count = 0
        for tag_data in default_tags:
            # 检查是否已存在
            existing = db.query(CulturalTag).filter(
                CulturalTag.name == tag_data['name']
            ).first()

            if not existing:
                tag = CulturalTag(**tag_data)
                db.add(tag)
                created_count += 1

        db.commit()
        logger.info(f"初始化默认文化标签完成: 创建了 {created_count} 个标签")
        return created_count
