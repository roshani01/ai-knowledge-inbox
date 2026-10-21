import pytest
from backend.app.core.errors import SSRFSecurityError, UrlFetchError
from backend.app.services.url_extractor import (
    extract_readable_text,
    is_ip_allowed,
    validate_url_for_ssrf,
)


def test_is_ip_allowed():
    # Restricted IPs
    assert not is_ip_allowed("127.0.0.1")
    assert not is_ip_allowed("10.0.0.1")
    assert not is_ip_allowed("172.16.0.1")
    assert not is_ip_allowed("192.168.1.1")
    assert not is_ip_allowed("169.254.169.254")
    assert not is_ip_allowed("::1")
    assert not is_ip_allowed("fe80::1")
    assert not is_ip_allowed("0.0.0.0")

    # Public IPs
    assert is_ip_allowed("8.8.8.8")
    assert is_ip_allowed("1.1.1.1")
    assert is_ip_allowed("93.184.216.34")


def test_ssrf_validation_disallowed_hosts():
    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("http://localhost:8000/secret")

    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("http://127.0.0.1/admin")

    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("http://169.254.169.254/latest/meta-data")

    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("http://metadata.google.internal/computeMetadata/v1")

    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("ftp://example.com/file.txt")

    with pytest.raises(SSRFSecurityError):
        validate_url_for_ssrf("file:///etc/passwd")


def test_extract_readable_text_strips_scripts_and_styles():
    raw_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Engineering Blog - AI Knowledge</title>
        <style>body { background: #000; }</style>
        <script>alert('malicious');</script>
      </head>
      <body>
        <nav><a href="/">Home</a><a href="/about">About</a></nav>
        <main>
          <h1>Building Grounded RAG Systems</h1>
          <p>Vector search combined with clean chunking provides accurate answers.</p>
          <aside>Related links and ads</aside>
        </main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    title, content = extract_readable_text(raw_html, "Default Title")
    assert title == "Engineering Blog - AI Knowledge"
    assert "Building Grounded RAG Systems" in content
    assert "Vector search combined with clean chunking provides accurate answers." in content
    assert "alert('malicious')" not in content
    assert "background: #000" not in content
    assert "Related links and ads" not in content
    assert "Copyright 2026" not in content
