from typing import List
from pydantic import BaseModel
from backend.app.core.config import settings


class TextChunk(BaseModel):
    chunk_index: int
    content: str
    char_count: int


class TextChunker:
    """
    Splits text into chunks preserving semantic boundaries (paragraphs, sentences, words).
    Default target is approximately 500 tokens (~2000 characters) with 80 tokens (~320 characters) overlap.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        # Using ~4 chars per token approximation
        self.chunk_size_chars = chunk_size * 4
        self.overlap_chars = chunk_overlap * 4
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def split_text(self, text: str) -> List[TextChunk]:
        cleaned = text.strip()
        if not cleaned:
            return []

        # Short notes: return single chunk immediately
        if len(cleaned) <= self.chunk_size_chars:
            return [TextChunk(chunk_index=0, content=cleaned, char_count=len(cleaned))]

        raw_chunks = self._recursive_split(cleaned, self.separators)
        merged_chunks = self._merge_splits(raw_chunks)

        result: List[TextChunk] = []
        for idx, chunk_str in enumerate(merged_chunks):
            stripped = chunk_str.strip()
            if stripped:
                result.append(
                    TextChunk(
                        chunk_index=len(result),
                        content=stripped,
                        char_count=len(stripped),
                    )
                )

        # Fallback if no valid chunks generated
        if not result and cleaned:
            result.append(TextChunk(chunk_index=0, content=cleaned, char_count=len(cleaned)))

        return result

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if not separators or len(text) <= self.chunk_size_chars:
            return [text]

        sep = separators[0]
        remaining_separators = separators[1:]

        if sep == "":
            # Character level fallback
            return [
                text[i : i + self.chunk_size_chars]
                for i in range(0, len(text), self.chunk_size_chars)
            ]

        splits = text.split(sep)
        result: List[str] = []

        for piece in splits:
            if not piece.strip():
                continue
            if len(piece) <= self.chunk_size_chars:
                result.append(piece)
            else:
                # Recurse with finer separator
                result.extend(self._recursive_split(piece, remaining_separators))

        return result

    def _merge_splits(self, splits: List[str]) -> List[str]:
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for piece in splits:
            piece_len = len(piece)
            if current_length + piece_len + 1 > self.chunk_size_chars and current_chunk:
                merged = " ".join(current_chunk).strip()
                if merged:
                    chunks.append(merged)

                # Keep overlap from the end of current_chunk
                overlap_acc: List[str] = []
                overlap_len = 0
                for prev_piece in reversed(current_chunk):
                    if overlap_len + len(prev_piece) <= self.overlap_chars:
                        overlap_acc.insert(0, prev_piece)
                        overlap_len += len(prev_piece) + 1
                    else:
                        break

                current_chunk = overlap_acc
                current_length = sum(len(p) for p in current_chunk) + len(current_chunk)

            current_chunk.append(piece)
            current_length += piece_len + 1

        if current_chunk:
            final_chunk = " ".join(current_chunk).strip()
            if final_chunk:
                chunks.append(final_chunk)

        return chunks


default_chunker = TextChunker()


def chunk_text(text: str) -> List[TextChunk]:
    return default_chunker.split_text(text)
