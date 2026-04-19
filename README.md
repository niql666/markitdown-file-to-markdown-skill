# MarkItDown File To Markdown Skill

[中文说明](README.zh-CN.md)

Codex skill and wrapper script for converting local files to Markdown with [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

This repository packages the skill definition, setup notes, and a Python wrapper that adds:

- automatic runtime detection for Python environments that already have `markitdown`
- recursive directory conversion with preserved relative paths
- optional OCR / VLM support through OpenAI-compatible or Azure OpenAI clients
- batch conversion options such as `--skip-errors` and per-file timeouts

## Repository Layout

```text
markitdown-file-to-markdown-skill/
├── SKILL.md
├── README.md
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

## What It Supports

- PDF, Word, Excel, PowerPoint
- HTML, CSV, JSON, XML, EPUB, ZIP
- image files such as JPG, JPEG, PNG
- optional OCR and image description with a vision-capable model

The exact supported file types still depend on the installed MarkItDown build and plugins.

## Install

Create an isolated Python environment and install dependencies:

```bash
python3.11 -m venv ~/.venvs/markitdown
~/.venvs/markitdown/bin/pip install --upgrade pip
~/.venvs/markitdown/bin/pip install "markitdown[all]" openai markitdown-ocr
```

Verify:

```bash
~/.venvs/markitdown/bin/markitdown --help
~/.venvs/markitdown/bin/python -c "import markitdown, openai, markitdown_ocr"
```

## Use As A Codex Skill

Copy or symlink this directory into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
ln -s /absolute/path/to/markitdown-file-to-markdown-skill ~/.codex/skills/markitdown-file-to-markdown
```

Or copy it directly:

```bash
cp -R /absolute/path/to/markitdown-file-to-markdown-skill ~/.codex/skills/markitdown-file-to-markdown
```

## Wrapper Examples

Single file:

```bash
python3 scripts/run_markitdown.py /absolute/path/input.pdf
```

Single file with explicit output:

```bash
python3 scripts/run_markitdown.py /absolute/path/input.docx --output /absolute/path/output.md
```

Recursive conversion with preserved structure:

```bash
python3 scripts/run_markitdown.py /absolute/path/in-dir --recursive --output-dir /absolute/path/out-dir
```

Recursive conversion with explicit filters:

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

Enable OCR with an OpenAI-compatible endpoint:

```bash
OPENAI_API_KEY=your_key_here \
MARKITDOWN_LLM_MODEL=gpt-4o \
MARKITDOWN_ENABLE_OCR=1 \
python3 scripts/run_markitdown.py /absolute/path/scanned.pdf
```

Use a compatible base URL:

```bash
OPENAI_API_KEY=placeholder \
OPENAI_BASE_URL=http://localhost:8000/v1 \
MARKITDOWN_LLM_MODEL=my-vision-model \
python3 scripts/run_markitdown.py /absolute/path/slides.pptx --use-plugins
```

Use Azure OpenAI:

```bash
MARKITDOWN_LLM_PROVIDER=azure-openai \
AZURE_OPENAI_API_KEY=your_key_here \
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
AZURE_OPENAI_API_VERSION=2024-10-21 \
MARKITDOWN_LLM_MODEL=gpt-4o \
python3 scripts/run_markitdown.py /absolute/path/file.pdf --enable-ocr
```

## Environment Variables

See [.env.example](.env.example) and [references/setup.md](references/setup.md).

Main variables:

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

## VLM API Key Configuration

The wrapper supports vision-capable LLMs through either an OpenAI-compatible API or Azure OpenAI.

### OpenAI-compatible providers

Set these variables:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://your-provider.example/v1
MARKITDOWN_LLM_MODEL=your-vision-model
MARKITDOWN_ENABLE_OCR=1
```

Then run:

```bash
python3 scripts/run_markitdown.py /absolute/path/file.pdf --enable-ocr
```

### OpenRouter example

```bash
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MARKITDOWN_LLM_MODEL=your-vision-model
MARKITDOWN_ENABLE_OCR=1
python3 scripts/run_markitdown.py /absolute/path/file.pdf --enable-ocr
```

Important:

- the selected model must support image input
- free models may hit aggressive rate limits during image-heavy batch runs
- if your endpoint ignores auth, `OPENAI_API_KEY` still needs a non-empty placeholder value

### Azure OpenAI

```bash
MARKITDOWN_LLM_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-21
MARKITDOWN_LLM_MODEL=your_deployment_name
MARKITDOWN_ENABLE_OCR=1
python3 scripts/run_markitdown.py /absolute/path/file.pdf --enable-ocr
```

### Optional provider selection

You can also set the provider explicitly:

```bash
MARKITDOWN_LLM_PROVIDER=openai
```

or:

```bash
MARKITDOWN_LLM_PROVIDER=azure-openai
```

## Publishing To GitHub

```bash
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Notes

- This repository does not include real API keys or personal shell configuration.
- Free OpenAI-compatible vision endpoints may rate limit heavily when converting image-heavy batches.
- Large PPT/PDF conversions can be slow; use `--skip-errors` and `--timeout-seconds` for long directory runs.

## License

MIT
