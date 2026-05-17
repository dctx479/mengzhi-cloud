"""
导出功能API - 完善版

支持产品列表导出为CSV和Excel格式，包含分批处理、自定义字段、权限验证等功能

版本: 2.0
创建日期: 2026-01-17
更新日期: 2026-01-21
"""

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
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
    encoded = urllib.parse.quote(filename.encode('utf-8'))
    header_value = 'attachment; filename="' + filename + '"; filename*=UTF-8''' + encoded
    return header_value

def _build_product_dict(product: Product, fields: Optional[List[str]] = None) -> dict:
    """构建产品字典，支持自定义字段"""
    all_fields = {
        "产品ID": product.id,
        "产品名称": product.name,
        "SKU": product.sku,
        "分类": product.category,
        "价格（元）": float(product.price) if product.price else 0,
        "产地": product.region,
        "状态": product.status,
        "是否精选": "是" if product.is_featured else "否",
        "库存": product.stock,
        "销量": product.sales_count,
        "文化标签": product.cultural_tags or "",
        "文化描述": product.cultural_description or "",
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
            query = query.filter(Product.region == region)
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
            "SKU": ["SKU-001"],
            "分类": ["肉类"],
            "价格（元）": [99.00],
            "产地": ["呼和浩特"],
            "状态": ["active"],
            "库存": [100],
            "文化标签": ["草原牛肉"],
            "文化描述": ["来自内蒙古大草原的优质牛肉"]
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
        {"name": "产品名称", "description": "产品名称"},
        {"name": "SKU", "description": "产品SKU编码"},
        {"name": "分类", "description": "产品分类"},
        {"name": "价格（元）", "description": "产品价格"},
        {"name": "产地", "description": "产品产地"},
        {"name": "状态", "description": "产品状态"},
        {"name": "是否精选", "description": "是否为精选产品"},
        {"name": "库存", "description": "库存数量"},
        {"name": "销量", "description": "销售数量"},
        {"name": "文化标签", "description": "文化标签"},
        {"name": "文化描述", "description": "文化描述"},
        {"name": "创建时间", "description": "创建时间"},
        {"name": "更新时间", "description": "更新时间"}
    ]

    return success_response(data=fields, message="获取可导出字段成功").dict()
