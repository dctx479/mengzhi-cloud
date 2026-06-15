"""
导出功能API - 完善版

支持产品列表导出为CSV和Excel格式，包含分批处理、自定义字段、权限验证等功能

版本: 2.0
创建日期: 2026-01-17
更新日期: 2026-01-21
"""

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import io
from typing import Optional, List
from datetime import datetime
import uuid
import urllib.parse

from app.api.deps import get_db, get_current_user, require_admin
from app.models.product import Product
from app.core.responses import error_response, success_response
from app.core.errors import ErrorCode, BusinessException
from app.core.logging_config import logger

router = APIRouter()

# 导出配置
BATCH_SIZE = 1000  # 分批处理大小
MAX_SYNC_EXPORT = 5000  # 同步导出最大记录数
MAX_EXPORT_LIMIT = 50000  # 导出绝对上限，超出拒绝请求



def _encode_filename_header(filename: str) -> str:
    """RFC 5987编码文件名，支持中文字符
    
    Args:
        filename: 原始文件名（可包含中文）
    
    Returns:
        RFC 5987格式的Content-Disposition值，兼容所有浏览器
    """
    encoded = urllib.parse.quote(filename.encode("utf-8"))
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "download"
    return "attachment; filename=" + ascii_fallback + "; filename*=UTF-8'''" + encoded
def _build_product_dict(product: Product, fields: Optional[List[str]] = None) -> dict:
    """构建产品字典，支持自定义字段"""
    specs = product.specifications or {}
    all_fields = {
        "产品ID": product.id,
        "产品UUID": product.product_uuid,
        "产品名称": product.name,
        "分类": product.category,
        "子分类": product.sub_category or "",
        "价格（元）": float(product.price) if product.price else 0,
        "产地": product.origin_province or "",
        "产地城市": product.origin_city or "",
        "状态": product.status.value if hasattr(product.status, 'value') else str(product.status),
        "浏览量": product.view_count or 0,
        "生成次数": product.generate_count or 0,
        "文化标签": ", ".join(product.cultural_tags) if isinstance(product.cultural_tags, list) else (product.cultural_tags or ""),
        "文化故事": product.cultural_story or "",
        "主图URL": product.main_image_url or "",
        "描述": (product.description or "")[:500],
        "来源店铺": specs.get("shop_title") or specs.get("shop_name") or "",
        "创建时间": product.created_at.strftime("%Y-%m-%d %H:%M:%S") if product.created_at else "",
        "更新时间": product.updated_at.strftime("%Y-%m-%d %H:%M:%S") if product.updated_at else ""
    }

    if fields:
        return {k: v for k, v in all_fields.items() if k in fields}
    return all_fields


def _export_to_csv(df: pd.DataFrame, filename: str) -> StreamingResponse:
    """导出为CSV格式
    
    使用生成器函数处理CSV内容，确保正确的流式传输。
    BUG FIX: 使用生成器函数而不是iter([string])来正确流式传输数据
    """
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    csv_content = output.getvalue()

    def iter_csv():
        """生成器：yield CSV内容"""
        yield csv_content

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": _encode_filename_header(filename),
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


def _export_to_excel(df: pd.DataFrame, filename: str) -> StreamingResponse:
    """导出为Excel格式，带样式优化"""
    from openpyxl.styles import Font, PatternFill, Alignment

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='产品列表', index=False)

        worksheet = writer.sheets['产品列表']

        # 标题行样式
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # 自动调整列宽
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except (TypeError, AttributeError) as e:
                    logger.debug(f"计算列宽失败: {e}")
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    def iter_bytes():
        """生成器：逐块读取BytesIO内容
        
        以8KB块的形式流式传输二进制数据，避免一次性加载整个文件到内存。
        """
        while True:
            chunk = output.read(8192)  # 8KB chunks
            if not chunk:
                break
            yield chunk

    return StreamingResponse(
        iter_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _encode_filename_header(filename)}
    )


