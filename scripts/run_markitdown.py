#!/usr/bin/env python3
"""Run Microsoft MarkItDown against one or more local files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
from typing import Any, Iterable, List, Optional, Sequence


PREFERRED_PYTHONS = (
    "python3.13",
    "python3.12",
    "python3.11",
    "python3.10",
)

DEFAULT_VENV_BIN = Path.home() / ".venvs" / "markitdown" / "bin" / "markitdown"
DEFAULT_VENV_PYTHON = Path.home() / ".venvs" / "markitdown" / "bin" / "python"
RUNTIME_ENV_FLAG = "MARKITDOWN_WRAPPER_RUNTIME"
DEFAULT_DIRECTORY_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".epub",
    ".htm",
    ".html",
    ".jpeg",
    ".jpg",
    ".json",
    ".msg",
    ".pdf",
    ".png",
    ".pptx",
    ".txt",
    ".xls",
    ".xlsx",
    ".xml",
    ".zip",
}


@dataclass(frozen=True)
class ConversionJob:
    input_path: Path
    relative_output: Path


class FileConversionTimeout(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert local files to Markdown using Microsoft MarkItDown."
    )
    parser.add_argument("inputs", nargs="+", help="Input file paths.")
    parser.add_argument(
        "--output",
        help="Explicit output Markdown path. Only valid with a single input.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to receive generated Markdown files.",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Continue processing other files when one input fails to convert.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        help="Abort a single file conversion if it runs longer than this many seconds.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When an input is a directory, walk subdirectories recursively.",
    )
    parser.add_argument(
        "--include-ext",
        action="append",
        default=[],
        help="Limit directory traversal to these file extensions. Repeat as needed, for example --include-ext .pdf --include-ext .docx.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print Markdown to stdout instead of writing files. Only valid with a single input.",
    )
    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="Keep full data URIs for embedded images instead of truncating them.",
    )
    parser.add_argument(
        "--use-plugins",
        action="store_true",
        help="Enable installed MarkItDown plugins.",
    )
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR-capable plugins. This implies --use-plugins.",
    )
    parser.add_argument(
        "--llm-provider",
        choices=("auto", "none", "openai", "azure-openai"),
        help="VLM client provider. Defaults to MARKITDOWN_LLM_PROVIDER or auto-detection.",
    )
    parser.add_argument(
        "--llm-model",
        help="Vision-capable model or deployment name used for image descriptions and OCR.",
    )
    parser.add_argument(
        "--llm-prompt",
        help="Optional custom prompt for image description or OCR extraction.",
    )
    parser.add_argument(
        "--openai-api-key",
        help="API key for OpenAI-compatible providers. Defaults to OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--openai-base-url",
        help="Optional base URL for OpenAI-compatible providers. Defaults to OPENAI_BASE_URL.",
    )
    parser.add_argument(
        "--azure-api-key",
        help="Azure OpenAI API key. Defaults to AZURE_OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--azure-endpoint",
        help="Azure OpenAI endpoint. Defaults to AZURE_OPENAI_ENDPOINT.",
    )
    parser.add_argument(
        "--azure-api-version",
        help="Azure OpenAI API version. Defaults to AZURE_OPENAI_API_VERSION or OPENAI_API_VERSION.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Compatibility passthrough for older wrapper usage. Supports --use-plugins, --keep-data-uris, --llm-model=..., and --llm-prompt=....",
    )
    return parser.parse_args()


def env_truthy(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_value(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def apply_compat_extra_args(args: argparse.Namespace) -> None:
    for value in args.extra_arg:
        if value == "--use-plugins":
            args.use_plugins = True
        elif value == "--keep-data-uris":
            args.keep_data_uris = True
        elif value.startswith("--llm-model=") and not args.llm_model:
            args.llm_model = value.split("=", 1)[1]
        elif value.startswith("--llm-prompt=") and not args.llm_prompt:
            args.llm_prompt = value.split("=", 1)[1]
        else:
            raise SystemExit(
                "Unsupported --extra-arg value: %s. Use the explicit wrapper flags instead."
                % value
            )


def file_to_markdown_name(input_path: Path) -> str:
    return input_path.stem + ".md"


def normalize_inputs(raw_inputs: Sequence[str]) -> List[Path]:
    inputs = [Path(item).expanduser().resolve() for item in raw_inputs]
    missing = [str(path) for path in inputs if not path.exists()]
    if missing:
        raise SystemExit("Input path does not exist: " + ", ".join(missing))
    return inputs


def normalize_extensions(values: Sequence[str]) -> set[str]:
    if not values:
        return set(DEFAULT_DIRECTORY_EXTENSIONS)

    normalized: set[str] = set()
    for value in values:
        ext = value.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        normalized.add(ext)
    if not normalized:
        raise SystemExit("--include-ext was provided but no valid extensions were found.")
    return normalized


def iter_directory_files(
    directory: Path,
    recursive: bool,
    allowed_extensions: set[str],
) -> Iterable[Path]:
    iterator = directory.rglob("*") if recursive else directory.glob("*")
    for path in iterator:
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_extensions:
            continue
        yield path


def build_jobs(inputs: Sequence[Path], args: argparse.Namespace) -> List[ConversionJob]:
    if args.output and len(inputs) != 1:
        raise SystemExit("--output only supports a single input path.")
    if args.stdout and len(inputs) != 1:
        raise SystemExit("--stdout only supports a single input path.")
    if args.stdout and args.output:
        raise SystemExit("--stdout cannot be combined with --output.")

    contains_directory = any(path.is_dir() for path in inputs)
    if contains_directory and args.stdout:
        raise SystemExit("--stdout cannot be used when any input is a directory.")
    if contains_directory and args.output:
        raise SystemExit("--output cannot be used when any input is a directory.")
    if contains_directory and not args.output_dir:
        raise SystemExit("--output-dir is required when any input is a directory.")

    allowed_extensions = normalize_extensions(args.include_ext)
    jobs: List[ConversionJob] = []

    for input_path in inputs:
        if input_path.is_file():
            jobs.append(
                ConversionJob(
                    input_path=input_path,
                    relative_output=Path(file_to_markdown_name(input_path)),
                )
            )
            continue

        matched = sorted(
            iter_directory_files(
                input_path,
                recursive=args.recursive,
                allowed_extensions=allowed_extensions,
            )
        )
        for file_path in matched:
            relative = file_path.relative_to(input_path).with_suffix(".md")
            jobs.append(ConversionJob(input_path=file_path, relative_output=relative))

    if not jobs:
        raise SystemExit("No input files matched the requested paths and extension filters.")

    return jobs


def resolve_output_path(job: ConversionJob, args: argparse.Namespace) -> Path:
    if args.output:
        return Path(args.output).expanduser().resolve()
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / job.relative_output
    return job.input_path.with_name(file_to_markdown_name(job.input_path))


def can_import_module(python_bin: str, module_name: str) -> bool:
    try:
        result = subprocess.run(
            [python_bin, "-c", "import %s" % module_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def find_markitdown_python() -> Optional[str]:
    env_python = os.environ.get("MARKITDOWN_PYTHON")
    if env_python:
        expanded = str(Path(env_python).expanduser())
        if Path(expanded).exists() and can_import_module(expanded, "markitdown"):
            return expanded
        raise SystemExit(
            "MARKITDOWN_PYTHON is set but does not provide an importable markitdown module: %s"
            % expanded
        )

    if DEFAULT_VENV_PYTHON.exists() and can_import_module(
        str(DEFAULT_VENV_PYTHON), "markitdown"
    ):
        return str(DEFAULT_VENV_PYTHON)

    if DEFAULT_VENV_BIN.exists():
        candidate = str(DEFAULT_VENV_BIN.parent / "python")
        if Path(candidate).exists() and can_import_module(candidate, "markitdown"):
            return candidate

    for candidate in PREFERRED_PYTHONS:
        python_bin = shutil.which(candidate)
        if python_bin and can_import_module(python_bin, "markitdown"):
            return python_bin

    discovered_python = shutil.which("python3")
    if discovered_python and can_import_module(discovered_python, "markitdown"):
        return discovered_python

    return None


def ensure_runtime_python() -> None:
    if os.environ.get(RUNTIME_ENV_FLAG) == "1":
        return

    if can_import_module(sys.executable, "markitdown"):
        return

    runtime_python = find_markitdown_python()
    if not runtime_python:
        raise SystemExit(
            "Microsoft MarkItDown is not available. Install Python 3.10+ and then install "
            "\"markitdown[all]\". For VLM and OCR support also install \"openai\" and "
            "\"markitdown-ocr\". See references/setup.md in this skill for the supported setup."
        )

    env = os.environ.copy()
    env[RUNTIME_ENV_FLAG] = "1"
    result = subprocess.run(
        [runtime_python, __file__, *sys.argv[1:]],
        env=env,
        check=False,
    )
    raise SystemExit(result.returncode)


def resolve_provider(args: argparse.Namespace) -> str:
    provider = args.llm_provider or env_value("MARKITDOWN_LLM_PROVIDER") or "auto"
    provider = provider.strip().lower()

    if provider == "auto":
        if env_value("AZURE_OPENAI_ENDPOINT") and env_value("AZURE_OPENAI_API_KEY"):
            return "azure-openai"
        if args.azure_endpoint and (args.azure_api_key or env_value("AZURE_OPENAI_API_KEY")):
            return "azure-openai"
        if args.openai_api_key or env_value("OPENAI_API_KEY"):
            return "openai"
        if args.openai_base_url and (args.openai_api_key or env_value("OPENAI_API_KEY")):
            return "openai"
        return "none"

    return provider


def build_llm_client(args: argparse.Namespace) -> tuple[Optional[Any], Optional[str], Optional[str]]:
    provider = resolve_provider(args)
    model = args.llm_model or env_value("MARKITDOWN_LLM_MODEL")
    prompt = args.llm_prompt or env_value("MARKITDOWN_LLM_PROMPT")

    if provider == "none":
        return None, model, prompt

    if not model:
        raise SystemExit(
            "A vision model is required when VLM is enabled. Set --llm-model or MARKITDOWN_LLM_MODEL."
        )

    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError as exc:
        raise SystemExit(
            "The openai package is required for VLM support. Install it in the MarkItDown runtime."
        ) from exc

    if provider == "openai":
        api_key = args.openai_api_key or env_value("OPENAI_API_KEY")
        base_url = args.openai_base_url or env_value("OPENAI_BASE_URL")
        if not api_key:
            raise SystemExit(
                "OPENAI_API_KEY is required for the OpenAI-compatible provider. "
                "If your endpoint ignores auth, set OPENAI_API_KEY to any non-empty placeholder."
            )
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs), model, prompt

    if provider == "azure-openai":
        api_key = args.azure_api_key or env_value("AZURE_OPENAI_API_KEY")
        endpoint = args.azure_endpoint or env_value("AZURE_OPENAI_ENDPOINT")
        api_version = args.azure_api_version or env_value(
            "AZURE_OPENAI_API_VERSION", "OPENAI_API_VERSION"
        )
        if not api_key:
            raise SystemExit(
                "AZURE_OPENAI_API_KEY is required for the Azure OpenAI provider."
            )
        if not endpoint:
            raise SystemExit(
                "AZURE_OPENAI_ENDPOINT is required for the Azure OpenAI provider."
            )
        if not api_version:
            raise SystemExit(
                "AZURE_OPENAI_API_VERSION or OPENAI_API_VERSION is required for the Azure OpenAI provider."
            )
        return (
            AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version,
            ),
            model,
            prompt,
        )

    raise SystemExit("Unsupported llm provider: %s" % provider)


def should_enable_plugins(args: argparse.Namespace) -> bool:
    return (
        args.use_plugins
        or args.enable_ocr
        or env_truthy("MARKITDOWN_ENABLE_PLUGINS")
        or env_truthy("MARKITDOWN_ENABLE_OCR")
    )


def _timeout_handler(signum, frame):  # type: ignore[no-untyped-def]
    raise FileConversionTimeout("Timed out while converting the current file.")


def convert_one(
    input_path: Path,
    output_path: Optional[Path],
    args: argparse.Namespace,
    markitdown: Any,
) -> None:
    timeout_seconds = args.timeout_seconds
    previous_handler = None
    timed_call_supported = timeout_seconds is not None and timeout_seconds > 0 and hasattr(signal, "SIGALRM")
    if timed_call_supported:
        previous_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_seconds)
    try:
        result = markitdown.convert(
            str(input_path),
            keep_data_uris=args.keep_data_uris,
        )
    finally:
        if timed_call_supported:
            signal.alarm(0)
            assert previous_handler is not None
            signal.signal(signal.SIGALRM, previous_handler)

    if args.stdout:
        sys.stdout.write(result.markdown)
        if not result.markdown.endswith("\n"):
            sys.stdout.write("\n")
        return

    if output_path is None:
        raise SystemExit("Internal error: output path is missing.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")
    print(output_path)


def format_error(input_path: Path, exc: Exception) -> str:
    return f"FAILED\t{input_path}\t{type(exc).__name__}: {exc}"


def main() -> int:
    ensure_runtime_python()

    args = parse_args()
    apply_compat_extra_args(args)
    input_paths = normalize_inputs(args.inputs)
    jobs = build_jobs(input_paths, args)

    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise SystemExit(
            "The active Python runtime does not provide markitdown. "
            "Set MARKITDOWN_PYTHON to the correct interpreter if needed."
        ) from exc

    llm_client, llm_model, llm_prompt = build_llm_client(args)
    markitdown_kwargs = {
        "enable_plugins": should_enable_plugins(args),
    }
    if llm_client is not None:
        markitdown_kwargs["llm_client"] = llm_client
    if llm_model:
        markitdown_kwargs["llm_model"] = llm_model
    if llm_prompt:
        markitdown_kwargs["llm_prompt"] = llm_prompt

    converter = MarkItDown(**markitdown_kwargs)

    failures: List[str] = []
    for job in jobs:
        output_path = None if args.stdout else resolve_output_path(job, args)
        try:
            convert_one(job.input_path, output_path, args, converter)
        except Exception as exc:
            if not args.skip_errors:
                raise
            message = format_error(job.input_path, exc)
            failures.append(message)
            print(message, file=sys.stderr)

    if failures:
        print(
            f"Completed with {len(failures)} skipped file(s).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
