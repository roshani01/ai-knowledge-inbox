from backend.app.services.chunker import TextChunker, chunk_text


def test_chunk_empty_or_whitespace():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  \t  ") == []


def test_chunk_short_note():
    short_content = "This is a quick note about Q3 company goals and roadmap."
    chunks = chunk_text(short_content)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == short_content
    assert chunks[0].char_count == len(short_content)


def test_chunk_long_document():
    # Construct a long text with distinct paragraphs
    paragraphs = [
        f"Paragraph {i}: This is detailed content explaining concept number {i}. "
        "It provides in-depth architectural considerations and implementation details. " * 5
        for i in range(25)
    ]
    full_text = "\n\n".join(paragraphs)

    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split_text(full_text)

    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert len(c.content.strip()) > 0
        assert c.char_count == len(c.content)


def test_chunk_custom_separators():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    text = "First section. Second section with more words. Third section with additional context."
    chunks = chunker.split_text(text)
    assert len(chunks) >= 1
    assert all(c.content for c in chunks)
