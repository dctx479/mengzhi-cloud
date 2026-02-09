"""
多模态素材管理系统 - 使用示例

演示如何使用媒体上传和管理API

版本: 1.0
更新日期: 2026-01-17
"""

import requests
from pathlib import Path


# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 认证Token（需要先登录获取）
# 实际使用中，应该通过 /api/v1/auth/login 获取
AUTH_TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}


def upload_image_example():
    """示例1: 上传产品图片"""
    print("=" * 50)
    print("示例1: 上传产品图片")
    print("=" * 50)

    # 准备图片文件
    image_path = "path/to/your/product.jpg"

    if not Path(image_path).exists():
        print(f"警告: 图片文件不存在: {image_path}")
        print("请修改 image_path 为实际的图片路径")
        return

    # 准备上传数据
    files = {
        "file": open(image_path, "rb")
    }
    data = {
        "category": "product",
        "title": "蒙古羊肉产品图",
        "description": "内蒙古优质草原羊肉",
        "alt_text": "蒙古羊肉"
    }

    # 发送上传请求
    response = requests.post(
        f"{BASE_URL}/media/upload/image",
        files=files,
        data=data,
        headers=headers
    )

    # 处理响应
    if response.status_code == 201:
        result = response.json()
        print("✓ 图片上传成功！")
        print(f"  - 媒体ID: {result['data']['id']}")
        print(f"  - 文件URL: {result['data']['file_url']}")
        print(f"  - 缩略图URL: {result['data']['thumbnail_url']}")
        print(f"  - 尺寸: {result['data']['width']}x{result['data']['height']}")
        print(f"  - 大小: {result['data']['file_size'] / 1024:.2f} KB")
        return result['data']
    else:
        print(f"✗ 上传失败: {response.status_code}")
        print(f"  错误信息: {response.json()}")
        return None


def list_media_example():
    """示例2: 获取媒体列表"""
    print("\n" + "=" * 50)
    print("示例2: 获取媒体列表")
    print("=" * 50)

    # 查询参数
    params = {
        "media_type": "image",
        "category": "product",
        "page": 1,
        "page_size": 10
    }

    response = requests.get(
        f"{BASE_URL}/media/",
        params=params,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ 查询成功！共 {result['total']} 条记录")
        print(f"  当前页: {result['page']}/{(result['total'] + result['page_size'] - 1) // result['page_size']}")

        for i, media in enumerate(result['items'], 1):
            print(f"\n  [{i}] {media['filename']}")
            print(f"      ID: {media['id']}")
            print(f"      URL: {media['file_url']}")
            print(f"      尺寸: {media.get('width', 'N/A')}x{media.get('height', 'N/A')}")
            print(f"      创建时间: {media['created_at']}")

        return result['items']
    else:
        print(f"✗ 查询失败: {response.status_code}")
        return []


def get_media_detail_example(media_id):
    """示例3: 获取媒体详情"""
    print("\n" + "=" * 50)
    print(f"示例3: 获取媒体详情 (ID: {media_id})")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/media/{media_id}",
        headers=headers
    )

    if response.status_code == 200:
        media = response.json()
        print("✓ 获取成功！")
        print(f"  标题: {media.get('title', '未设置')}")
        print(f"  描述: {media.get('description', '未设置')}")
        print(f"  分类: {media['category']}")
        print(f"  类型: {media['media_type']}")
        print(f"  文件名: {media['filename']}")
        print(f"  URL: {media['file_url']}")
        print(f"  大小: {media['file_size'] / 1024:.2f} KB")
        return media
    else:
        print(f"✗ 获取失败: {response.status_code}")
        return None


def update_media_example(media_id):
    """示例4: 更新媒体信息"""
    print("\n" + "=" * 50)
    print(f"示例4: 更新媒体信息 (ID: {media_id})")
    print("=" * 50)

    update_data = {
        "title": "更新后的标题",
        "description": "这是更新后的描述信息",
        "alt_text": "更新后的alt文本",
        "is_public": True
    }

    response = requests.put(
        f"{BASE_URL}/media/{media_id}",
        json=update_data,
        headers=headers
    )

    if response.status_code == 200:
        media = response.json()
        print("✓ 更新成功！")
        print(f"  新标题: {media['title']}")
        print(f"  新描述: {media['description']}")
        return media
    else:
        print(f"✗ 更新失败: {response.status_code}")
        return None


def assign_to_product_example(media_id, product_id):
    """示例5: 关联媒体到产品"""
    print("\n" + "=" * 50)
    print(f"示例5: 关联媒体到产品 (媒体ID: {media_id}, 产品ID: {product_id})")
    print("=" * 50)

    response = requests.post(
        f"{BASE_URL}/media/{media_id}/assign-product/{product_id}",
        headers=headers
    )

    if response.status_code == 200:
        media = response.json()
        print("✓ 关联成功！")
        print(f"  产品ID: {media['product_id']}")
        return media
    else:
        print(f"✗ 关联失败: {response.status_code}")
        return None


def get_stats_example():
    """示例6: 获取媒体统计"""
    print("\n" + "=" * 50)
    print("示例6: 获取媒体统计")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/media/stats",
        headers=headers
    )

    if response.status_code == 200:
        stats = response.json()
        print("✓ 统计数据：")
        print(f"  总媒体数: {stats['total_count']}")
        print(f"  总大小: {stats['total_size'] / (1024 * 1024):.2f} MB")
        print(f"  图片数: {stats['image_count']}")
        print(f"  视频数: {stats['video_count']}")
        print("\n  按分类统计:")
        for category, count in stats['by_category'].items():
            print(f"    - {category}: {count}")
        return stats
    else:
        print(f"✗ 获取统计失败: {response.status_code}")
        return None


def delete_media_example(media_id):
    """示例7: 删除媒体"""
    print("\n" + "=" * 50)
    print(f"示例7: 删除媒体 (ID: {media_id})")
    print("=" * 50)

    # 确认删除
    confirm = input(f"确定要删除媒体 {media_id} 吗？(yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消删除")
        return False

    response = requests.delete(
        f"{BASE_URL}/media/{media_id}",
        headers=headers
    )

    if response.status_code == 204:
        print("✓ 删除成功！")
        return True
    else:
        print(f"✗ 删除失败: {response.status_code}")
        return False


def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 50)
    print("多模态素材管理系统 - 使用示例")
    print("=" * 50)

    # 检查认证
    if AUTH_TOKEN == "your_access_token_here":
        print("\n⚠ 警告: 请先设置有效的 AUTH_TOKEN")
        print("   1. 登录系统获取token")
        print("   2. 修改脚本中的 AUTH_TOKEN 变量")
        return

    # 示例1: 上传图片
    # media = upload_image_example()

    # 示例2: 获取媒体列表
    media_list = list_media_example()

    # 如果有媒体，演示其他操作
    if media_list:
        first_media_id = media_list[0]['id']

        # 示例3: 获取详情
        get_media_detail_example(first_media_id)

        # 示例4: 更新信息（可选）
        # update_media_example(first_media_id)

        # 示例5: 关联产品（可选，需要有产品ID）
        # assign_to_product_example(first_media_id, product_id=1)

    # 示例6: 获取统计
    get_stats_example()

    # 示例7: 删除媒体（可选）
    # delete_media_example(first_media_id)

    print("\n" + "=" * 50)
    print("示例演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
