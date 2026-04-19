# MarkItDown 文件转 Markdown 技能

这是一个基于 [Microsoft MarkItDown](https://github.com/microsoft/markitdown) 的 Codex 技能与包装脚本，用来把本地文件批量转换成 Markdown。

仓库里包含三部分核心内容：

- `SKILL.md`：Codex 技能定义
- `scripts/run_markitdown.py`：增强版包装脚本
- `references/setup.md`：安装与配置说明

这个包装脚本在原始 `markitdown` 能力之外，还补充了：

- 自动寻找已安装 `markitdown` 的 Python 运行时
- 递归处理目录，并保持相对目录结构
- 支持批量转换、跳过错误、单文件超时
- 可选接入 OCR 和 VLM
- 支持 OpenAI 兼容接口和 Azure OpenAI

## 目录结构

```text
markitdown-file-to-markdown-skill/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── .gitignore
├── .env.example
├── agents/
│   └── openai.example.yaml
├── references/
│   └── setup.md
└── scripts/
    └── run_markitdown.py
```

## 支持的能力

- PDF、Word、Excel、PowerPoint
- HTML、CSV、JSON、XML、EPUB、ZIP
- JPG、JPEG、PNG 等图片文件
- 可选 OCR 和图片描述

实际可转换格式仍取决于本地安装的 MarkItDown 版本与插件。

## 安装

建议使用独立 Python 虚拟环境：

```bash
python3.11 -m venv ~/.venvs/markitdown
~/.venvs/markitdown/bin/pip install --upgrade pip
~/.venvs/markitdown/bin/pip install "markitdown[all]" openai markitdown-ocr
```

验证安装：

```bash
~/.venvs/markitdown/bin/markitdown --help
~/.venvs/markitdown/bin/python -c "import markitdown, openai, markitdown_ocr"
```

## 作为 Codex 技能使用

把仓库复制或软链接到 `~/.codex/skills`：

```bash
mkdir -p ~/.codex/skills
ln -s /absolute/path/to/markitdown-file-to-markdown-skill ~/.codex/skills/markitdown-file-to-markdown
```

或者直接复制：

```bash
cp -R /absolute/path/to/markitdown-file-to-markdown-skill ~/.codex/skills/markitdown-file-to-markdown
```

## 用法示例

单文件转换：

```bash
python3 scripts/run_markitdown.py /absolute/path/input.pdf
```

指定输出文件：

```bash
python3 scripts/run_markitdown.py /absolute/path/input.docx --output /absolute/path/output.md
```

递归处理目录并保持结构：

```bash
python3 scripts/run_markitdown.py /absolute/path/in-dir --recursive --output-dir /absolute/path/out-dir
```

按扩展名过滤并跳过错误：

```bash
python3 scripts/run_markitdown.py \
  /absolute/path/in-dir \
  --recursive \
  --include-ext .pdf \
  --include-ext .docx \
  --include-ext .pptx \
  --output-dir /absolute/path/out-dir \
  --skip-errors
```

启用 OCR：

```bash
OPENAI_API_KEY=your_key_here \
MARKITDOWN_LLM_MODEL=gpt-4o \
MARKITDOWN_ENABLE_OCR=1 \
python3 scripts/run_markitdown.py /absolute/path/scanned.pdf
```

使用 OpenAI 兼容接口：

```bash
OPENAI_API_KEY=placeholder \
OPENAI_BASE_URL=http://localhost:8000/v1 \
MARKITDOWN_LLM_MODEL=my-vision-model \
python3 scripts/run_markitdown.py /absolute/path/slides.pptx --use-plugins
```

使用 Azure OpenAI：

```bash
MARKITDOWN_LLM_PROVIDER=azure-openai \
AZURE_OPENAI_API_KEY=your_key_here \
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
AZURE_OPENAI_API_VERSION=2024-10-21 \
MARKITDOWN_LLM_MODEL=gpt-4o \
python3 scripts/run_markitdown.py /absolute/path/file.pdf --enable-ocr
```

## 环境变量

参考 [.env.example](.env.example) 和 [references/setup.md](references/setup.md)。

主要变量有：

- `MARKITDOWN_PYTHON`
- `MARKITDOWN_LLM_PROVIDER`
- `MARKITDOWN_LLM_MODEL`
- `MARKITDOWN_LLM_PROMPT`
- `MARKITDOWN_ENABLE_PLUGINS`
- `MARKITDOWN_ENABLE_OCR`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`

## 发布到 GitHub

```bash
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## 说明

- 仓库中不包含真实 API key 或个人 shell 配置
- 免费视觉模型在图片很多时很容易触发限流
- 大型 PPT / PDF 批处理时建议配合 `--skip-errors` 和 `--timeout-seconds`

## 许可证

MIT