@router.get("/products", tags=["导出"])
async def export_products(
    format: str = Query("csv", pattern="^(csv|excel)$", description="导出格式：csv或excel"),
    category: Optional[str] = Query(None, description="产品类别筛选"),
    region: Optional[str] = Query(None, description="产地筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    fields: Optional[str] = Query(None, description="自定义导出字段，逗号分隔"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出产品列表（优化版）

    功能特性:
    - 支持CSV和Excel格式
    - 支持筛选条件
    - 支持自定义导出字段
    - 分批处理大数据量
    - Excel带样式优化
    - 唯一文件名

    参数:
        format: 导出格式（csv或excel）
        category: 类别筛选（可选）
        region: 产地筛选（可选）
        status: 状态筛选（可选）
        fields: 自定义字段，如 "产品名称,SKU,价格（元）"
        current_user: 当前用户
        db: 数据库会话

    返回:
        CSV或Excel文件流

    示例:
        GET /api/v1/export/products?format=csv
        GET /api/v1/export/products?format=excel&category=肉类&fields=产品名称,SKU,价格（元）
    """
    try:
        # 权限验证：记录导出操作
        logger.info(f"用户 {current_user.get('user_id', 'unknown')} 开始导出产品，格式: {format}")

        # 构建查询
        query = db.query(Product).filter(Product.deleted_at.is_(None))

        # 应用筛选
        if category:
            query = query.filter(Product.category == category)
        if region:
            query = query.filter(Product.origin_province == region)
        if status_filter:
            query = query.filter(Product.status == status_filter)

        # 检查数据量
        total_count = query.count()

        if total_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    code=ErrorCode.RECORD_NOT_FOUND,
                    message="没有可导出的产品数据"
                ).dict()
            )

        if total_count > MAX_EXPORT_LIMIT:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    code=ErrorCode.INVALID_PARAMS,
                    message=f"导出数据量 {total_count} 超过上限 {MAX_EXPORT_LIMIT}，请缩小筛选范围"
                ).dict()
            )

        logger.info(f"准备导出 {total_count} 条产品记录")

        # 解析自定义字段
        custom_fields = [f.strip() for f in fields.split(",")] if fields else None

        # 分批处理数据
        data = []
        for offset in range(0, total_count, BATCH_SIZE):
            batch = query.offset(offset).limit(BATCH_SIZE).all()
            for p in batch:
                data.append(_build_product_dict(p, custom_fields))

        # 创建DataFrame
        df = pd.DataFrame(data)

        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"products_{timestamp}_{unique_id}.{'csv' if format == 'csv' else 'xlsx'}"

        # 根据格式导出
        if format == "csv":
            response = _export_to_csv(df, filename)
        else:
            response = _export_to_excel(df, filename)

        logger.info(f"成功导出 {total_count} 条记录到 {filename}")
        return response

    except BusinessException as e:
        logger.warning(f"导出产品失败: {e.message}")
        return JSONResponse(
            status_code=e.get_http_status(),
            content=error_response(code=e.code, message=e.message).dict()
        )
    except Exception as e:
        logger.error(f"导出产品异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="导出失败"
            ).dict()
        )


@router.get("/products/template", tags=["导出"])
async def download_import_template(
    format: str = Query("excel", pattern="^(csv|excel)$", description="模板格式"),
    current_user: dict = Depends(require_admin)
):
    """下载产品导入模板（需要管理员权限）

    参数:
        format: 模板格式（csv或excel）
        current_user: 当前用户（需要管理员权限）

    返回:
        CSV或Excel模板文件
    """
    try:
        logger.info(f"管理员 {current_user.get('user_id', 'unknown')} 下载导入模板，格式: {format}")

        template_data = {
            "产品名称": ["示例产品"],
            "分类": ["肉类"],
            "价格（元）": [99.00],
            "产地": ["呼和浩特"],
            "状态": ["published"],
            "文化标签": ["草原牛肉"],
            "文化故事": ["来自内蒙古大草原的优质牛肉"]
        }

        df = pd.DataFrame(template_data)

        if format == "csv":
            return _export_to_csv(df, "product_import_template.csv")
        else:
            return _export_to_excel(df, "product_import_template.xlsx")

    except Exception as e:
        logger.error(f"下载模板异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code=ErrorCode.SYSTEM_ERROR,
                message="下载模板失败"
            ).dict()
        )


@router.get("/products/fields", tags=["导出"])
async def get_available_fields(
    current_user: dict = Depends(get_current_user)
):
    """获取可导出的字段列表

    返回:
        可用字段列表及说明
    """
    fields = [
        {"name": "产品ID", "description": "产品唯一标识"},
        {"name": "产品UUID", "description": "产品UUID"},
        {"name": "产品名称", "description": "产品名称"},
        {"name": "分类", "description": "产品分类"},
        {"name": "子分类", "description": "产品子分类"},
        {"name": "价格（元）", "description": "产品价格"},
        {"name": "产地", "description": "产地省份"},
        {"name": "产地城市", "description": "产地城市"},
        {"name": "状态", "description": "产品状态"},
        {"name": "浏览量", "description": "浏览次数"},
        {"name": "生成次数", "description": "内容生成次数"},
        {"name": "文化标签", "description": "文化标签"},
        {"name": "文化故事", "description": "文化故事"},
        {"name": "来源店铺", "description": "外部来源店铺名称"},
        {"name": "创建时间", "description": "创建时间"},
        {"name": "更新时间", "description": "更新时间"}
    ]

    return success_response(data=fields, message="获取可导出字段成功").dict()


# ============ 完整JSON导出 ============

def _product_to_full_dict(product: Product) -> dict:
    """将Product ORM对象序列化为完整JSON字典（可用于恢复导入）"""
    return {
        "product_uuid": product.product_uuid,
        "name": product.name,
        "short_name": product.short_name,
        "category": product.category,
        "sub_category": product.sub_category,
        "origin_province": product.origin_province,
        "origin_city": product.origin_city,
        "origin_district": product.origin_district,
        "origin_detail": product.origin_detail,
        "latitude": float(product.latitude) if product.latitude else None,
        "longitude": float(product.longitude) if product.longitude else None,
        "description": product.description,
        "features": product.features,
        "specifications": product.specifications,
        "nutrition_facts": product.nutrition_facts,
        "price": float(product.price) if product.price else 0,
        "certification_type": product.certification_type,
        "certification_no": product.certification_no,
        "certification_date": str(product.certification_date) if product.certification_date else None,
        "certification_expires": str(product.certification_expires) if product.certification_expires else None,
        "cultural_tags": product.cultural_tags,
        "cultural_story": product.cultural_story,
        "historical_origin": product.historical_origin,
        "main_image_url": product.main_image_url,
        "image_urls": product.image_urls,
        "original_image_urls": product.original_image_urls,
        "video_url": product.video_url,
        "status": product.status.value if hasattr(product.status, 'value') else str(product.status),
        "view_count": product.view_count or 0,
        "generate_count": product.generate_count or 0,
        "enterprise_id": product.enterprise_id,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


@router.get("/products/json", tags=["导出"])
async def export_products_json(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出产品完整数据为JSON文件（含所有字段，可用于恢复导入）"""
    import json

    try:
        products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
        if not products:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(code=ErrorCode.RECORD_NOT_FOUND, message="没有可导出的产品数据").dict()
            )

        export_data = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "total_count": len(products),
            "products": [_product_to_full_dict(p) for p in products],
        }

        json_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"products_backup_{timestamp}.json"

        return StreamingResponse(
            iter([json_bytes]),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": _encode_filename_header(filename)},
        )
    except Exception as e:
        logger.error(f"JSON导出异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(code=ErrorCode.SYSTEM_ERROR, message="JSON导出失败").dict()
        )


