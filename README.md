<img width="3020" height="1536" alt="d8d18af3-5cfd-464e-aee9-1d2f39a52ab7" src="https://github.com/user-attachments/assets/38b76803-888f-4c48-b565-8a525c93309e" />


# OCR & AI 提示词工具

集多格式文件 OCR 内容提取与 AI 提示词生成于一体的 Web 应用。

## 技术栈

- **前端**：Vue 3 + Vite + TypeScript + Ant-Design-Vue
- **后端**：Python FastAPI + RapidOCR + LibreOffice

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 可选：配置 Claude API Key 以启用 AI 增强提示词生成
export ANTHROPIC_API_KEY=your_key_here

docker-compose up --build
```

访问 http://localhost

### 方式二：本地开发

**后端**

```bash
cd backend

# 安装系统依赖（macOS）
brew install poppler libreoffice

# 安装 Python 依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 填入 ANTHROPIC_API_KEY

# 启动
python run.py
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 功能说明

### OCR 内容提取

- 支持文件类型：JPG、PNG、BMP、TIFF、PDF、DOCX、XLSX、PPTX
- 拖拽或点击上传，实时显示进度
- 文本内容以 Label+Text 形式展示，表格内容以 DataGrid 形式展示
- 支持一键复制、导出 TXT/JSON

### 提示词生成

- 支持类型：通用问答、代码生成、文档总结、数据分析、翻译
- 配置 `ANTHROPIC_API_KEY` 后使用 Claude AI 生成高质量提示词
- 未配置时使用本地规则模板生成
- 支持一键复制和验证提示词效果

## 接口文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger 文档。

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # 路由层
│   │   ├── core/         # 配置
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务逻辑
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # 公共组件
│   │   ├── views/        # 页面
│   │   ├── router/       # 路由
│   │   ├── types/        # TypeScript 类型
│   │   └── utils/        # 工具函数
│   └── Dockerfile
└── docker-compose.yml
```
