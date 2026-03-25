"""
RAG（检索增强生成）知识库服务 - AI-007 内容生成优化

功能：
- 文化元素知识库构建和维护
- 向量化和检索（使用FAISS）
- 产品相关背景信息检索
- 营销素材库管理

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("FAISS/sentence_transformers not installed. RAG features may be limited.")

from app.models.product import Product
from app.models.cultural_tag import CulturalTag
from app.core.config import settings


class CulturalKnowledgeBase:
    """文化元素知识库 - 支持向量检索"""

    def __init__(self):
        """初始化知识库"""
        self.cache_dir = Path(__file__).parent.parent / "data" / "rag"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化向量模型
        if HAS_FAISS:
            self.encoder = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2',
                device='cpu'
            )
            self.index = None
            self.documents = []
            self.dimension = 384  # MiniLM-L12-v2 的输出维度
        else:
            logger.warning("FAISS not available, using fallback retrieval method")
            self.index = None
            self.documents = []

    async def build_index(self, db: Session) -> bool:
        """
        构建向量索引（异步）

        Args:
            db: 数据库会话

        Returns:
            构建是否成功
        """
        if not HAS_FAISS:
            logger.info("跳过FAISS索引构建（未安装依赖）")
            return False

        try:
            logger.info("开始构建RAG知识库索引...")

            # 1. 加载所有文化数据
            self.documents = await self._load_cultural_data(db)

            if not self.documents:
                logger.warning("没有找到文化数据")
                return False

            # 2. 提取文本并生成向量
            texts = [doc['text'] for doc in self.documents]
            logger.info(f"正在对 {len(texts)} 个文档进行向量化...")

            # 分批处理大型文档集
            embeddings_list = []
            batch_size = 32
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.encoder.encode(batch, convert_to_numpy=True)
                embeddings_list.append(batch_embeddings)

            embeddings = np.vstack(embeddings_list)

            # 3. 构建FAISS索引
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings.astype('float32'))

            logger.info(f"RAG索引构建完成: {len(self.documents)} 个文档已索引")

            # 4. 保存索引到磁盘（可选）
            await self._save_index()

            return True

        except Exception as e:
            logger.error(f"RAG索引构建失败: {str(e)}")
            return False

    async def retrieve_cultural_context(
        self,
        product: Product,
        top_k: int = 5,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        检索与产品相关的文化背景（RAG核心）

        Args:
            product: 产品对象
            top_k: 返回的结果数
            db: 数据库会话

        Returns:
            文化背景结果列表
        """
        if not self.documents:
            logger.warning("知识库为空，请先构建索引")
            return await self._fallback_retrieve(product, top_k, db)

        try:
            # 构建查询
            query_text = f"{product.name} {product.category} {product.origin_province} {product.origin_city}"

            if product.cultural_tags:
                # 处理 cultural_tags 可能是字符串或列表的情况
                if isinstance(product.cultural_tags, str):
                    query_text += f" {product.cultural_tags}"
                elif isinstance(product.cultural_tags, (list, tuple)):
                    query_text += f" {' '.join(str(tag) for tag in product.cultural_tags)}"

            # 向量检索
            if HAS_FAISS and self.index is not None:
                query_embedding = self.encoder.encode([query_text], convert_to_numpy=True)[0].astype('float32')
                distances, indices = self.index.search(
                    query_embedding.reshape(1, -1),
                    min(top_k, len(self.documents))
                )

                results = []
                for list_idx, idx in enumerate(indices[0]):
                    doc = self.documents[int(idx)]
                    # 计算相似度（从距离转换）
                    distance = distances[0][list_idx]
                    similarity = 1.0 / (1.0 + distance)

                    results.append({
                        'type': doc.get('type'),
                        'content': doc.get('text'),
                        'relevance': float(similarity),
                        'category': doc.get('category'),
                        'source': doc.get('source')
                    })

                return sorted(results, key=lambda x: x['relevance'], reverse=True)
            else:
                return await self._fallback_retrieve(product, top_k, db)

        except Exception as e:
            logger.error(f"文化背景检索失败: {str(e)}")
            return await self._fallback_retrieve(product, top_k, db)

    async def retrieve_marketing_materials(
        self,
        category: str,
        style: str,
        top_k: int = 3,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        检索营销素材库

        Args:
            category: 产品类别
            style: 内容风格
            top_k: 返回结果数
            db: 数据库会话

        Returns:
            营销素材列表
        """
        try:
            # 构建查询
            query_text = f"营销 {category} {style}"

            if not HAS_FAISS or self.index is None:
                return []

            query_embedding = self.encoder.encode([query_text], convert_to_numpy=True)[0].astype('float32')
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(top_k, len(self.documents))
            )

            results = []
            for idx in indices[0]:
                doc = self.documents[int(idx)]
                if doc.get('type') == 'marketing_material':
                    results.append({
                        'content': doc.get('text'),
                        'category': doc.get('category'),
                        'style': doc.get('style'),
                        'source': doc.get('source')
                    })

            return results[:top_k]

        except Exception as e:
            logger.error(f"营销素材检索失败: {str(e)}")
            return []

    async def _load_cultural_data(self, db: Session) -> List[Dict[str, Any]]:
        """
        从数据库加载文化数据

        Args:
            db: 数据库会话

        Returns:
            文化数据列表
        """
        cultural_elements = []

        try:
            # 1. 地理标志信息
            products_with_certs = db.query(Product).filter(
                Product.certification_type.isnot(None)
            ).all()

            for product in products_with_certs:
                if product.certification_type and product.origin_province:
                    cultural_elements.append({
                        'type': 'geo_indicator',
                        'category': product.origin_province,
                        'text': f"{product.origin_province}{product.certification_type}: {product.name}",
                        'source': f"product_{product.id}",
                        'metadata': {
                            'certification': product.certification_type,
                            'province': product.origin_province,
                            'product_id': product.id
                        }
                    })

            # 2. 文化标签
            tags = db.query(CulturalTag).filter(
                CulturalTag.is_active == True
            ).all()

            for tag in tags:
                cultural_elements.append({
                    'type': 'cultural_tag',
                    'category': tag.category,
                    'text': f"{tag.name}: {tag.description}",
                    'source': f"tag_{tag.id}",
                    'metadata': {
                        'tag_name': tag.name,
                        'keywords': tag.keywords
                    }
                })

            # 3. 产品故事
            products_with_stories = db.query(Product).filter(
                Product.cultural_story.isnot(None)
            ).all()

            for product in products_with_stories:
                if product.cultural_story:
                    cultural_elements.append({
                        'type': 'cultural_story',
                        'category': product.category,
                        'text': product.cultural_story,
                        'source': f"product_story_{product.id}",
                        'metadata': {
                            'product_name': product.name,
                            'product_id': product.id
                        }
                    })

            logger.info(f"加载了 {len(cultural_elements)} 个文化元素")
            return cultural_elements

        except Exception as e:
            logger.error(f"加载文化数据失败: {str(e)}")
            return []

    async def _fallback_retrieve(
        self,
        product: Product,
        top_k: int,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        备用检索方法（当FAISS不可用时）

        Args:
            product: 产品对象
            top_k: 返回结果数
            db: 数据库会话

        Returns:
            检索结果
        """
        results = []

        try:
            if db:
                # 基于产品类别查询相关标签
                related_tags = db.query(CulturalTag).filter(
                    CulturalTag.is_active == True
                ).order_by(
                    CulturalTag.usage_count.desc()
                ).limit(top_k).all()

                for tag in related_tags:
                    results.append({
                        'type': 'cultural_tag',
                        'content': f"{tag.name}: {tag.description}",
                        'relevance': 0.5,
                        'category': tag.category,
                        'source': f"tag_{tag.id}"
                    })

            return results

        except Exception as e:
            logger.error(f"备用检索失败: {str(e)}")
            return []

    async def _save_index(self) -> None:
        """保存索引到磁盘"""
        try:
            if HAS_FAISS and self.index:
                index_path = self.cache_dir / "faiss_index.bin"
                meta_path = self.cache_dir / "index_metadata.json"

                faiss.write_index(self.index, str(index_path))

                # 保存元数据（用于恢复）
                metadata = {
                    'dimension': self.dimension,
                    'num_documents': len(self.documents),
                    'document_count': len(self.documents)
                }

                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)

                logger.info(f"索引已保存到 {index_path}")
        except Exception as e:
            logger.error(f"保存索引失败: {str(e)}")

    async def load_index(self) -> bool:
        """从磁盘加载索引"""
        try:
            if not HAS_FAISS:
                return False

            index_path = self.cache_dir / "faiss_index.bin"

            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
                logger.info(f"索引已从 {index_path} 加载")
                return True

            return False
        except Exception as e:
            logger.error(f"加载索引失败: {str(e)}")
            return False


