"""
SQLAlchemy数据模型导入测试

用于验证所有模型是否正确生成和可以导入。

版本: 1.0
日期: 2026-01-17
"""

# 测试脚本 - 在项目根目录运行: python test_models.py

def test_imports():
    """测试所有模型导入"""
    try:
        print("测试模型导入...")

        # 基类
        from app.models.base import BaseModel, generate_uuid
        print("✓ BaseModel导入成功")

        # 用户模型
        from app.models.user import User, UserType, UserStatus, UserRole, Gender
        print("✓ User模型导入成功")

        # 企业模型
        from app.models.enterprise import Enterprise, EnterpriseScale, VerifyStatus, PlanType
        print("✓ Enterprise模型导入成功")

        # 产品模型
        from app.models.product import Product, ProductStatus
        print("✓ Product模型导入成功")

        # 对话模型
        from app.models.conversation import Conversation, AgentType, ConversationStatus
        print("✓ Conversation模型导入成功")

        # 消息模型
        from app.models.message import Message, MessageRole, ContentType
        print("✓ Message模型导入成功")

        # 内容记录模型
        from app.models.content_record import ContentRecord, Platform, Style, LengthType, RecordStatus
        print("✓ ContentRecord模型导入成功")

        # 配额模型
        from app.models.user_quota import UserQuota, QuotaType
        print("✓ UserQuota模型导入成功")

        # 模板模型
        from app.models.generation_template import GenerationTemplate, TemplateContentType, TemplatePlatform
        print("✓ GenerationTemplate模型导入成功")

        print("\n✓ 所有模型导入测试通过！")
        return True

    except ImportError as e:
        print(f"✗ 导入失败: {str(e)}")
        return False


def test_model_attributes():
    """测试模型属性"""
    try:
        print("\n测试模型属性...")

        from app.models import User, Product, Conversation

        # 检查User模型
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == 'users'
        print("✓ User.__tablename__ = 'users'")

        # 检查Product模型
        assert hasattr(Product, '__tablename__')
        assert Product.__tablename__ == 'products'
        print("✓ Product.__tablename__ = 'products'")

        # 检查Conversation模型
        assert hasattr(Conversation, '__tablename__')
        assert Conversation.__tablename__ == 'ai_conversations'
        print("✓ Conversation.__tablename__ = 'ai_conversations'")

        print("\n✓ 所有模型属性测试通过！")
        return True

    except AssertionError as e:
        print(f"✗ 属性检查失败: {str(e)}")
        return False


def test_database_connection():
    """测试数据库连接"""
    try:
        print("\n测试数据库连接...")

        from app.core.database import check_db_connection

        # 测试连接
        if check_db_connection():
            print("✓ 数据库连接成功")
            return True
        else:
            print("✗ 数据库连接失败")
            return False

    except Exception as e:
        print(f"✗ 连接测试异常: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SQLAlchemy 数据模型测试")
    print("=" * 60)

    # 运行测试
    results = []
    results.append(("模型导入", test_imports()))
    results.append(("模型属性", test_model_attributes()))

    # 数据库连接测试（如果配置了DATABASE_URL）
    try:
        results.append(("数据库连接", test_database_connection()))
    except Exception:
        print("\n跳过数据库连接测试（未配置或数据库不可用）")

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    for test_name, result in results:
        status = "通过" if result else "失败"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("✓ 所有测试通过！模型生成成功。")
    else:
        print("✗ 部分测试失败，请检查上面的错误信息。")
    print("=" * 60)
