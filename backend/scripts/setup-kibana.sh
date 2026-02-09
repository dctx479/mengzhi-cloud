#!/bin/bash
# Kibana自动配置脚本
# 配置索引模式和仪表盘

echo "🔧 开始配置Kibana..."

# 等待Kibana启动
echo "等待Kibana启动..."
until curl -s http://localhost:5601/api/status | grep -q "green"; do
    echo "Kibana还未就绪，等待10秒..."
    sleep 10
done

echo "✅ Kibana已就绪"

# 创建索引模式
echo "创建索引模式: ai-platform-*..."
curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/ai-platform-*" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "title": "ai-platform-*",
      "timeFieldName": "@timestamp"
    }
  }'

echo ""
echo "✅ 索引模式创建成功"

# 设置默认索引模式
echo "设置默认索引模式..."
curl -X POST "http://localhost:5601/api/kibana/settings/defaultIndex" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '"ai-platform-*"'

echo ""
echo "✅ 默认索引模式设置成功"

echo "🎉 Kibana配置完成！"
echo "访问 http://localhost:5601 查看日志"