# ============ ZIP完整备份 ============

@router.get("/products/backup", tags=["导出"])
async def export_products_backup(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """导出产品完整备份包（JSON + Excel + 本地图片），ZIP格式"""
    import json
    import zipfile
    from pathlib import Path

    try:
        products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
        if not products:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(code=ErrorCode.RECORD_NOT_FOUND, message="没有可导出的产品数据").dict()
            )

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. products.json
            export_data = {
                "version": "1.0",
                "export_time": datetime.now().isoformat(),
                "total_count": len(products),
                "products": [_product_to_full_dict(p) for p in products],
            }
            zf.writestr("products.json", json.dumps(export_data, ensure_ascii=False, indent=2))

            # 2. products.xlsx
            data = [_build_product_dict(p) for p in products]
            df = pd.DataFrame(data)
            excel_buf = io.BytesIO()
            df.to_excel(excel_buf, index=False, sheet_name="产品列表")
            zf.writestr("products.xlsx", excel_buf.getvalue())

            # 3. images/ folder — collect local image files
            image_count = 0
            for p in products:
                for url in (p.image_urls or []):
                    if url and url.startswith("/uploads/"):
                        filepath = Path(url.lstrip("/"))
                        if filepath.exists():
                            zf.write(filepath, f"images/{filepath.name}")
                            image_count += 1
                if p.main_image_url and p.main_image_url.startswith("/uploads/"):
                    main_path = Path(p.main_image_url.lstrip("/"))
                    if main_path.exists() and f"images/{main_path.name}" not in zf.namelist():
                        zf.write(main_path, f"images/{main_path.name}")
                        image_count += 1

            # 4. manifest
            manifest = {
                "products": len(products),
                "images": image_count,
                "exported_at": datetime.now().isoformat(),
            }
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"products_backup_{timestamp}.zip"

        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": _encode_filename_header(filename)},
        )
    except Exception as e:
        logger.error(f"ZIP备份异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(code=ErrorCode.SYSTEM_ERROR, message="备份失败").dict()
        )


