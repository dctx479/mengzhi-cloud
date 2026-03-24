# 前端Dockerfile - 多阶段构建

# ============ 构建阶段 ============
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci && \
    npm cache clean --force

# 复制源代码
COPY . .

# 设置构建时环境变量 - Docker 环境中 nginx 反代 /api → backend:8000
ENV VITE_API_BASE_URL=/api

# 构建应用
RUN npm run build

# ============ 生产阶段 ============
FROM nginx:alpine

# 复制自定义nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查 (alpine wget 不支持 --spider, 用 -qO /dev/null)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO /dev/null http://127.0.0.1/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
