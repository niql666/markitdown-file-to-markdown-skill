---
name: markitdown-file-to-markdown
description: Convert local files to Markdown using Microsoft MarkItDown, with optional VLM image description and OCR plugins. Trigger when a user asks to turn PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, XML, EPUB, ZIP, images, audio, or similar files into Markdown.
---

# MarkItDown File To Markdown

Use this skill when the user wants Markdown extracted from local files and wants the conversion performed with Microsoft MarkItDown. This skill can also attach a vision-capable LLM client for image description and the `markitdown-ocr` plugin.

## Required flow

1. Confirm the local input path or paths and the desired output location.
2. Run `scripts/run_markitdown.py` from this skill instead of invoking `markitdown` directly.
3. If the wrapper reports that `markitdown` is unavailable, follow `references/setup.md` to install a Python 3.10+ environment with `markitdown[all]`.
4. If the user wants image understanding or OCR from embedded images, configure a VLM client and enable plugins.
5. Write the generated Markdown to a `.md` file unless the user explicitly wants stdout only.
6. Verify that the output file exists and spot-check the first section for obvious conversion failures.

## Wrapper usage

Single file:

```bash
python3 scripts/run_markitdown.py /absolute/path/input.pdf
```

Single file with explicit output:

```bash
python3 scripts/run_markitdown.py /absolute/path/input.docx --output /absolute/path/output.md
```

Multiple files:

```bash
python3 scripts/run_markitdown.py /a/report.pdf /a/slides.pptx --output-dir /absolute/path/out
```

Recursive directory conversion with preserved subdirectories:

```bash
python3 scripts/run_markitdown.py /absolute/path/in-dir --recursive --output-dir /absolute/path/out-dir
```

Recursive directory conversion with explicit extension filters:

```bash
python3 scripts/run_markitdown.py /absolute/path/in-dir --recursive --include-ext .pdf --include-ext .docx --include-ext .pptx --output-dir /absolute/path/out-dir
```

Recursive conversion that skips unsupported or corrupt files:

```bash
python3 scripts/run_markitdown.py /absolute/path/in-dir --recursive --include-ext .pdf --include-ext .docx --include-ext .pptx --output-dir /absolute/path/out-dir --skip-errors
```

Keep embedded image data URIs:

```bash
python3 scripts/run_markitdown.py /absolute/path/input.html --keep-data-uris
```

Enable OCR plugins with an OpenAI-compatible model:

```bash
OPENAI_API_KEY=... \
MARKITDOWN_LLM_MODEL=gpt-4o \
python3 scripts/run_markitdown.py /absolute/path/scanned.pdf --enable-ocr
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
AZURE_OPENAI_API_KEY=... \
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
AZURE_OPENAI_API_VERSION=2024-10-21 \
MARKITDOWN_LLM_MODEL=gpt-4o \
python3 scripts/run_markitdown.py /absolute/path/doc-with-images.docx --enable-ocr
```

## Notes

- The wrapper re-executes itself under a Python runtime that has `markitdown` installed.
- The wrapper automatically detects the default install at `~/.venvs/markitdown/bin/python`.
- `MARKITDOWN_PYTHON` can point to a Python 3.10+ interpreter that already has `markitdown` installed.
- When several inputs are provided, use `--output-dir` or let the wrapper write each `.md` file next to its source file.
- Directory inputs require `--output-dir`. Their relative subdirectory structure is recreated under that output directory.
- Directory traversal defaults to a common set of supported extensions. Use `--include-ext` to narrow or expand that set.
- Do not assume the local system `python3` is sufficient. MarkItDown currently requires Python 3.10+.
- Use `--enable-ocr` or `MARKITDOWN_ENABLE_OCR=1` to load `markitdown-ocr`.
- VLM provider selection can be explicit with `--llm-provider`, or automatic from the available environment variables.
- Supported environment variables: `MARKITDOWN_LLM_PROVIDER`, `MARKITDOWN_LLM_MODEL`, `MARKITDOWN_LLM_PROMPT`, `MARKITDOWN_ENABLE_PLUGINS`, `MARKITDOWN_ENABLE_OCR`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, and `OPENAI_API_VERSION`.

## References

- `references/setup.md` - install and verification steps for MarkItDown.
