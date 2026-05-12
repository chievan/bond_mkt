#!/bin/bash

# 确保在项目根目录
cd /opt/bond_mkt

echo "🚀 开始一键部署更新..."

# 1. 拉取最新代码
echo "📥 正在拉取代码..."
git pull https://ghfast.top/https://github.com/chievan/bond_mkt.git main

# 2. 更新后端依赖
echo "📦 正在更新后端依赖..."
cd backend
./venv/bin/pip install -r requirements.txt
cd ..

# 3. 编译前端
echo "🏗️ 正在编译前端..."
cd frontend
npm install
npm run build
cd ..

# 4. 重启 PM2 项目
echo "♻️ 正在重启 PM2 服务..."
pm2 start ecosystem.config.js || pm2 restart ecosystem.config.js

echo "✅ 部署完成！"
pm2 list
