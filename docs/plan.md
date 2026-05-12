# Implementation Plan: Bond Market Tracker

## Phase 1: Backend Foundation (Target: Data Availability)
- [ ] 1.1 初始化后端项目结构 (`backend/app/`)
- [ ] 1.2 编写 `requirements.txt` 并安装依赖
- [ ] 1.3 定义 SQLAlchemy 模型 (`models/bond.py`)
- [ ] 1.4 编写数据导入脚本，将 Excel 数据迁移至 SQLite
- [ ] 1.5 实现基础 FastAPI 接口（获取收益率列表、分位数数据）

## Phase 2: Frontend Foundation (Target: Data Visualization)
- [ ] 2.1 初始化 Vue 3 + Vite 项目
- [ ] 2.2 配置 Tailwind CSS 和基础 UI 库
- [ ] 2.3 集成 ECharts，实现收益率曲线图和历史利差图
- [ ] 2.4 实现分位数热力图组件

## Phase 3: Data & AI Integration (Target: Intelligence)
- [ ] 3.1 实现同花顺 iTHS HTTP 接口客户端
- [ ] 3.2 配置 LangChain + DeepSeek V4 环境
- [ ] 3.3 开发 AI 助手接口：支持自然语言查询债市数据
- [ ] 3.4 实现 AI 异常分析逻辑（例如：当 10Y-2Y 倒挂时触发 AI 评论）

## Phase 4: Polish (Target: Premium UX)
- [ ] 4.1 优化 UI 审美（深色模式、玻璃拟态）
- [ ] 4.2 添加页面转场动画和数据加载微动效
- [ ] 4.3 最终联调与部署验证
