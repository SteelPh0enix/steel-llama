from __future__ import annotations


class LLMResponse:
    """Class representing a processed LLM response"""

    def __init__(self, raw_response: str, thinking_tags: tuple[str, str] | None = None):
        self.raw_response: str = raw_response
        self.thinking_start_tag: str | None = None
        self.thinking_end_tag: str | None = None

        if thinking_tags is not None:
            self.thinking_start_tag, self.thinking_end_tag = thinking_tags

        self.process()

    def process(self):
        self.raw_response = self.raw_response.strip()
        self.extract_thoughts()

    def extract_thoughts(self):
        if (self.thinking_start_tag is not None) and (self.thinking_end_tag is not None):
            thinking_start_tag_position = self.raw_response.find(self.thinking_start_tag)
            thinking_end_tag_position = self.raw_response.find(self.thinking_end_tag)

            if thinking_start_tag_position != -1:
                if thinking_end_tag_position != -1:
                    # both prefix and suffix is found
                    thoughts_start = thinking_start_tag_position + len(self.thinking_start_tag)
                    self.thoughts = self.raw_response[thoughts_start:thinking_end_tag_position]
                    pass
                else:
                    pass
