# MarkItDown Setup

Microsoft MarkItDown currently requires Python 3.10 or newer.

## Recommended isolated install

Create a dedicated virtual environment with a Python 3.10+ interpreter that already exists on the machine:

```bash
python3.11 -m venv ~/.venvs/markitdown
~/.venvs/markitdown/bin/pip install --upgrade pip
~/.venvs/markitdown/bin/pip install "markitdown[all]" openai markitdown-ocr
```

Verify the install:

```bash
~/.venvs/markitdown/bin/markitdown --help
~/.venvs/markitdown/bin/python -c "import markitdown, openai, markitdown_ocr"
```

Use that install through the wrapper:

```bash
python3 scripts/run_markitdown.py /absolute/path/file.pdf
```

The wrapper auto-detects `~/.venvs/markitdown/bin/python`. If you need a non-default install, point at the runtime explicitly:

```bash
MARKITDOWN_PYTHON=~/.venvs/markitdown/bin/python python3 scripts/run_markitdown.py /absolute/path/file.pdf
```

Enable VLM + OCR with OpenAI-compatible settings:

```bash
OPENAI_API_KEY=... \
MARKITDOWN_LLM_MODEL=gpt-4o \
MARKITDOWN_ENABLE_OCR=1 \
python3 scripts/run_markitdown.py /absolute/path/file.pdf
```

Enable Azure OpenAI:

```bash
MARKITDOWN_LLM_PROVIDER=azure-openai \
AZURE_OPENAI_API_KEY=... \
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
AZURE_OPENAI_API_VERSION=2024-10-21 \
MARKITDOWN_LLM_MODEL=gpt-4o \
python3 scripts/run_markitdown.py /absolute/path/file.pdf
```

## Direct CLI examples

```bash
markitdown /absolute/path/file.pdf > /absolute/path/file.md
markitdown /absolute/path/file.docx -o /absolute/path/file.md
```

## Environment variables

- `MARKITDOWN_PYTHON`: force a specific runtime interpreter
- `MARKITDOWN_LLM_PROVIDER`: `auto`, `none`, `openai`, or `azure-openai`
- `MARKITDOWN_LLM_MODEL`: vision-capable model or Azure deployment name
- `MARKITDOWN_LLM_PROMPT`: override the image description / OCR prompt
- `MARKITDOWN_ENABLE_PLUGINS`: load installed MarkItDown plugins
- `MARKITDOWN_ENABLE_OCR`: convenience alias that implies plugins
- `OPENAI_API_KEY`: API key for OpenAI-compatible providers
- `OPENAI_BASE_URL`: optional OpenAI-compatible API base URL
- `AZURE_OPENAI_API_KEY`: Azure OpenAI key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_VERSION` or `OPENAI_API_VERSION`: Azure OpenAI API version

## If no Python 3.10+ interpreter exists yet

Install one first with your preferred toolchain, then install MarkItDown into an isolated environment. The wrapper will report the missing prerequisite clearly when it cannot find a suitable runtime.
