"""LLM 交互模块，封装消息构造、completion 调用与工具循环入口。"""

from typing import Any

from ..gateways.tool_gateway import DefaultToolGateway
from .transport import CompletionTransport
from .runtime import LLMRequestRuntime
from .provider_config import normalize_model_name, build_completion_kwargs
from .character_card_flow import generate_character_card, integrate_character_analyses
from .prompts import (
    build_summarize_content_payload,
    build_summarize_chara_card_payload,
    build_generate_skills_folder_init_payload,
    build_compress_content_payload,
)
LANG_NAMES = {"zh": "中文", "en": "English", "ja": "日本語"}

def _format_vndb_section(
    vndb_data: dict[str, Any] | None,
    title: str,
    bullet: str = "-",
) -> str:
    """格式化 VNDB 信息段落。

    Args:
        vndb_data: VNDB 数据。
        title: 段落标题。
        bullet: 列表前缀。

    Returns:
        str: 格式化后的段落文本。

    Raises:
        Exception: 文本构造失败时向上抛出。
    """
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
    _runtime_cls = LLMRequestRuntime

    def __init__(
        self,
        tool_gateway: Any = None,
        transport: Any = None,
        runtime: Any = None,
    ) -> None:
        """初始化 LLM 交互客户端。

        Args:
            tool_gateway: 工具网关。
            transport: 传输层实现。
            runtime: 运行时记录器。

        Returns:
            None

        Raises:
            Exception: 初始化失败时向上抛出。
        """
        self.baseurl = ""
        self.modelname = ""
        self.apikey = ""
        self.max_retries = 3
        self.tool_gateway = tool_gateway or DefaultToolGateway()
        self.transport = transport or CompletionTransport()
        self.runtime = runtime or self._runtime_cls()
    
    def set_config(
        self,
        baseurl: str,
        modelname: str,
        apikey: str,
        max_retries: int | None = None,
    ) -> None:
        """设置客户端配置。

        Args:
            baseurl: 接口基地址。
            modelname: 模型名。
            apikey: API Key。
            max_retries: 最大重试次数。

        Returns:
            None

        Raises:
            Exception: 配置设置失败时向上抛出。
        """
        self.baseurl = baseurl
        self.modelname = modelname
        self.apikey = apikey
        if max_retries is not None and max_retries > 0:
            self.max_retries = max_retries
    
    @classmethod
    def build_runtime(cls, total_requests: int = 0) -> Any:
        """构造请求级运行时实例。"""
        return cls._runtime_cls(total_requests=total_requests)

    def _log_request_start(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        use_counter: bool,
    ) -> None:
        """记录请求开始日志。"""
        self.runtime.log_request_start(
            model=model,
            baseurl=self.baseurl,
            apikey=self.apikey,
            messages=messages,
            tools=tools,
            use_counter=use_counter,
        )

    def _log_request_success(self, use_counter: bool) -> None:
        """记录请求成功日志。"""
        self.runtime.log_request_success(use_counter=use_counter)

    def _log_response_preview(self, response: Any) -> None:
        """记录响应预览日志。"""
        self.runtime.log_response_preview(response)

    def _log_request_failed(self, use_counter: bool) -> None:
        """记录请求失败日志。"""
        self.runtime.log_request_failed(use_counter=use_counter)
    
    def send_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_retries: int | None = None,
        use_counter: bool = True,
    ) -> Any:
        """发送一次模型请求。

        Args:
            messages: 消息列表。
            tools: 工具定义列表。
            max_retries: 最大重试次数。
            use_counter: 是否使用计数器。

        Returns:
            Any: 模型响应对象，失败时返回 None。

        Raises:
            Exception: 请求发送或回调执行失败时向上抛出。
        """
        if max_retries is None:
            max_retries = self.max_retries
        model = normalize_model_name(self.modelname, self.baseurl)
        self._log_request_start(model=model, messages=messages, tools=tools, use_counter=use_counter)
        kwargs = build_completion_kwargs(
            model=model,
            messages=messages,
            tools=tools,
            apikey=self.apikey,
            baseurl=self.baseurl,
        )
        
        print(f"[LLM] Attempt 1/{max_retries}")

        def _on_attempt_failed(attempt: int, error: Exception, retries: int) -> None:
            print(f"[LLM] Attempt {attempt + 1} failed: {error}")

        def _on_retry_wait(wait_time: int, attempt: int, retries: int) -> None:
            print(f"[LLM] Retrying in {wait_time} seconds...")

        def _on_success(response: Any) -> None:
            self._log_request_success(use_counter=use_counter)
            self._log_response_preview(response)

        def _on_final_failure(error: Exception) -> None:
            self._log_request_failed(use_counter=use_counter)

        return self.transport.complete_with_retry(
            kwargs=kwargs,
            max_retries=max_retries,
            on_attempt_failed=_on_attempt_failed,
            on_retry_wait=_on_retry_wait,
            on_success=_on_success,
            on_final_failure=_on_final_failure,
        )
    
    def get_tool_response(self, response: Any) -> list[Any] | None:
        """提取模型响应中的工具调用。"""
        if response and hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls'):
                return choice.message.tool_calls
        return None
    
    def summarize_content(
        self,
        content: str,
        role_name: str,
        instruction: str,
        output_file_path: str,
        output_language: str = "",
        vndb_data: dict[str, Any] | None = None,
    ) -> Any:
        """执行文本归纳请求。"""
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
    
    def summarize_content_for_chara_card(
        self,
        content: str,
        role_name: str,
        instruction: str,
        output_file_path: str,
        output_language: str = "",
        vndb_data: dict[str, Any] | None = None,
    ) -> Any:
        """执行角色卡分析归纳请求。"""
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
    
    def generate_skills_folder_init(
        self,
        summaries: str,
        role_name: str,
        output_language: str = "",
        vndb_data: dict[str, Any] | None = None,
        output_root_dir: str = "",
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """构造技能包初始化消息和工具定义。"""
        messages, tools = build_generate_skills_folder_init_payload(
            summaries=summaries,
            role_name=role_name,
            output_root_dir=output_root_dir,
            output_language=output_language,
            vndb_data=vndb_data,
            lang_names=LANG_NAMES,
            format_vndb_section=_format_vndb_section,
        )
        return messages, tools

    def compress_content_with_llm(
        self,
        group_files_content: dict[str, str],
        group_info: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """构造压缩请求消息和工具定义。"""
        messages, tools = build_compress_content_payload(
            group_files_content=group_files_content,
            group_info=group_info,
        )
        return messages, tools

    def generate_character_card_with_tools(
        self,
        role_name: str,
        all_analyses: list[dict[str, Any]],
        all_lorebook_entries: list[Any],
        output_path: str,
        creator: str = "",
        vndb_data: dict[str, Any] | None = None,
        output_language: str = "",
        checkpoint_id: str | None = None,
        ckpt_messages: list[dict[str, Any]] | None = None,
        ckpt_fields_data: dict[str, Any] | None = None,
        ckpt_iteration_count: int | None = None,
        save_llm_state_fn: Any = None,
    ) -> dict[str, Any]:
        """执行角色卡生成流程。"""
        return generate_character_card(
            send_message=self.send_message,
            tool_gateway=self.tool_gateway,
            lang_names=LANG_NAMES,
            format_vndb_section=_format_vndb_section,
            role_name=role_name,
            all_analyses=all_analyses,
            all_lorebook_entries=all_lorebook_entries,
            output_path=output_path,
            creator=creator,
            vndb_data=vndb_data,
            output_language=output_language,
            checkpoint_id=checkpoint_id,
            ckpt_messages=ckpt_messages,
            ckpt_fields_data=ckpt_fields_data,
            ckpt_iteration_count=ckpt_iteration_count,
            save_llm_state_fn=save_llm_state_fn,
        )
    
    def _integrate_analyses(
        self,
        role_name: str,
        all_analyses: list[dict[str, Any]],
        vndb_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """整合多份角色分析结果。"""
        return integrate_character_analyses(
            send_message=self.send_message,
            tool_gateway=self.tool_gateway,
            role_name=role_name,
            all_analyses=all_analyses,
            vndb_data=vndb_data,
            format_vndb_section=_format_vndb_section,
        )
