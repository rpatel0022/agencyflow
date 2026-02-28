"""Tests for file parser — TXT and PDF extraction."""

import pytest

from app.file_parser import parse_file, PDF_MAGIC_BYTES


class TestFileParser:

    @pytest.mark.asyncio
    async def test_parse_txt_file(self):
        content = b"This is a test brief with enough content to parse."
        result = await parse_file("brief.txt", content)
        assert result == "This is a test brief with enough content to parse."

    @pytest.mark.asyncio
    async def test_parse_txt_strips_whitespace(self):
        content = b"  Hello world  \n\n"
        result = await parse_file("brief.txt", content)
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_rejects_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            await parse_file("brief.docx", b"content")

    @pytest.mark.asyncio
    async def test_rejects_invalid_pdf_magic_bytes(self):
        with pytest.raises(ValueError, match="does not appear to be a valid PDF"):
            await parse_file("brief.pdf", b"NOT A PDF FILE CONTENT")

    @pytest.mark.asyncio
    async def test_rejects_exe_renamed_to_pdf(self):
        """Ensures magic byte validation catches renamed files."""
        fake_exe = b"MZ" + b"\x00" * 100  # PE executable magic bytes
        with pytest.raises(ValueError, match="does not appear to be a valid PDF"):
            await parse_file("malicious.pdf", fake_exe)
