from __future__ import annotations


class LLMResponse:
    """Class representing a processed LLM response"""

    def __init__(self, thinking_start_tag: str | None = None, thinking_end_tag: str | None = None):
        self._thinking_start_tag = thinking_start_tag
        self._thinking_end_tag = thinking_end_tag
        self._thoughts: str = ""
        self._content: str = ""

        self._thinking_started = False
        self._thinking_finished = False

    @property
    def thoughts(self) -> str | None:
        return self._thoughts

    @property
    def content(self) -> str | None:
        return self._content

    @property
    def thinking_in_progress(self) -> bool:
        return self._thinking_started and not self._thinking_finished

    def append(self, chunk: str):
        thinking_processed = self._process_thinking(chunk)
        if not self.thinking_in_progress and not thinking_processed:
            self._content += chunk

    def _process_thinking(self, chunk: str) -> bool:
        if self._thinking_finished or (self._thinking_start_tag is None) or (self._thinking_end_tag is None):
            return False

        thinking_start_tag_position = chunk.find(self._thinking_start_tag)
        thinking_end_tag_position = chunk.find(self._thinking_end_tag)

        thinking_start = (
            thinking_start_tag_position + len(self._thinking_start_tag) if thinking_start_tag_position != -1 else None
        )
        thinking_end = thinking_end_tag_position if thinking_end_tag_position != -1 else None
        content_start = thinking_end + len(self._thinking_end_tag) if thinking_end is not None else None
        if content_start is not None and content_start >= len(chunk):
            content_start = None

        chunk_processed = False

        if thinking_start is not None:
            if thinking_end is not None:
                self._thoughts += chunk[thinking_start:thinking_end].strip()
            else:
                self._thoughts += chunk[thinking_start:].lstrip()
            self._thinking_started = True
            chunk_processed = True

        if thinking_end is not None:
            if not chunk_processed:
                self._thoughts += chunk[:thinking_end].rstrip()
                chunk_processed = True
            self._thinking_finished = True

        if self.thinking_in_progress and not chunk_processed:
            self._thoughts += chunk
            return True

        if content_start is not None:
            self._content += chunk[content_start:].lstrip()
            return True

        return chunk_processed
