# Bond Market Dashboard (Bond Hub)

这是一个基于 FastAPI 和 Vue 3 开发的债券市场监控面板。

## 技术栈
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, Pandas
- **Frontend**: Vue 3, Vite, Tailwind CSS, ECharts

## 部署指南 (使用 PM2)

### 1. 克隆项目
```bash
git clone https://github.com/chievan/bond_mkt.git
cd bond_mkt
```

### 2. 后端配置
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# 配置 .env 文件 (DEEPSEEK_API_KEY, ITHS_API_KEY 等)
cp .env.example .env # 如果有的话
cd ..
```

### 3. 前端配置与构建
```bash
cd frontend
npm install
# 构建生产环境代码
npm run build
cd ..
```

### 4. 使用 PM2 启动
项目包含 `ecosystem.config.js`，可一键启动前后端：

```bash
# 确保已安装 pm2: npm install -g pm2
pm2 start ecosystem.config.js
```

- **前端访问端口**: `8503`
- **后端 API 端口**: `8000`

### 5. 常用命令
- 查看状态: `pm2 list`
- 查看日志: `pm2 logs`
- 重启服务: `pm2 restart bond-hub`
- 停止服务: `pm2 stop all`

## 注意事项
- 请确保服务器防火墙开放了 **8503** 和 **8000** 端口。
- 前端 API 地址在 `frontend/src/App.vue` 中配置，默认为 `localhost:8000`。若远程访问，请在构建前修改环境变量 `VITE_API_BASE_URL`。
