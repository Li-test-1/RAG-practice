# RAG-ljy 企业知识库问答系统

基于 LangChain + LanceDB 的 RAG 问答系统，支持混合检索（BM25 + 向量检索）、可选重排序、以及大模型回答，提供 CLI 和 Web 两种交互方式。

## 项目架构

```
RAG-ljy/
├── config.py                  # 全局配置（dataclass）
├── main.py                    # CLI 命令行入口（click）
├── requirements.txt           # Python 依赖
├── run_api.py                 # FastAPI 服务启动入口
├── api/                       # FastAPI 后端
│   ├── app.py                 # FastAPI 应用实例 + CORS
│   ├── routes.py              # API 路由
│   └── state.py               # 全局状态管理（config + pipeline 单例）
├── src/                       # 核心业务逻辑
│   ├── pdf_converter.py       # MinerU PDF → Markdown 转换
│   ├── text_splitter.py       # Markdown 两阶段切分
│   ├── embedding.py           # Embedding 模型工厂
│   ├── vector_store.py        # LanceDB 向量存储
│   ├── bm25_store.py          # BM25 索引（jieba 分词）
│   ├── retriever.py           # 混合检索器（RRF 融合）
│   ├── reranker.py            # 重排序模块
│   ├── generator.py           # LLM 生成器
│   ├── pipeline.py            # Pipeline 主流程编排
│   └── prompts.py             # Prompt 模板
├── data/
│   ├── pdf/                   # 原始 PDF 文件
│   ├── markdown/              # 转换后的 MD 文件（运行后生成）
│   ├── lancedb/               # 向量数据库（运行后生成）
│   └── bm25/                  # BM25 索引（运行后生成）
└── web/                       # Vue 3 前端
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue
        ├── main.js
        ├── api/index.js           # API 调用封装
        └── components/
            ├── ConfigPanel.vue    # 配置面板
            ├── QueryPanel.vue     # 查询面板
            └── ResultPanel.vue    # 结果展示面板
```

## RAG 流程

```
PDF → Markdown(MinerU) → 切分(标题+递归) → 双路索引(LanceDB+BM25)
                                              ↓
                              查询 → 混合检索(RRF融合) → Rerank → LLM生成
```

## 模型配置

### Embedding 模型（3 选 1）

| 模型 | 维度 | 调用方式 |
|------|------|---------|
| `bge-large-zh` | 1024 | HuggingFace 本地 |
| `text-embedding-3-small` | 1536 | OpenAI API |
| `text-embedding-v3`（默认） | 1024 | DashScope API |

### Rerank 模型（4 选 1）

| 模型 | 调用方式 |
|------|---------|
| `bge-reranker-v2-m3` | HuggingFace 本地 |
| `jina-reranker-v2` | Jina API |
| `gte-rerank` | DashScope API |
| `qwen3-rerank`（默认） | DashScope API |

### LLM

默认使用 `qwen-plus`，通过 DashScope OpenAI 兼容接口调用。

## 环境配置

### 1. 安装 Python 依赖

```bash
cd RAG-ljy
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd web
npm install
```

### 3. 配置 API Key

在 `RAG-ljy/` 目录下创建 `.env` 文件：

```
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
JINA_API_KEY=your_jina_api_key
MINERU_API_KEY=your_mineru_api_key
```

> 使用默认配置（DashScope Embedding + DashScope Rerank + qwen-plus LLM）只需配置 `DASHSCOPE_API_KEY`。

## 使用方式

### CLI 命令行

```bash
# 一键构建索引（PDF转换 → 切分 → 建库）
python main.py index-all

# 分步执行
python main.py convert       # PDF → Markdown
python main.py chunk         # Markdown 切分
python main.py build-index   # 构建向量索引 + BM25 索引

# 单次查询
python main.py ask -q "中芯国际2024年营收是多少？"

# 交互式问答
python main.py interactive
```

### Web 界面

```bash
# 启动后端（端口 8000）
python run_api.py

# 启动前端（端口 5173，自动代理 API 到 8000）
cd web && npm run dev
```

浏览器访问 `http://localhost:5173`，左侧配置参数，右侧输入问题查询。

### API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/config` | 获取当前配置 + 可选项 |
| POST | `/api/config` | 更新配置（动态生效） |
| POST | `/api/query` | 问答查询 |
| GET | `/api/tags` | 获取标签列表 |

**查询示例**：

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "中芯国际的营收情况", "top_k": 5}'
```

## 关键设计

- **混合检索**：向量检索（LanceDB）+ 稀疏检索（BM25/jieba），通过 RRF（Reciprocal Rank Fusion）算法融合排序
- **两阶段切分**：先按 Markdown 标题层级（H1/H2/H3）切分，再按字符数递归切分（chunk_size=500, overlap=50）
- **权限标签**：从文件名自动提取标签（financial_report / research_report / research_memo / earnings_review / general），支持按标签过滤检索
- **动态配置**：Web 端支持运行时修改所有参数（Embedding 模型、Rerank 开关、检索参数、LLM 参数等），无需重启服务
- **完整溯源**：查询结果包含引用片段的完整文本、RRF 分数、Rerank 分数，以及完整的 System/User Prompt

## 依赖

```
langchain>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0
langchain-core>=0.3.0
langchain-text-splitters>=0.3.0
lancedb>=0.15.0
sentence-transformers>=3.0.0
rank-bm25>=0.2.2
jieba>=0.42.1
python-dotenv>=1.0.0
openai>=1.50.0
dashscope>=1.20.0
pydantic>=2.0.0
requests>=2.32.0
tqdm>=4.66.0
pypdf>=4.0.0
fastapi>=0.100.0
uvicorn>=0.20.0
```
