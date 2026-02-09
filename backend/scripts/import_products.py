#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内蒙古农畜产品数据导入脚本

功能：
- 从JSON文件读取产品数据
- 验证数据完整性和格式
- 导入到数据库
- 生成导入报告

用法：
    python import_products.py --batch 1,2,3 --env development
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductDataImporter:
    """产品数据导入器"""

    def __init__(self, data_dir: str = "data"):
        """初始化导入器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.products_dir = self.data_dir / "products"
        self.cultural_dir = self.data_dir / "cultural"
        self.marketing_dir = self.data_dir / "marketing"

        self.stats = {
            "total_products": 0,
            "valid_products": 0,
            "invalid_products": 0,
            "validation_errors": [],
            "import_errors": []
        }

    def load_json_file(self, file_path: Path) -> Dict:
        """加载JSON文件

        Args:
            file_path: 文件路径

        Returns:
            JSON数据字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载文件: {file_path}")
            return data
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {file_path}, 错误信息: {str(e)}")
            return None

    def validate_product(self, product: Dict) -> Tuple[bool, str]:
        """验证产品数据

        Args:
            product: 产品数据字典

        Returns:
            (是否有效, 错误信息)
        """
        # 检查必需字段
        required_fields = ['id', 'name', 'category', 'region', 'description']
        for field in required_fields:
            if field not in product:
                return False, f"缺少必需字段: {field}"

        # 检查字段类型和长度
        if not isinstance(product['name'], str) or len(product['name']) == 0:
            return False, "产品名称不能为空"

        if not isinstance(product['category'], str) or len(product['category']) == 0:
            return False, "产品分类不能为空"

        if not isinstance(product['description'], str) or len(product['description']) < 50:
            return False, "产品描述需要至少50个字符"

        # 检查特征、认证等数组字段
        if 'characteristics' in product:
            if not isinstance(product['characteristics'], list) or len(product['characteristics']) == 0:
                return False, "产品特征应为非空数组"

        if 'certifications' in product:
            if not isinstance(product['certifications'], list) or len(product['certifications']) == 0:
                return False, "认证信息应为非空数组"

        return True, ""

    def validate_batch(self, batch_data: Dict) -> bool:
        """验证批次数据

        Args:
            batch_data: 批次数据

        Returns:
            是否通过验证
        """
        if 'products' not in batch_data:
            logger.error("批次数据缺少'products'字段")
            return False

        products = batch_data['products']
        if not isinstance(products, list):
            logger.error("'products'字段应为数组")
            return False

        logger.info(f"批次: {batch_data.get('batch', 'unknown')}, 产品数: {len(products)}")

        self.stats['total_products'] += len(products)

        for product in products:
            is_valid, error_msg = self.validate_product(product)
            if is_valid:
                self.stats['valid_products'] += 1
            else:
                self.stats['invalid_products'] += 1
                self.stats['validation_errors'].append({
                    'product_id': product.get('id', 'unknown'),
                    'product_name': product.get('name', 'unknown'),
                    'error': error_msg
                })
                logger.warning(f"产品验证失败: {product.get('name', 'unknown')} - {error_msg}")

        return self.stats['invalid_products'] == 0

    def load_all_batches(self) -> List[Dict]:
        """加载所有产品批次

        Returns:
            批次数据列表
        """
        batches = []

        # 查找所有batch*.json文件
        batch_files = sorted(self.products_dir.glob("batch*.json"))

        for batch_file in batch_files:
            logger.info(f"加载批次文件: {batch_file}")
            data = self.load_json_file(batch_file)
            if data:
                if self.validate_batch(data):
                    batches.append(data)
                else:
                    logger.warning(f"批次 {batch_file} 验证失败，但继续加载")
                    batches.append(data)

        return batches

    def load_cultural_data(self) -> Dict:
        """加载文化元素数据"""
        cultural_file = self.cultural_dir / "cultural_elements.json"
        return self.load_json_file(cultural_file)

    def load_marketing_data(self) -> Dict:
        """加载营销素材数据"""
        marketing_file = self.marketing_dir / "marketing_materials.json"
        return self.load_json_file(marketing_file)

    def generate_import_report(self) -> str:
        """生成导入报告

        Returns:
            报告文本
        """
        report = []
        report.append("=" * 60)
        report.append("内蒙古农畜产品数据导入报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 统计信息
        report.append("## 数据统计")
        report.append(f"- 总产品数: {self.stats['total_products']}")
        report.append(f"- 有效产品: {self.stats['valid_products']}")
        report.append(f"- 无效产品: {self.stats['invalid_products']}")
        report.append(f"- 有效率: {self.stats['valid_products']/max(1, self.stats['total_products'])*100:.1f}%")
        report.append("")

        # 验证错误
        if self.stats['validation_errors']:
            report.append("## 验证错误详情")
            for error in self.stats['validation_errors']:
                report.append(f"- 产品ID: {error['product_id']}, 名称: {error['product_name']}")
                report.append(f"  错误: {error['error']}")
            report.append("")

        # 导入建议
        report.append("## 导入建议")
        if self.stats['invalid_products'] > 0:
            report.append("- 发现无效数据，建议修复后重新导入")
            report.append("- 检查缺少的字段和格式错误")
        else:
            report.append("- 数据验证通过，可以安全导入数据库")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def run(self):
        """执行导入流程"""
        logger.info("开始导入内蒙古农畜产品数据...")

        # 加载所有批次
        batches = self.load_all_batches()
        logger.info(f"加载了 {len(batches)} 个批次")

        # 加载文化数据
        cultural_data = self.load_cultural_data()
        if cultural_data:
            logger.info(f"加载了 {len(cultural_data.get('elements', []))} 个文化元素")

        # 加载营销数据
        marketing_data = self.load_marketing_data()
        if marketing_data:
            logger.info(f"加载了 {len(marketing_data.get('materials', []))} 个营销素材")

        # 生成报告
        report = self.generate_import_report()
        print(report)

        # 保存报告
        report_file = self.data_dir / "IMPORT_REPORT.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"导入报告已保存到: {report_file}")

        return self.stats['invalid_products'] == 0


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='内蒙古农畜产品数据导入脚本')
    parser.add_argument('--data-dir', default='data', help='数据目录路径')
    parser.add_argument('--env', default='development', help='环境: development/production')
    parser.add_argument('--batch', default='1,2,3', help='要导入的批次')

    args = parser.parse_args()

    importer = ProductDataImporter(data_dir=args.data_dir)
    success = importer.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
