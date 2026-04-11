import os
import sys
import webbrowser
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from utils.llm_interaction import LLMInteraction
from utils.file_processor import FileProcessor
from utils.tool_handler import ToolHandler

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=get_resource_path('utils'))
CORS(app)

file_processor = FileProcessor()
current_slices = []
summaries = []

class NoRequestFilter:
    def filter(self, record):
        return not (record.getMessage().startswith('127.0.0.1') and 'HTTP' in record.getMessage())

import logging
log = logging.getLogger('werkzeug')
log.addFilter(NoRequestFilter())

def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

def get_llm_client():
    data = request.json if request.is_json else {}
    baseurl = data.get('baseurl', '')
    modelname = data.get('modelname', '')
    apikey = data.get('apikey', '')
    client = LLMInteraction()
    if baseurl or modelname or apikey:
        client.set_config(baseurl, modelname, apikey)
    return client

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def scan_files():
    files = file_processor.scan_resource_files()
    return jsonify({'success': True, 'files': files})

@app.route('/api/summaries/roles', methods=['GET'])
def scan_summary_roles():
    roles = set()
    script_dir = get_base_dir()
    for root, dirs, files in os.walk(script_dir):
        for dir_name in dirs:
            if dir_name.endswith('_summaries'):
                summaries_dir = os.path.join(root, dir_name)
                for filename in os.listdir(summaries_dir):
                    if filename.endswith('.md'):
                        parts = filename.replace('.md', '').split('_')
                        if len(parts) >= 3:
                            role_name = '_'.join(parts[2:])
                            if role_name:
                                roles.add(role_name)
    return jsonify({
        'success': True,
        'roles': sorted(list(roles))
    })

@app.route('/api/summaries/files', methods=['POST'])
def get_summary_files():
    data = request.json
    role_name = data.get('role_name', '')
    if not role_name:
        return jsonify({'success': False, 'message': '请输入角色名称'})
    script_dir = get_base_dir()
    matching_files = []
    for root, dirs, files in os.walk(script_dir):
        for dir_name in dirs:
            if dir_name.endswith('_summaries'):
                summaries_dir = os.path.join(root, dir_name)
                for filename in sorted(os.listdir(summaries_dir)):
                    if filename.endswith('.md') and f'_{role_name}.md' in filename:
                        file_path = os.path.join(summaries_dir, filename)
                        matching_files.append(file_path)
    return jsonify({
        'success': True,
        'files': sorted(matching_files)
    })

