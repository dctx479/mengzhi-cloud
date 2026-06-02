"""
客服知识库 RAG 服务

功能：
- 基于 FAISS 的向量检索
- 内蒙古农畜产品 FAQ 知识库
- 支持增量更新

版本: 1.0
更新日期: 2026-05-25
"""

import os
import json
import asyncio
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("FAISS not installed. Kefu RAG will use keyword fallback.")

from app.core.config import settings


# 知识库根目录
KB_DIR = Path(__file__).parent.parent / "data" / "kefu_kb"
KB_DIR.mkdir(parents=True, exist_ok=True)


class KefuKnowledgeBase:
    """客服知识库 - 向量检索"""

    _build_lock = threading.Lock()
    _instance: Optional["KefuKnowledgeBase"] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if KefuKnowledgeBase._initialized:
            return

        self.kb_dir = KB_DIR
        self.index_path = self.kb_dir / "faiss_index.bin"
        self.docs_path = self.kb_dir / "documents.json"
        self.dimension = 384  # MiniLM-L12-v2

        self.encoder = None
        self.index = None
        self.documents: List[Dict[str, str]] = []

        if HAS_FAISS:
            self.encoder = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2',
                device='cpu'
            )
            self._load_index()

        KefuKnowledgeBase._initialized = True

    def _load_index(self):
        """加载已有索引"""
        if self.index_path.exists() and self.docs_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.docs_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                logger.info(f"客服知识库已加载: {len(self.documents)} 条文档")
            except Exception as e:
                logger.warning(f"加载客服知识库失败: {e}, 将重新构建")
                self.index = None
                self.documents = []

    async def build_index(self) -> bool:
        """构建或重建知识库索引"""
        if not HAS_FAISS:
            logger.warning("FAISS 未安装，使用关键词 fallback")
            return False

        if not self.encoder:
            self.encoder = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2', device='cpu'
            )

        if not KefuKnowledgeBase._build_lock.acquire(blocking=True, timeout=10):
            logger.warning("知识库正在构建中，跳过本次")
            return False

        try:
            # 加载 Markdown 文件
            docs = self._load_kb_files()
            if not docs:
                logger.warning("未找到知识库文件，跳过构建")
                return False

            # 转换为文本
            texts = [d["content"] for d in docs]
            self.documents = docs

            # 向量化
            embeddings = self.encoder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            embeddings = embeddings.astype('float32')

            # 构建 FAISS 索引
            self.index = faiss.IndexFlatIP(self.dimension)
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)

            # 保存
            faiss.write_index(self.index, str(self.index_path))
            with open(self.docs_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)

            logger.info(f"客服知识库构建完成: {len(self.documents)} 条文档")
            return True

        except Exception as e:
            logger.error(f"构建客服知识库失败: {e}")
            return False
        finally:
            KefuKnowledgeBase._build_lock.release()

    def _load_kb_files(self) -> List[Dict[str, str]]:
        """加载所有知识库 Markdown 文件"""
        docs = []
        for md_file in self.kb_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                # 按 ## 分段拆分
                sections = self._split_sections(content, md_file.stem)
                docs.extend(sections)
            except Exception as e:
                logger.warning(f"加载 {md_file} 失败: {e}")
        return docs

    def _split_sections(self, content: str, source: str) -> List[Dict[str, str]]:
        """按 ## 标题拆分内容"""
        sections = []
        parts = content.split("\n## ")
        # 第一个 part 没有 ## 前缀
        if parts[0].strip():
            sections.append({
                "source": source,
                "title": parts[0].split("\n")[0].lstrip("# ").strip(),
                "content": parts[0].strip(),
            })
        for part in parts[1:]:
            lines = part.split("\n", 1)
            title = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            sections.append({
                "source": source,
                "title": title,
                "content": f"## {title}\n{body}",
            })
        return sections

    async def query(self, question: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        检索最相关的知识库片段

        Args:
            question: 用户问题
            top_k: 返回条数

        Returns:
            [{"title", "content", "source"}, ...]
        """
        if not HAS_FAISS or not self.index or not self.encoder:
            return self._keyword_fallback(question)

        if self.index.ntotal == 0:
            return self._keyword_fallback(question)

        top_k = min(top_k, 10)
        try:
            query_vec = self.encoder.encode([question], convert_to_numpy=True)[0].astype('float32')
            faiss.normalize_L2(query_vec.reshape(1, -1))
            distances, indices = self.index.search(query_vec.reshape(1, -1), top_k)

            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    results.append({
                        **self.documents[idx],
                        "score": float(dist),
                    })
            return results
        except Exception as e:
            logger.error(f"RAG 检索失败: {e}")
            return self._keyword_fallback(question)

    def _keyword_fallback(self, question: str) -> List[Dict[str, str]]:
        """关键词 fallback（无 FAISS 时使用）"""
        results = []
        keywords = [w for w in question if len(w) >= 2]

        for doc in self.documents:
            score = sum(1 for kw in keywords if kw in doc["content"])
            if score > 0:
                results.append({**doc, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:3]

    def sync_products_to_kb(self, db) -> Dict[str, Any]:
        """混合同步: 保留手写静态KB + 从DB产品生成产品文档, 重建FAISS索引"""
        from app.models.product import Product, ProductStatus

        products = db.query(Product).filter(
            Product.deleted_at.is_(None),
            Product.status == ProductStatus.PUBLISHED,
        ).all()

        lines = [
            "# 产品信息（自动生成，请勿手动编辑）\n",
            f"> 生成时间: {__import__('datetime').datetime.now().isoformat()}\n",
            f"> 产品数量: {len(products)}\n\n",
        ]

        for p in products:
            lines.append(f"## {p.name}\n")
            lines.append(f"- 分类: {p.category or '未分类'}\n")
            if p.origin_province:
                origin = p.origin_province
                if p.origin_city:
                    origin += f" {p.origin_city}"
                lines.append(f"- 产地: {origin}\n")
            if p.price:
                lines.append(f"- 价格: ¥{float(p.price):.2f}\n")
            if p.description:
                lines.append(f"- 描述: {p.description[:300]}\n")
            if p.features and isinstance(p.features, list):
                lines.append(f"- 特点: {'、'.join(str(f) for f in p.features[:10])}\n")
            if p.cultural_story:
                lines.append(f"- 文化故事: {p.cultural_story[:200]}\n")
            lines.append("\n")

        auto_file = self.kb_dir / "_auto_products.md"
        auto_file.write_text("".join(lines), encoding="utf-8")

        static_docs = len(list(self.kb_dir.glob("[!_]*.md")))

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.build_index())
            else:
                loop.run_until_complete(self.build_index())
        except RuntimeError:
            asyncio.run(self.build_index())

        logger.info(f"知识库同步完成: {len(products)} 个产品, {static_docs} 个静态文档")
        return {
            "synced_count": len(products),
            "static_docs": static_docs,
            "auto_docs": 1,
            "auto_file": str(auto_file),
        }

    def answer(self, question: str, chat_history: List[Dict] = None) -> str:
        """基于知识库生成回答"""
        import httpx
        import asyncio

        retrieved = asyncio.run(self.query(question, top_k=3))

        if not retrieved:
            return None

        # 构建 context
        context_parts = []
        for i, doc in enumerate(retrieved, 1):
            context_parts.append(f"【参考资料{i}】\n{doc['content'][:500]}")
        context = "\n\n".join(context_parts)

        system_prompt = f"""你是一个内蒙古农畜产品平台的智能客服。请根据以下参考信息回答用户问题。
如果参考信息不足以回答，请说"这个问题我需要进一步了解"或转人工。

## 参考信息：
{context}

## 回答要求：
- 亲切、专业
- 3句话以内（除非用户追问细节）
- 如果涉及具体产品/价格信息，注明来源"""

        async def _call_llm():
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": question}
                            ],
                            "temperature": 0.5,
                            "max_tokens": 500,
                        }
                    )
                    result = resp.json()
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                logger.error(f"LLM 回答生成失败: {e}")
                return None

        return asyncio.run(_call_llm())