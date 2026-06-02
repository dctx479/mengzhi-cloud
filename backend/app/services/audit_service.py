"""
审计日志服务 - BUG-028修复

负责记录和查询操作日志

版本: 1.0
创建日期: 2026-01-17
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
from datetime import datetime

from app.models.audit_log import AuditLog
from app.core.logging_config import logger


def _safe_json_loads(data, default=None):
    """安全地解析JSON字符串，解析失败时返回默认值而非抛出异常。

    参数:
        data: 待解析的JSON字符串
        default: 解析失败时的返回值，默认为None

    返回:
        解析后的Python对象，或default
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"JSON解析失败: {str(e)}, data={repr(data)[:200]}")
        return default


class AuditService:
    """审计日志服务"""

    @staticmethod
    def log(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: str = "unknown",
        resource: str = "unknown",
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        before_data: Optional[Dict[str, Any]] = None,
        after_data: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status_code: Optional[int] = 200,
        is_success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """记录操作日志

        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            action: 操作类型（create/update/delete/login/logout等）
            resource: 资源类型（product/user/enterprise等）
            resource_id: 资源ID
            details: 操作详情
            changes: 变更内容（字典）
            before_data: 操作前数据（字典）
            after_data: 操作后数据（字典）
            ip: IP地址
            user_agent: User-Agent
            request_method: HTTP方法
            request_path: 请求路径
            status_code: 响应状态码
            is_success: 是否成功
            error_message: 错误消息

        返回:
            创建的审计日志对象
        """
        try:
            # 序列化changes为JSON字符串
            changes_json = None
            if changes:
                try:
                    changes_json = json.dumps(changes, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"序列化changes失败: {str(e)}")
                    changes_json = str(changes)

            # 序列化before_data为JSON字符串
            before_data_json = None
            if before_data:
                try:
                    before_data_json = json.dumps(before_data, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"序列化before_data失败: {str(e)}")
                    before_data_json = str(before_data)

            # 序列化after_data为JSON字符串
            after_data_json = None
            if after_data:
                try:
                    after_data_json = json.dumps(after_data, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"序列化after_data失败: {str(e)}")
                    after_data_json = str(after_data)

            # 创建日志记录
            log_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource=resource,
                resource_id=resource_id,
                details=details,
                changes=changes_json,
                before_data=before_data_json,
                after_data=after_data_json,
                ip_address=ip,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status_code=status_code,
                is_success=1 if is_success else 0,
                error_message=error_message
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.debug(
                f"审计日志记录成功: user={username}, action={action}, "
                f"resource={resource}, id={resource_id}"
            )

            return log_entry

        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
            db.rollback()
            # 不抛出异常，避免影响主业务流程
            return None

    @staticmethod
    def log_create(
        db: Session,
        user_id: int,
        username: str,
        resource: str,
        resource_id: int,
        details: str,
        ip: Optional[str] = None
    ) -> AuditLog:
        """记录创建操作
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            resource: 资源类型
            resource_id: 资源ID
            details: 操作详情
            ip: IP地址
            
        返回:
            审计日志对象
        """
        return AuditService.log(
            db=db,
            user_id=user_id,
            username=username,
            action="create",
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip=ip,
            status_code=201
        )

    @staticmethod
    def log_update(
        db: Session,
        user_id: int,
        username: str,
        resource: str,
        resource_id: int,
        details: str,
        changes: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None
    ) -> AuditLog:
        """记录更新操作
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            resource: 资源类型
            resource_id: 资源ID
            details: 操作详情
            changes: 变更内容
            ip: IP地址
            
        返回:
            审计日志对象
        """
        return AuditService.log(
            db=db,
            user_id=user_id,
            username=username,
            action="update",
            resource=resource,
            resource_id=resource_id,
            details=details,
            changes=changes,
            ip=ip,
            status_code=200
        )

    @staticmethod
    def log_delete(
        db: Session,
        user_id: int,
        username: str,
        resource: str,
        resource_id: int,
        details: str,
        ip: Optional[str] = None
    ) -> AuditLog:
        """记录删除操作
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            resource: 资源类型
            resource_id: 资源ID
            details: 操作详情
            ip: IP地址
            
        返回:
            审计日志对象
        """
        return AuditService.log(
            db=db,
            user_id=user_id,
            username=username,
            action="delete",
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip=ip,
            status_code=200
        )

    @staticmethod
    def log_login(
        db: Session,
        user_id: int,
        username: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """记录登录操作
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            ip: IP地址
            user_agent: User-Agent
            is_success: 是否成功
            error_message: 错误消息
            
        返回:
            审计日志对象
        """
        return AuditService.log(
            db=db,
            user_id=user_id,
            username=username,
            action="login",
            resource="auth",
            details=f"用户{username}登录{'成功' if is_success else '失败'}",
            ip=ip,
            user_agent=user_agent,
            is_success=is_success,
            error_message=error_message
        )

    @staticmethod
    def log_logout(
        db: Session,
        user_id: int,
        username: str,
        ip: Optional[str] = None
    ) -> AuditLog:
        """记录登出操作

        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            ip: IP地址

        返回:
            审计日志对象
        """
        return AuditService.log(
            db=db,
            user_id=user_id,
            username=username,
            action="logout",
            resource="auth",
            details=f"用户{username}登出",
            ip=ip
        )

    @staticmethod
    def query_logs(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[int] = None,
        is_success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """查询审计日志

        参数:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名（模糊搜索）
            action: 操作类型
            resource: 资源类型
            resource_id: 资源ID
            is_success: 是否成功
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页数量

        返回:
            包含日志列表和分页信息的字典
        """
        try:
            # 构建查询
            query = db.query(AuditLog)

            # 应用过滤条件
            if user_id is not None:
                query = query.filter(AuditLog.user_id == user_id)

            if username:
                safe_username = username.replace("%", "\\%").replace("_", "\\_")
                query = query.filter(AuditLog.username.like(f"%{safe_username}%", escape="\\"))

            if action:
                query = query.filter(AuditLog.action == action)

            if resource:
                query = query.filter(AuditLog.resource == resource)

            if resource_id is not None:
                query = query.filter(AuditLog.resource_id == resource_id)

            if is_success is not None:
                query = query.filter(AuditLog.is_success == (1 if is_success else 0))

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            # 获取总数
            total = query.count()

            # 分页
            offset = (page - 1) * page_size
            logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

            # 转换为字典
            log_list = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "changes": _safe_json_loads(log.changes) if log.changes else None,
                    "before_data": _safe_json_loads(log.before_data) if log.before_data else None,
                    "after_data": _safe_json_loads(log.after_data) if log.after_data else None,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "request_method": log.request_method,
                    "request_path": log.request_path,
                    "status_code": log.status_code,
                    "is_success": bool(log.is_success),
                    "error_message": log.error_message,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                log_list.append(log_dict)

            return {
                "logs": log_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

        except Exception as e:
            logger.error(f"查询审计日志失败: {str(e)}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }

    @staticmethod
    def get_log_by_id(db: Session, log_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取审计日志详情

        参数:
            db: 数据库会话
            log_id: 日志ID

        返回:
            日志详情字典或None
        """
        try:
            log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

            if not log:
                return None

            return {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "details": log.details,
                "changes": _safe_json_loads(log.changes) if log.changes else None,
                "before_data": _safe_json_loads(log.before_data) if log.before_data else None,
                "after_data": _safe_json_loads(log.after_data) if log.after_data else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "status_code": log.status_code,
                "is_success": bool(log.is_success),
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }

        except Exception as e:
            logger.error(f"获取审计日志详情失败: {str(e)}")
            return None

    @staticmethod
    def get_statistics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取审计日志统计信息

        参数:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        返回:
            统计信息字典
        """
        try:
            from sqlalchemy import func

            # 构建基础查询
            query = db.query(AuditLog)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            # 总操作数
            total_operations = query.count()

            # 成功/失败统计 — 基于独立的 filter，避免复用同一 query 对象叠加条件
            base_query = db.query(AuditLog)
            if start_date:
                base_query = base_query.filter(AuditLog.created_at >= start_date)
            if end_date:
                base_query = base_query.filter(AuditLog.created_at <= end_date)

            success_count = base_query.filter(AuditLog.is_success == 1).count()
            failure_count = base_query.filter(AuditLog.is_success == 0).count()

            # 按操作类型统计
            action_query = db.query(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            if start_date:
                action_query = action_query.filter(AuditLog.created_at >= start_date)
            if end_date:
                action_query = action_query.filter(AuditLog.created_at <= end_date)
            action_stats = action_query.group_by(AuditLog.action).all()

            # 按资源类型统计
            resource_query = db.query(
                AuditLog.resource,
                func.count(AuditLog.id).label('count')
            )
            if start_date:
                resource_query = resource_query.filter(AuditLog.created_at >= start_date)
            if end_date:
                resource_query = resource_query.filter(AuditLog.created_at <= end_date)
            resource_stats = resource_query.group_by(AuditLog.resource).all()

            # 活跃用户统计
            active_query = db.query(
                AuditLog.username,
                func.count(AuditLog.id).label('count')
            ).filter(AuditLog.username.isnot(None))
            if start_date:
                active_query = active_query.filter(AuditLog.created_at >= start_date)
            if end_date:
                active_query = active_query.filter(AuditLog.created_at <= end_date)
            active_users = active_query.group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()

            # 按日期分组的操作趋势
            from sqlalchemy import cast, Date, case
            trend_base = db.query(
                cast(AuditLog.created_at, Date).label('date'),
                func.count(AuditLog.id).label('count'),
                func.sum(case((AuditLog.is_success == 1, 1), else_=0)).label('success_count'),
                func.sum(case((AuditLog.is_success == 0, 1), else_=0)).label('failure_count')
            )
            if start_date:
                trend_base = trend_base.filter(AuditLog.created_at >= start_date)
            if end_date:
                trend_base = trend_base.filter(AuditLog.created_at <= end_date)
            action_trend = trend_base.group_by(cast(AuditLog.created_at, Date)).order_by(cast(AuditLog.created_at, Date)).all()

            return {
                "total_operations": total_operations,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": round(success_count / total_operations * 100, 2) if total_operations > 0 else 0,
                "failure_rate": round(failure_count / total_operations * 100, 2) if total_operations > 0 else 0,
                "action_stats": [{"action": action, "count": count} for action, count in action_stats],
                "resource_stats": [{"resource": resource, "count": count} for resource, count in resource_stats],
                "active_users": [{"username": username, "count": count} for username, count in active_users],
                "action_trend": [
                    {
                        "date": str(row.date),
                        "count": row.count,
                        "success_count": int(row.success_count or 0),
                        "failure_count": int(row.failure_count or 0)
                    }
                    for row in action_trend
                ]
            }

        except Exception as e:
            logger.error(f"获取审计日志统计失败: {str(e)}")
            return {
                "total_operations": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "action_stats": [],
                "resource_stats": [],
                "active_users": [],
                "action_trend": []
            }

    @staticmethod
    def export_logs(
        db: Session,
        format: str = "json",
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """导出审计日志

        参数:
            db: 数据库会话
            format: 导出格式（json/csv）
            user_id: 用户ID
            action: 操作类型
            resource: 资源类型
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大导出数量

        返回:
            包含导出数据的字典
        """
        try:
            # 构建查询
            query = db.query(AuditLog)

            # 应用过滤条件
            if user_id is not None:
                query = query.filter(AuditLog.user_id == user_id)

            if action:
                query = query.filter(AuditLog.action == action)

            if resource:
                query = query.filter(AuditLog.resource == resource)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            # 分批加载，避免大数据量时 OOM（每批 1000 条）
            BATCH = 1000
            log_list = []
            fetched = 0
            while fetched < limit:
                batch_size = min(BATCH, limit - fetched)
                batch = query.order_by(AuditLog.created_at.desc()).offset(fetched).limit(batch_size).all()
                if not batch:
                    break
                for log in batch:
                    log_dict = {
                        "id": log.id,
                        "user_id": log.user_id,
                        "username": log.username,
                        "action": log.action,
                        "resource": log.resource,
                        "resource_id": log.resource_id,
                        "details": log.details,
                        "changes": _safe_json_loads(log.changes) if log.changes else None,
                        "before_data": _safe_json_loads(log.before_data) if log.before_data else None,
                        "after_data": _safe_json_loads(log.after_data) if log.after_data else None,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "request_method": log.request_method,
                        "request_path": log.request_path,
                        "status_code": log.status_code,
                        "is_success": bool(log.is_success),
                        "error_message": log.error_message,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    log_list.append(log_dict)
                fetched += len(batch)

            if format == "csv":
                # 转换为CSV格式
                import csv
                import io

                output = io.StringIO()
                if log_list:
                    writer = csv.DictWriter(output, fieldnames=log_list[0].keys())
                    writer.writeheader()
                    writer.writerows(log_list)

                return {
                    "format": "csv",
                    "data": output.getvalue(),
                    "count": len(log_list)
                }
            else:
                # JSON格式
                return {
                    "format": "json",
                    "data": log_list,
                    "count": len(log_list)
                }

        except Exception as e:
            logger.error(f"导出审计日志失败: {str(e)}")
            return {
                "format": format,
                "data": [] if format == "json" else "",
                "count": 0,
                "error": "导出失败"
            }