@app.route('/api/files/tokens', methods=['POST'])
def calculate_tokens():
    data = request.json
    file_path = data.get('file_path', '')
    if not file_path:
        return jsonify({'success': False, 'message': '未提供文件路径'})
    try:
        token_count = file_processor.calculate_tokens(file_path)
        slice_count = file_processor.calculate_slices(token_count)
        return jsonify({
            'success': True,
            'token_count': token_count,
            'slice_count': slice_count,
            'formatted_tokens': f"{token_count:,}"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/slice', methods=['POST'])
def slice_file():
    data = request.json
    selected_file = data.get('file_path', '')
    if not selected_file:
        return jsonify({'success': False, 'message': '请先选择文件'})
    try:
        global current_slices
        current_slices = file_processor.slice_file(selected_file)
        return jsonify({
            'success': True,
            'message': f'文件已切片，共 {len(current_slices)} 个切片',
            'slice_count': len(current_slices)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'切片失败: {str(e)}'
        })

def process_single_slice(args):
    slice_index, slice_content, role_name, instruction, output_file_path, config = args
    llm_client = LLMInteraction()
    if config.get('baseurl') or config.get('modelname') or config.get('apikey'):
        llm_client.set_config(config.get('baseurl'), config.get('modelname'), config.get('apikey'))
    
    time.sleep(0.5 * slice_index)
    
    response = llm_client.summarize_content(slice_content, role_name, instruction, output_file_path)
    
    result = {
        'index': slice_index,
        'success': False,
        'summary': None,
        'tool_results': [],
        'output_path': output_file_path
    }
    
    if response and hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                tool_result = ToolHandler.handle_tool_call(tool_call)
                result['tool_results'].append(tool_result)
            result['success'] = True
            result['summary'] = f"Slice {slice_index + 1} saved to {output_file_path}"
        else:
            result['success'] = True
            result['summary'] = choice.message.content
    
    return result


@app.route('/api/summarize', methods=['POST'])
def summarize():
    global current_slices, summaries
    data = request.json
    role_name = data.get('role_name', '')
    instruction = data.get('instruction', '')
    selected_file = data.get('file_path', '')
    concurrency = data.get('concurrency', 1)
    
    if not role_name:
        return jsonify({'success': False, 'message': '请输入角色名称'})
    if not selected_file:
        return jsonify({'success': False, 'message': '请先选择文件'})
    
    llm_interaction = get_llm_client()
    current_slices = file_processor.slice_file(selected_file)
    LLMInteraction.set_total_requests(len(current_slices))
    
    summaries = []
    errors = []
    all_results = []
    
    file_name = os.path.basename(selected_file)
    name, ext = os.path.splitext(file_name)
    summary_dir = os.path.join(os.path.dirname(selected_file), f"{name}_summaries")
    os.makedirs(summary_dir, exist_ok=True)
    
    config = {
        'baseurl': data.get('baseurl', ''),
        'modelname': data.get('modelname', ''),
        'apikey': data.get('apikey', '')
    }
    
    tasks = []
    for i, slice_content in enumerate(current_slices):
        output_file_path = os.path.join(summary_dir, f"slice_{i+1:03d}_{role_name}.md")
        tasks.append((i, slice_content, role_name, instruction, output_file_path, config))
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_task = {executor.submit(process_single_slice, task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                if result['success']:
                    summaries.append(result['summary'])
                    all_results.extend(result['tool_results'])
                else:
                    errors.append(f'切片 {result["index"] + 1} 处理失败')
            except Exception as e:
                task = future_to_task[future]
                errors.append(f'切片 {task[0] + 1} 处理异常: {str(e)}')
    
    if errors:
        return jsonify({
            'success': len(summaries) > 0,
            'message': f'归纳完成，{len(errors)} 个切片失败',
            'slice_count': len(current_slices),
            'errors': errors,
            'results': all_results
        })
    
    return jsonify({
        'success': True,
        'message': '归纳完成',
        'slice_count': len(current_slices),
        'results': all_results
    })

@app.route('/api/skills', methods=['POST'])
def generate_skills():
    data = request.json
    role_name = data.get('role_name', '')
    if not role_name:
        return jsonify({'success': False, 'message': '请输入角色名称'})
    script_dir = get_base_dir()
    summary_files = []
    for root, dirs, files in os.walk(script_dir):
        for dir_name in dirs:
            if dir_name.endswith('_summaries'):
                summaries_dir = os.path.join(root, dir_name)
                for filename in sorted(os.listdir(summaries_dir)):
                    if filename.endswith('.md') and f'_{role_name}.md' in filename:
                        file_path = os.path.join(summaries_dir, filename)
                        summary_files.append(file_path)
    if not summary_files:
        return jsonify({'success': False, 'message': f'未找到角色 "{role_name}" 的归纳文件，请先完成归纳'})
    all_summaries = []
    for file_path in summary_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                all_summaries.append(f"=== {os.path.basename(file_path)} ===\n{content}")
        except Exception as e:
            pass
    summaries_text = "\n\n".join(all_summaries)
    llm_interaction = get_llm_client()
    messages, tools = llm_interaction.generate_skills_folder_init(summaries_text, role_name)
    all_results = []
    max_iterations = 20
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        response = llm_interaction.send_message(messages, tools, use_counter=False)
        if not response:
            return jsonify({'success': False, 'message': 'LLM交互失败'})
        tool_calls = llm_interaction.get_tool_response(response)
        if not tool_calls:
            break
        assistant_message = {
            "role": "assistant",
            "content": response.choices[0].message.content if response.choices[0].message.content else "",
            "tool_calls": [tc if isinstance(tc, dict) else {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            } for tc in tool_calls]
        }
        messages.append(assistant_message)
        for tool_call in tool_calls:
            result = ToolHandler.handle_tool_call(tool_call)
            all_results.append(result)
            import json
            tool_response = {
                "role": "tool",
                "tool_call_id": tool_call.id if hasattr(tool_call, 'id') else tool_call.get('id'),
                "content": json.dumps({"success": True, "result": result})
            }
            messages.append(tool_response)
    try:
        main_skill_dir = os.path.join(script_dir, f"{role_name}-skill-main")
        code_skill_dir = os.path.join(script_dir, f"{role_name}-skill-code")
        if os.path.exists(main_skill_dir):
            if os.path.exists(code_skill_dir):
                import shutil
                shutil.rmtree(code_skill_dir)
            import shutil
            shutil.copytree(main_skill_dir, code_skill_dir)
            limit_file = os.path.join(code_skill_dir, "limit.md")
            if os.path.exists(limit_file):
                os.remove(limit_file)
            all_results.append(f"Created {role_name}-skill-code (without limit.md)")
    except Exception as e:
        all_results.append(f"Warning: Failed to create -code version: {e}")
    return jsonify({
        'success': True,
        'message': f'技能文件夹生成完成，共执行 {len(all_results)} 次文件写入',
        'results': all_results
    })

if __name__ == '__main__':
    templates_dir = os.path.join(get_base_dir(), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
