# Spec: 债券跟踪系统 (Bond Market Tracker)

## Objective
将现有的 Excel 债券跟踪工作流转换为现代化的 Web 应用。实现国债收益率、利差、基差的实时监控、历史分位数分析，并集成 DeepSeek V4 AI 辅助决策。

### 用户故事
- 交易员可以查看实时国债收益率曲线。
- 风险控制人员可以监控利差是否突破历史分位数阈值。
- 分析师可以通过 AI 生成每日债市简评。

## Tech Stack
- **Backend**: Python 3.10+, FastAPI, SQLite, SQLAlchemy (ORM), LangChain (AI Orchestration).
- **Frontend**: Vue 3 (Vite), Tailwind CSS, ECharts (Data Visualization).
- **AI**: DeepSeek V4 API.
- **Data Source**: 同花顺 (iTHS) HTTP 接口。

## Commands
- **Backend Dev**: `uvicorn app.main:app --reload`
- **Frontend Dev**: `npm run dev`
- **Install Deps**: `pip install -r requirements.txt && npm install`

## Project Structure
```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 配置、日志、安全
│   ├── models/       # 数据库模型 (SQLAlchemy)
│   ├── services/     # 业务逻辑 (iTHS 接口、AI 逻辑)
│   └── main.py       # 入口
├── data/             # SQLite 数据库文件
├── requirements.txt
└── .env              # 密钥、API 地址
frontend/
├── src/
│   ├── api/          # Axios 请求
│   ├── components/   # 可复用组件
│   ├── views/        # 页面 (Dashboard, AI Chat)
│   ├── store/        # Pinia 状态管理
│   └── App.vue
├── tailwind.config.js
└── package.json
```

## Code Style
- **Python**: PEP 8, 类型注解 (Type Hints), 异步 (Async/Await).
- **Vue**: Composition API (Script Setup), 语义化 HTML.

## Testing Strategy
- **Backend**: Pytest (单元测试), HTTPX (集成测试).
- **Frontend**: Vitest.

## AI Integration (DeepSeek V4)
- **智能分析**: 对比当前利差与历史分位数，给出异常预警。
- **自然语言查询**: 用户输入“帮我看看 10Y-7Y 利差在过去一年的位置”，系统生成图表和文字解释。
- **日报生成**: 自动抓取数据并生成市场报告。

## Boundaries
- **Always**: 处理 API 异常，保留数据更新日志，使用环境变量管理密钥。
- **Ask first**: 修改数据库 Schema，引入大型前端库。
- **Never**: 将 API 密钥提交到 Git，在主线程执行耗时计算。

## Success Criteria
- [ ] 成功从 Excel 导入历史数据到 SQLite。
- [ ] 后端能通过 iTHS 接口获取最新数据并入库。
- [ ] 前端展示收益率曲线和分位数热力图。
- [ ] AI 能正确回答简单的债市数据查询。
