"""
P2修复验证脚本

用于快速验证P2 Bug修复是否完成

运行: python verify_p2_fixes.py
"""

import os
import sys

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (缺失)")
        return False

def check_directory_exists(dirpath, description):
    """检查目录是否存在"""
    if os.path.isdir(dirpath):
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description}: {dirpath} (缺失)")
        return False

def main():
    print("=" * 60)
    print("P2修复验证脚本")
    print("=" * 60)
    
    results = []
    
    # 检查新增服务层文件
    print("\n[1] 检查新增服务层文件...")
    results.append(check_file_exists("app/services/file_service.py", "文件上传服务"))
    results.append(check_file_exists("app/services/notification_service.py", "邮件/短信服务"))
    results.append(check_file_exists("app/services/audit_service.py", "审计日志服务"))
    
    # 检查新增API文件
    print("\n[2] 检查新增API文件...")
    results.append(check_file_exists("app/api/users.py", "用户API"))
    results.append(check_file_exists("app/api/exports.py", "导出API"))
    
    # 检查新增模型文件
    print("\n[3] 检查新增模型文件...")
    results.append(check_file_exists("app/models/audit_log.py", "审计日志模型"))
    
    # 检查数据库迁移文件
    print("\n[4] 检查数据库迁移文件...")
    results.append(check_file_exists("alembic/versions/002_add_audit_logs.py", "数据库迁移"))
    
    # 检查上传目录
    print("\n[5] 检查上传目录...")
    results.append(check_directory_exists("uploads", "上传根目录"))
    results.append(check_directory_exists("uploads/avatars", "头像上传目录"))
    results.append(check_directory_exists("uploads/products", "产品图片目录"))
    
    # 检查修改的文件
    print("\n[6] 检查关键修改...")
    
    # 检查config.py是否包含SMTP配置
    try:
        with open("app/core/config.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "SMTP_SERVER" in content and "SMTP_PORT" in content:
                print("✓ config.py包含SMTP配置")
                results.append(True)
            else:
                print("✗ config.py缺少SMTP配置")
                results.append(False)
    except:
        print("✗ 无法读取config.py")
        results.append(False)
    
    # 检查constants.py是否包含上传路径
    try:
        with open("app/core/constants.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "AVATAR_UPLOAD_DIR" in content and "PRODUCT_IMAGE_UPLOAD_DIR" in content:
                print("✓ constants.py包含上传路径常量")
                results.append(True)
            else:
                print("✗ constants.py缺少上传路径常量")
                results.append(False)
    except:
        print("✗ 无法读取constants.py")
        results.append(False)
    
    # 检查product_service.py是否包含joinedload
    try:
        with open("app/services/product_service.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "joinedload" in content and "MATCH" in content:
                print("✓ product_service.py包含N+1优化和全文搜索")
                results.append(True)
            else:
                print("✗ product_service.py缺少优化")
                results.append(False)
    except:
        print("✗ 无法读取product_service.py")
        results.append(False)
    
    # 检查products.py是否包含批量操作
    try:
        with open("app/api/products.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "batch-delete" in content and "batch-update" in content:
                print("✓ products.py包含批量操作API")
                results.append(True)
            else:
                print("✗ products.py缺少批量操作API")
                results.append(False)
    except:
        print("✗ 无法读取products.py")
        results.append(False)
    
    # 检查main.py是否注册新路由
    try:
        with open("app/main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "users" in content and "exports" in content:
                print("✓ main.py已注册新路由")
                results.append(True)
            else:
                print("✗ main.py缺少新路由注册")
                results.append(False)
    except:
        print("✗ 无法读取main.py")
        results.append(False)
    
    # 统计结果
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"验证结果: {passed}/{total} 通过 ({percentage:.1f}%)")
    if failed > 0:
        print(f"失败项: {failed}")
        print("\n请检查上述标记为 ✗ 的项目")
        sys.exit(1)
    else:
        print("\n✓ 所有检查通过！P2修复完成。")
        sys.exit(0)

if __name__ == "__main__":
    main()
