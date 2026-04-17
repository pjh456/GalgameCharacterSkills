import json
import sys
import os
from datetime import datetime
from ..gateways.tool_gateway import DefaultToolGateway
from .transport import CompletionTransport
from .runtime import LLMRequestRuntime
from .prompts import (
    build_summarize_content_payload,
    build_summarize_chara_card_payload,
    build_generate_skills_folder_init_payload,
    build_compress_content_payload,
)
from ..utils.prompt_builders import (
    build_character_card_language_instruction,
    build_character_card_system_prompt,
    build_character_card_user_prompt,
    build_integrate_analyses_system_prompt,
    build_integrate_analyses_user_prompt,
)

LANG_NAMES = {"zh": "中文", "en": "English", "ja": "日本語"}

def _format_vndb_section(vndb_data, title, bullet="-"):
    if not vndb_data:
        return ""

    entries = []
    field_map = [
        ("name", "Name"),
        ("original_name", "Original Name"),
        ("aliases", "Aliases"),
        ("description", "Description"),
        ("age", "Age"),
        ("birthday", "Birthday"),
        ("blood_type", "Blood Type"),
        ("height", "Height"),
        ("weight", "Weight"),
        ("traits", "Traits"),
        ("vns", "Visual Novels"),
    ]

    for key, label in field_map:
        value = vndb_data.get(key)
        if not value:
            continue
        if key == "aliases" and isinstance(value, list):
            value = ", ".join(value)
        elif key == "traits" and isinstance(value, list):
            value = ", ".join(value)
        elif key == "vns" and isinstance(value, list):
            value = ", ".join(value[:3])
        elif key == "height":
            value = f"{value}cm"
        elif key == "weight":
            value = f"{value}kg"
        prefix = f"{bullet} " if bullet else ""
        entries.append(f"{prefix}{label}: {value}")

    if vndb_data.get('bust') and vndb_data.get('waist') and vndb_data.get('hips'):
        prefix = f"{bullet} " if bullet else ""
        entries.append(f"{prefix}Measurements: {vndb_data['bust']}-{vndb_data['waist']}-{vndb_data['hips']}cm")

    if not entries:
        return ""

    return f"\n\n{title}\n" + "\n".join(entries) + "\n"

