import os
import json

class ToolHandler:
    @staticmethod
    def write_file(file_path, content):
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written successfully: {file_path}"
        except Exception as e:
            return f"File write failed: {str(e)}"
    
    @staticmethod
    def handle_tool_call(tool_call):
        if hasattr(tool_call, 'function'):
            function_name = tool_call.function.name
            arguments_str = tool_call.function.arguments
        else:
            function_name = tool_call['function']['name']
            arguments_str = tool_call['function']['arguments']
        
        if isinstance(arguments_str, str):
            arguments = json.loads(arguments_str)
        else:
            arguments = arguments_str
        
        if function_name == 'write_file':
            file_path = arguments.get('file_path')
            content = arguments.get('content')
            if file_path and content:
                return ToolHandler.write_file(file_path, content)
            else:
                return "Missing required parameters"
        else:
            return f"Unknown tool: {function_name}"
