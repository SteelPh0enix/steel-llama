from __future__ import annotations


class LLMResponse:
    """Class representing a processed LLM response"""

    def __init__(self, raw_response: str, thinking_tags: tuple[str, str] | None = None):
        self.thinking_start_tag: str | None = None
        self.thinking_end_tag: str | None = None
        self.thoughts: str | None = None
        self.content: str | None = None

        if thinking_tags is not None:
            self.thinking_start_tag, self.thinking_end_tag = thinking_tags

        self._process(raw_response)

    def _process(self, raw_response: str):
        self._extract_thoughts(raw_response.strip())

    def _extract_thoughts(self, raw_response: str):
        if (self.thinking_start_tag is not None) and (self.thinking_end_tag is not None):
            thinking_start_tag_position = raw_response.find(self.thinking_start_tag)
            thinking_end_tag_position = raw_response.find(self.thinking_end_tag)

            if thinking_start_tag_position != -1:
                thoughts_start = thinking_start_tag_position + len(self.thinking_start_tag)
                if thinking_end_tag_position != -1:
                    # both prefix and suffix are found
                    thoughts_end = thinking_end_tag_position + len(self.thinking_end_tag)
                    self.thoughts = raw_response[thoughts_start:thinking_end_tag_position].strip()
                    self.content = raw_response[thoughts_end:].lstrip()
                else:
                    # only prefix is found, thinking in progress
                    self.thoughts = raw_response[thoughts_start:].lstrip()
            else:
                # no tags found, no thinking content
                self.content = raw_response
        else:
            # model is not gonna output any thoughts, nothing to do
            self.content = raw_response
