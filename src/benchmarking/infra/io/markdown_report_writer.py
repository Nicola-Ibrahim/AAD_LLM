"""Filesystem adapter for statistical Markdown reports."""

from pathlib import Path

from benchmarking.application.interfaces.markdown_report_writer import MarkdownReportWriter


class MarkdownFileWriter(MarkdownReportWriter):
    def write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