class LLMInteraction:
    def __init__(self):
        self.baseurl = ""
        self.modelname = ""
        self.apikey = ""
        self.max_retries = 3
        self.tool_gateway = DefaultToolGateway()
        self.transport = CompletionTransport()
    
    def set_config(self, baseurl, modelname, apikey, max_retries=None):
        self.baseurl = baseurl
        self.modelname = modelname
        self.apikey = apikey
        if max_retries is not None and max_retries > 0:
            self.max_retries = max_retries
    
    @classmethod
    def set_total_requests(cls, total):
        LLMRequestRuntime.set_total_requests(total)

    def _normalize_model_name(self):
        model = self.modelname
        baseurl = self.baseurl.lower() if self.baseurl else ''

        if model and '/' not in model:
            if 'deepseek' in baseurl:
                return f"deepseek/{model}"
            if 'anthropic' in baseurl or 'claude' in baseurl:
                return f"anthropic/{model}"
            if 'gemini' in baseurl or 'google' in baseurl:
                return f"google/{model}"
            return f"openai/{model}"
        return model

    def _build_completion_kwargs(self, model, messages, tools):
        kwargs = {
            "model": model,
            "messages": messages,
            "timeout": 300
        }

        if 'google' in model or 'gemini' in model:
            kwargs["safety_settings"] = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if self.apikey:
            kwargs["api_key"] = self.apikey
        if self.baseurl:
            kwargs["api_base"] = self.baseurl
        return kwargs

    def _log_request_start(self, model, messages, tools, use_counter):
        LLMRequestRuntime.log_request_start(
            model=model,
            baseurl=self.baseurl,
            apikey=self.apikey,
            messages=messages,
            tools=tools,
            use_counter=use_counter,
        )

    def _log_request_success(self, use_counter):
        LLMRequestRuntime.log_request_success(use_counter=use_counter)

    def _log_response_preview(self, response):
        LLMRequestRuntime.log_response_preview(response)

    def _log_request_failed(self, use_counter):
        LLMRequestRuntime.log_request_failed(use_counter=use_counter)
    
    def send_message(self, messages, tools=None, max_retries=None, use_counter=True):
        if max_retries is None:
            max_retries = self.max_retries
        model = self._normalize_model_name()
        self._log_request_start(model=model, messages=messages, tools=tools, use_counter=use_counter)
        kwargs = self._build_completion_kwargs(model=model, messages=messages, tools=tools)
        
        print(f"[LLM] Attempt 1/{max_retries}")

        def _on_attempt_failed(attempt, error, retries):
            print(f"[LLM] Attempt {attempt + 1} failed: {error}")

        def _on_retry_wait(wait_time, attempt, retries):
            print(f"[LLM] Retrying in {wait_time} seconds...")

        def _on_success(response):
            self._log_request_success(use_counter=use_counter)
            self._log_response_preview(response)

        def _on_final_failure(error):
            self._log_request_failed(use_counter=use_counter)

        return self.transport.complete_with_retry(
            kwargs=kwargs,
            max_retries=max_retries,
            on_attempt_failed=_on_attempt_failed,
            on_retry_wait=_on_retry_wait,
            on_success=_on_success,
            on_final_failure=_on_final_failure,
        )
    
    def get_tool_response(self, response):
        if response and hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls'):
                return choice.message.tool_calls
        return None
    
    def summarize_content(self, content, role_name, instruction, output_file_path, output_language="", vndb_data=None):
        messages, tools = build_summarize_content_payload(
            content=content,
            role_name=role_name,
            instruction=instruction,
            output_file_path=output_file_path,
            output_language=output_language,
            vndb_data=vndb_data,
            lang_names=LANG_NAMES,
            format_vndb_section=_format_vndb_section,
        )
        return self.send_message(messages, tools)
    
    def summarize_content_for_chara_card(self, content, role_name, instruction, output_file_path, output_language="", vndb_data=None):
        messages, tools = build_summarize_chara_card_payload(
            content=content,
            role_name=role_name,
            instruction=instruction,
            output_file_path=output_file_path,
            output_language=output_language,
            vndb_data=vndb_data,
            lang_names=LANG_NAMES,
            format_vndb_section=_format_vndb_section,
        )
        return self.send_message(messages, tools)
    
    def generate_skills_folder_init(self, summaries, role_name, output_language="", vndb_data=None):
        messages, tools = build_generate_skills_folder_init_payload(
            summaries=summaries,
            role_name=role_name,
            output_language=output_language,
            vndb_data=vndb_data,
            lang_names=LANG_NAMES,
            format_vndb_section=_format_vndb_section,
        )
        return messages, tools

    def compress_content_with_llm(self, group_files_content, group_info):
        messages, tools = build_compress_content_payload(
            group_files_content=group_files_content,
            group_info=group_info,
        )
        return messages, tools

    def generate_character_card_with_tools(self, role_name, all_analyses, all_lorebook_entries, output_path, creator="", vndb_data=None, output_language="", checkpoint_id=None, ckpt_messages=None, ckpt_fields_data=None, ckpt_iteration_count=None):
        integrated_analysis = self._integrate_analyses(role_name, all_analyses, vndb_data)
        
        vndb_ref = _format_vndb_section(vndb_data, "VNDB REFERENCE DATA (HIGHEST PRIORITY - Use these values as authoritative source for character appearance and basic info)", bullet="")
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_field",
                    "description": "Write a specific field to the character card JSON file. Call this tool multiple times to write different fields.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_name": {
                                "type": "string",
                                "description": "The name of the field to write. Must be one of: name, description, personality, first_mes, mes_example, scenario, system_prompt, post_history_instructions, depth_prompt",
                                "enum": ["name", "description", "personality", "first_mes", "mes_example", "scenario",
                                        "system_prompt", "post_history_instructions", "depth_prompt"]
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write for this field. For string fields, provide the text. For list fields (like personality traits), provide a JSON array string."
                            },
                            "is_complete": {
                                "type": "boolean",
                                "description": "Set to true if this is the last field you want to write. The system will finalize the character card after this."
                            }
                        },
                        "required": ["field_name", "content"]
                    }
                }
            }
        ]
        
        merged_entries = self.tool_gateway.merge_lorebook_entries(all_lorebook_entries)
        lorebook_entries = self.tool_gateway.build_lorebook_entries(merged_entries, start_id=0)
        
        base_name = role_name
        if vndb_data and vndb_data.get('name'):
            base_name = vndb_data['name']
        
        fields_data = {
            "name": base_name,
            "description": "",
            "personality": "",
            "first_mes": "",
            "mes_example": "",
            "scenario": "",
            "system_prompt": "",
            "post_history_instructions": "",
            "depth_prompt": "",
            "creatorcomment": f"Character card for {base_name}" + (f" (VNDB: {vndb_data.get('vndb_id', '')})" if vndb_data else ""),
            "world_name": base_name,
            "create_date": datetime.now().isoformat(),
            "creator": creator or "AI Character Generator",
            "tags": ["character", base_name.lower().replace(" ", "_")],
            "character_book_entries": lorebook_entries
        }

        is_resuming = ckpt_messages is not None and len(ckpt_messages) > 0
        if is_resuming and ckpt_fields_data:
            for key in fields_data:
                if key in ckpt_fields_data and ckpt_fields_data[key]:
                    if key == "character_book_entries":
                        continue
                    fields_data[key] = ckpt_fields_data[key]
        
        language_instruction = build_character_card_language_instruction(output_language, LANG_NAMES)
        integrated_analysis_json = json.dumps(integrated_analysis, ensure_ascii=False, indent=2)
        system_prompt = build_character_card_system_prompt(
            role_name=role_name,
            integrated_analysis_json=integrated_analysis_json,
            vndb_ref=vndb_ref,
            language_instruction=language_instruction,
        )

        if is_resuming:
            messages = ckpt_messages
            tool_call_count = ckpt_iteration_count or 0
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": build_character_card_user_prompt(role_name)}
            ]
            tool_call_count = 0
        
        max_tool_calls = 50 
        
        while tool_call_count < max_tool_calls:
            if checkpoint_id:
                from .checkpoint_manager import CheckpointManager
                mgr = CheckpointManager()
                mgr.save_llm_state(
                    checkpoint_id, messages=messages,
                    iteration_count=tool_call_count,
                    fields_data={k: v for k, v in fields_data.items() if k != 'character_book_entries'}
                )

            response = self.send_message(messages, tools=tools, use_counter=False)
            
            if not response or not response.choices:
                if checkpoint_id:
                    from .checkpoint_manager import CheckpointManager
                    mgr = CheckpointManager()
                    mgr.save_llm_state(
                        checkpoint_id, messages=messages,
                        last_response=None, iteration_count=tool_call_count,
                        fields_data={k: v for k, v in fields_data.items() if k != 'character_book_entries'}
                    )
                return {
                    'success': False,
                    'message': 'LLM交互失败',
                    'can_resume': True
                }
            
            message = response.choices[0].message
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "write_field":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            field_name = args.get("field_name")
                            content = args.get("content")
                            is_complete = args.get("is_complete", False)
                            
                            if field_name in ["creatorcomment", "creator_notes", "world_name"]:
                                pass
                            elif field_name and field_name in fields_data:
                                fields_data[field_name] = content
                                if is_complete:
                                    tool_call_count = max_tool_calls  
                        except Exception:
                            pass
                
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                        } for tc in message.tool_calls
                    ]
                })
                
                for tool_call in message.tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"status": "success", "message": f"Field written successfully"})
                    })
                
                tool_call_count += 1
            else:
                content = message.content
                
                try:
                    parsed = self.tool_gateway.parse_llm_json_response(content)
                    if parsed:
                        for key in fields_data.keys():
                            if key in parsed and key != "character_book_entries":
                                fields_data[key] = parsed[key]
                except Exception:
                    pass
                
                break

            if checkpoint_id:
                from .checkpoint_manager import CheckpointManager
                mgr = CheckpointManager()
                mgr.save_llm_state(
                    checkpoint_id, messages=messages,
                    last_response=response, iteration_count=tool_call_count,
                    fields_data={k: v for k, v in fields_data.items() if k != 'character_book_entries'}
                )
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'chara_card_template.json')
        
        field_mappings = {
            "{{name}}": fields_data["name"],
            "{{description}}": fields_data["description"],
            "{{personality}}": fields_data["personality"],
            "{{first_mes}}": fields_data["first_mes"],
            "{{mes_example}}": fields_data["mes_example"],
            "{{scenario}}": fields_data["scenario"],
            "{{create_date}}": fields_data["create_date"],
            "{{creatorcomment}}": fields_data["creatorcomment"],
            "{{system_prompt}}": fields_data["system_prompt"],
            "{{post_history_instructions}}": fields_data["post_history_instructions"],
            "{{tags}}": fields_data["tags"],
            "{{creator}}": fields_data["creator"],
            "{{world_name}}": fields_data["world_name"],
            "{{depth_prompt}}": fields_data["depth_prompt"],
            "{{character_book_entries}}": fields_data["character_book_entries"],
        }
        
        result = self.tool_gateway.fill_json_template(template_path, output_path, field_mappings)
        
        return {
            'success': True,
            'output_path': output_path,
            'fields_written': [k for k, v in fields_data.items() if v and k != 'character_book_entries'],
            'result': result
        }
    
    def _integrate_analyses(self, role_name, all_analyses, vndb_data=None):
        vndb_section = _format_vndb_section(vndb_data, "## VNDB Character Information", bullet="")
        system_prompt = build_integrate_analyses_system_prompt(role_name, vndb_section)
        
        analyses_json = json.dumps(all_analyses, ensure_ascii=False, indent=2)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_integrate_analyses_user_prompt(role_name, analyses_json)}
        ]
        
        response = self.send_message(messages, use_counter=False)
        
        if response and response.choices:
            content = response.choices[0].message.content
            result = self.tool_gateway.parse_llm_json_response(content) or {}
            return result
        return {}
