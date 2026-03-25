# "五行知己" Demo

## Intro

基于 `FastApi` + `LangChain` + `chromadb` 的中医AI-Agent

## Usage

### 后端

1. 进入 `backend` 目录，安装依赖：

```bash
pipenv install
```

2. 配置 `.env` 文件，参考 `.env.example`

3. 启动后端：

```bash
pipenv run main.py
```

### 前端

1. 进入 `demo_frontend` 目录，安装依赖：

```bash
npm install .
```

2. 启动前端：

```bash
npm run dev
```

3. 打开浏览器访问 `http://localhost:5173`

## More

如果要更新向量库，参见 [``这里``](./backend/rag/README.md)