# ============ JSON导入/恢复 ============

@router.post("/products/import-json", tags=["导入"])
async def import_products_from_json(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """从JSON备份文件恢复产品数据（管理员操作）

    - 按 product_uuid 去重
    - 导入状态统一设为 DRAFT
    - 不覆盖已存在的产品
    """
    import json
    from app.models.product import ProductStatus

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))

        products_data = data.get("products", [])
        if not products_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(code=ErrorCode.PARAM_ERROR, message="JSON文件中没有产品数据").dict()
            )

        from app.models.user import User
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response(code=ErrorCode.FORBIDDEN, message="用户不存在").dict()
            )

        imported = skipped = errors_count = 0

        for item in products_data:
            try:
                p_uuid = item.get("product_uuid")
                if p_uuid:
                    existing = db.query(Product).filter(Product.product_uuid == p_uuid).first()
                    if existing:
                        skipped += 1
                        continue

                product = Product(
                    name=item.get("name", "未知产品")[:200],
                    category=item.get("category", "其他")[:100],
                    sub_category=item.get("sub_category"),
                    origin_province=item.get("origin_province", "未知")[:50],
                    origin_city=item.get("origin_city"),
                    origin_district=item.get("origin_district"),
                    origin_detail=item.get("origin_detail"),
                    description=item.get("description"),
                    features=item.get("features"),
                    specifications=item.get("specifications"),
                    nutrition_facts=item.get("nutrition_facts"),
                    price=item.get("price", 0),
                    certification_type=item.get("certification_type"),
                    certification_no=item.get("certification_no"),
                    cultural_tags=item.get("cultural_tags"),
                    cultural_story=item.get("cultural_story"),
                    historical_origin=item.get("historical_origin"),
                    main_image_url=item.get("main_image_url"),
                    image_urls=item.get("image_urls"),
                    original_image_urls=item.get("original_image_urls"),
                    video_url=item.get("video_url"),
                    status=ProductStatus.DRAFT,
                    created_by=user.id,
                )
                db.add(product)
                imported += 1
            except Exception as e:
                logger.warning(f"导入单条产品失败: {e}")
                errors_count += 1

        db.commit()

        return success_response(
            data={"imported": imported, "skipped": skipped, "errors": errors_count},
            message=f"导入完成: 新增{imported}, 跳过{skipped}, 失败{errors_count}"
        ).dict()

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(code=ErrorCode.PARAM_ERROR, message="无效的JSON文件").dict()
        )
    except Exception as e:
        logger.error(f"JSON导入异常: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(code=ErrorCode.SYSTEM_ERROR, message="导入失败").dict()
        )