class MarketingMaterialLibrary:
    """营销素材库 - 存储和管理营销内容模板"""

    def __init__(self):
        """初始化营销素材库"""
        self.materials = self._load_default_materials()

    def _load_default_materials(self) -> Dict[str, List[str]]:
        """加载默认营销素材"""
        return {
            'opening_lines': {
                'casual': [
                    '你知道吗？',
                    '有没有想过',
                    '不少人都在追捧',
                    '最近发现了一个宝藏',
                    '听说过吗？',
                    '真的没吃过',
                ],
                'professional': [
                    '根据市场调研',
                    '经过多年发展',
                    '作为业界领先的',
                    '结合现代消费需求',
                    '凭借优势',
                    '基于深厚的文化底蕴',
                ],
                'emotional': [
                    '每一个产品背后',
                    '代代相传的手艺',
                    '守护这份美味',
                    '源于对品质的执着',
                    '是多少人的回忆',
                    '承载着故事',
                ],
            },
            'core_messages': {
                'quality': [
                    '优质原料精心打造',
                    '严格的品质把控',
                    '每一步都用心打磨',
                    '只为呈现最好的',
                ],
                'culture': [
                    '蒙古族文化的传承',
                    '千年历史的见证',
                    '民族工艺的精粹',
                    '游牧文明的遗产',
                ],
                'health': [
                    '营养丰富',
                    '天然健康',
                    '无污染纯净',
                    '富含微量元素',
                ],
            },
            'closing_lines': {
                'casual': [
                    '绝了！',
                    '必须尝一尝',
                    '后悔会很大',
                    '值得拥有',
                    '一口就停不下来',
                ],
                'professional': [
                    '值得信赖的选择',
                    '品质的保证',
                    '市场的选择',
                    '消费者的认可',
                ],
                'emotional': [
                    '品味生活的方式',
                    '传承的味道',
                    '记忆中的美好',
                    '心中的珍藏',
                ],
            }
        }

    def get_material(self, material_type: str, style: str, default: str = "") -> str:
        """
        获取营销素材

        Args:
            material_type: 素材类型 (opening_lines, core_messages, closing_lines)
            style: 风格 (casual, professional, emotional)
            default: 默认值

        Returns:
            随机选择的素材
        """
        try:
            if material_type in self.materials and style in self.materials[material_type]:
                import random
                return random.choice(self.materials[material_type][style])
            return default
        except Exception as e:
            logger.error(f"获取营销素材失败: {str(e)}")
            return default
