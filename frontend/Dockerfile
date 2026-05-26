# ============================================================
# 阶段 1: 构建 Vue 前端
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# ============================================================
# 阶段 2: Nginx 托管前端 + 反向代理 API
# ============================================================
FROM nginx:alpine

# 覆盖默认 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制前端构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
