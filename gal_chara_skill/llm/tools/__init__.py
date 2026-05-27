from .remove_duplicates import REMOVE_DUPLICATES
from .write_field import write_field
from .write_file import WRITE_FILE
from ..providers import OpenAIProvider

write_file_tool = lambda: OpenAIProvider().build_tool_request(WRITE_FILE)
remove_duplicates_tool = lambda: OpenAIProvider().build_tool_request(REMOVE_DUPLICATES)
write_field_tool = lambda field_names: OpenAIProvider().build_tool_request(write_field(field_names))

__all__ = ["write_file_tool", "remove_duplicates_tool", "write_field_tool"]
