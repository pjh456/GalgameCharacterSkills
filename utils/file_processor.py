import os
import sys
import tiktoken

class FileProcessor:
    def __init__(self):
        self.resource_dir = self._get_resource_dir()
        os.makedirs(self.resource_dir, exist_ok=True)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _get_base_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def _get_resource_dir(self):
        return os.path.join(self._get_base_dir(), 'resource')
    
    def scan_resource_files(self):
        files = []
        if os.path.exists(self.resource_dir):
            for file in os.listdir(self.resource_dir):
                if file.endswith(".txt"):
                    files.append(os.path.join(self.resource_dir, file))
        return files
    
    def calculate_tokens(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tokens = self.tokenizer.encode(content)
            return len(tokens)
        except Exception as e:
            return 0
    
    def calculate_slices(self, token_count):
        slice_size = 50000
        return (token_count // slice_size) + 1
    
    def slice_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            token_count = self.calculate_tokens(file_path)
            slice_count = self.calculate_slices(token_count)
            lines_per_slice = len(lines) // slice_count
            slices = []
            for i in range(slice_count):
                start_line = i * lines_per_slice
                end_line = (i + 1) * lines_per_slice if i < slice_count - 1 else len(lines)
                slice_content = ''.join(lines[start_line:end_line])
                slices.append(slice_content)
            return slices
        except Exception as e:
            return []
    
    def read_file_first_1000_lines(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:1000]
            return ''.join(lines)
        except Exception as e:
            return ""
