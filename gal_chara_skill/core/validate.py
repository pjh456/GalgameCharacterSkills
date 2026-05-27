from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
import inspect
from typing import Any, Callable, Optional, ParamSpec, TypeVar, Union

from numpydoc_decorator import doc

from .result import Result

P = ParamSpec("P")
T = TypeVar("T")
MISSING = object()


@doc(
    summary="描述单个字典字段的校验规则",
    parameters={
        "type_": "字段允许的类型或类型元组",
        "error": "该字段自身失败时的错误文本，默认继承外层入口错误",
        "code": "该字段自身失败时的错误码，默认继承外层入口错误码",
        "required": "字段是否必须存在",
        "allow_none": "字段是否允许为 None",
        "default": "字段缺失时使用的默认值",
        "literal": "字段允许的字面量集合",
        "item_type": "当字段为列表或元组时，元素允许的类型或类型元组",
        "item_transform": "当字段为列表或元组时，对每个元素执行的转换函数",
        "non_empty": "字段是否要求长度大于 0",
        "validator": "对字段值执行的额外校验函数，返回 False 或错误文本表示失败",
        "transform": "字段值通过基础校验后的转换函数，可直接返回 Result",
    },
)
@dataclass(frozen=True)
class FieldRule:
    type_: type[Any] | tuple[type[Any], ...]
    error: Optional[str] = None
    code: Optional[str] = None
    required: bool = True
    allow_none: bool = False
    default: Any = MISSING
    literal: Optional[set[Any]] = None
    item_type: Optional[type[Any] | tuple[type[Any], ...]] = None
    item_transform: Optional[Callable[[Any], Union[Any, "Result[Any]"]]] = None
    non_empty: bool = False
    validator: Optional[Callable[[Any], Union[bool, str, None]]] = None
    transform: Optional[Callable[[Any], Union[Any, "Result[Any]"]]] = None


@doc(
    summary="from_dict 风格的字典字段校验",
    parameters={
        "data_arg": "被视为原始字典输入的参数名",
        "error": "校验失败时统一返回的错误文本",
        "code": "校验失败时统一返回的错误码",
        "keep_unknown": "是否保留未声明字段并传给原函数",
        "fields": "按字段名组织的校验规则映射",
    },
    returns="可应用于返回 Result 的函数装饰器",
)
def validate_dict_fields(
    *,
    data_arg: str = "data",
    error: str,
    code: str,
    keep_unknown: bool = True,
    **fields: FieldRule,
) -> Callable[[Callable[P, Result[T]]], Callable[P, Result[T]]]:
    def decorator(func: Callable[P, Result[T]]) -> Callable[P, Result[T]]:
        signature = inspect.signature(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T]:
            bound = signature.bind_partial(*args, **kwargs)
            if data_arg not in bound.arguments:
                raise TypeError(f"缺少用于校验的参数: {data_arg}")

            validation_result = _validate_data(
                bound.arguments[data_arg],
                fields=fields,
                error=error,
                code=code,
                keep_unknown=keep_unknown,
            )
            if not validation_result.ok:
                return Result.failure_from(
                    validation_result,
                    error=error,
                    code=code,
                )

            bound.arguments[data_arg] = validation_result.unwrap()
            return func(*bound.args, **bound.kwargs)

        return wrapper

    return decorator


@doc(
    summary="校验原始输入字典并返回规范化后的字段映射",
    parameters={
        "data": "待校验的原始输入对象",
        "fields": "按字段名组织的校验规则映射",
        "error": "校验失败时统一返回的错误文本",
        "code": "校验失败时统一返回的错误码",
        "keep_unknown": "是否保留未声明字段",
    },
    returns="成功时 value 为规范化后的字段字典，失败时返回具体字段错误",
)
def _validate_data(
    data: Any,
    *,
    fields: dict[str, FieldRule],
    error: str,
    code: str,
    keep_unknown: bool,
) -> Result[dict[str, Any]]:
    if not isinstance(data, dict):
        return _build_failure(
            error,
            code=code,
            actual_type=type(data).__name__,
        )

    normalized: dict[str, Any] = dict(data) if keep_unknown else {}

    for field_name, rule in fields.items():
        has_value = field_name in data
        if not has_value:
            if rule.default is not MISSING:
                default_result = _validate_field(
                    field_name,
                    deepcopy(rule.default),
                    rule,
                    error=error,
                    code=code,
                )
                if not default_result.ok:
                    return default_result
                normalized[field_name] = default_result.value
                continue
            if rule.required:
                return _build_failure(
                    error,
                    code=code,
                    field=field_name,
                )
            continue

        field_result = _validate_field(field_name, data[field_name], rule, error=error, code=code)
        if not field_result.ok:
            return field_result

        normalized[field_name] = field_result.value

    return Result.success(normalized)


@doc(
    summary="按单条规则校验并规范化一个字段值",
    parameters={
        "field_name": "当前字段名",
        "value": "待校验的字段值",
        "rule": "字段校验规则",
        "error": "校验失败时统一返回的错误文本",
        "code": "校验失败时统一返回的错误码",
    },
    returns="成功时 value 为校验后的字段值，失败时返回具体字段错误",
)
def _validate_field(
    field_name: str,
    value: Any,
    rule: FieldRule,
    *,
    error: str,
    code: str,
) -> Result[Any]:
    field_error = rule.error or error
    field_code = rule.code or code

    if value is None:
        if rule.allow_none:
            return Result.success(None)
        return _build_field_failure(
            error=field_error,
            code=field_code,
            field_name=field_name,
        )

    if not _matches_type(value, rule.type_):
        return _build_field_failure(
            error=field_error,
            code=field_code,
            field_name=field_name,
            expected=_type_name(rule.type_),
            actual_type=type(value).__name__,
        )

    item_result = _validate_list_items(
        field_name,
        value,
        rule,
        error=field_error,
        code=field_code,
    )
    if not item_result.ok:
        return item_result

    normalized = value
    if rule.transform is not None:
        try:
            normalized = rule.transform(normalized)
        except Exception as exc:
            return _build_field_failure(
                error=field_error,
                code=field_code,
                field_name=field_name,
                exception=str(exc),
            )
        if isinstance(normalized, Result):
            if not normalized.ok:
                return _wrap_field_failure(
                    result=normalized,
                    error=field_error,
                    code=field_code,
                    field=field_name,
                )
            normalized = normalized.value

    item_transform_result = _transform_list_items(
        field_name,
        normalized,
        rule,
        error=error,
        code=code,
    )
    if not item_transform_result.ok:
        return item_transform_result
    normalized = item_transform_result.unwrap()

    if rule.literal is not None and normalized not in rule.literal:
        return _build_field_failure(
            error=field_error,
            code=field_code,
            field_name=field_name,
            expected=list(rule.literal),
            actual=normalized,
        )

    if rule.non_empty:
        try:
            if len(normalized) == 0:
                return _build_field_failure(
                    error=field_error,
                    code=field_code,
                    field_name=field_name,
                )
        except TypeError:
            return _build_field_failure(
                error=field_error,
                code=field_code,
                field_name=field_name,
                actual_type=type(normalized).__name__,
            )

    if rule.validator is not None:
        validator_result = rule.validator(normalized)
        if validator_result is False:
            return _build_field_failure(
                error=field_error,
                code=field_code,
                field_name=field_name,
            )
        if isinstance(validator_result, str):
            return _build_field_failure(
                error=field_error,
                code=field_code,
                field_name=field_name,
                detail=validator_result,
            )

    return Result.success(normalized)


@doc(
    summary="校验列表或元组中每个元素的类型",
    parameters={
        "field_name": "当前字段名",
        "value": "待校验的字段值",
        "rule": "字段校验规则",
        "error": "字段级失败时的错误文本",
        "code": "字段级失败时的错误码",
    },
    returns="成功时表示元素类型校验通过，失败时返回具体元素错误",
)
def _validate_list_items(
    field_name: str,
    value: Any,
    rule: FieldRule,
    *,
    error: str,
    code: str,
) -> Result[None]:
    if rule.item_type is None:
        return Result.success()

    if not isinstance(value, (list, tuple)):
        return _build_field_failure(
            error=error,
            code=code,
            field_name=field_name,
            actual_type=type(value).__name__,
        )

    for index, item in enumerate(value):
        if not _matches_type(item, rule.item_type):
            return _build_field_failure(
                error=error,
                code=code,
                field_name=field_name,
                index=index,
                expected=_type_name(rule.item_type),
                actual_type=type(item).__name__,
            )

    return Result.success()


@doc(
    summary="对列表或元组字段的每个元素执行规范化转换",
    parameters={
        "field_name": "当前字段名",
        "value": "已完成基础校验的字段值",
        "rule": "字段校验规则",
        "error": "外层入口失败时的统一错误文本",
        "code": "外层入口失败时的统一错误码",
    },
    returns="成功时 value 为转换后的字段值，失败时返回具体元素错误",
)
def _transform_list_items(
    field_name: str,
    value: Any,
    rule: FieldRule,
    *,
    error: str,
    code: str,
) -> Result[Any]:
    if rule.item_transform is None:
        return Result.success(value)

    field_error = rule.error or error
    field_code = rule.code or code

    if not isinstance(value, (list, tuple)):
        return _build_field_failure(
            error=field_error,
            code=field_code,
            field_name=field_name,
            actual_type=type(value).__name__,
        )

    transformed_items: list[Any] = []
    for index, item in enumerate(value):
        try:
            transformed_item = rule.item_transform(item)
        except Exception as exc:
            return _build_field_failure(
                error=field_error,
                code=field_code,
                field_name=field_name,
                index=index,
                exception=str(exc),
            )

        if isinstance(transformed_item, Result):
            if not transformed_item.ok:
                return _wrap_field_failure(
                    result=transformed_item,
                    error=field_error,
                    code=field_code,
                    field=field_name,
                    index=index,
                )
            transformed_item = transformed_item.value

        transformed_items.append(transformed_item)

    if isinstance(value, tuple):
        return Result.success(tuple(transformed_items))
    return Result.success(transformed_items)


@doc(
    summary="判断字段值是否符合声明的类型规则",
    parameters={
        "value": "待判断的字段值",
        "expected": "允许的类型或类型元组",
    },
    returns="字段值是否满足类型要求",
)
def _matches_type(
    value: Any,
    expected: type[Any] | tuple[type[Any], ...],
) -> bool:
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    if isinstance(value, bool) and bool not in expected_types:
        if int in expected_types or float in expected_types:
            return False
    return isinstance(value, expected_types)


@doc(
    summary="将类型规则转换为易读文本",
    parameters={"expected": "允许的类型或类型元组"},
    returns="适合放入错误详情的类型名称文本",
)
def _type_name(expected: type[Any] | tuple[type[Any], ...]) -> str | list[str]:
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    names = [expected_type.__name__ for expected_type in expected_types]
    return names[0] if len(names) == 1 else names


@doc(
    summary="构造一条统一格式的字段校验失败结果",
    parameters={
        "error": "校验失败时统一返回的错误文本",
        "code": "校验失败时统一返回的错误码",
        "data": "需要附带返回的额外错误信息",
    },
    returns="封装字段上下文的失败结果对象",
)
def _build_failure(error: str, *, code: str, **data: Any) -> Result[Any]:
    return Result.failure(error, code=code, **data)


@doc(
    summary="构造一条保留外层边界语义的字段失败结果",
    parameters={
        "error": "字段级失败时的错误文本",
        "code": "字段级失败时的错误码",
        "field_name": "当前失败字段名",
        "data": "需要附带的额外上下文",
    },
    returns="一个字段级失败结果对象",
)
def _build_field_failure(
    *,
    error: str,
    code: str,
    field_name: str,
    **data: Any,
) -> Result[Any]:
    return Result.failure(
        error,
        code=code,
        field=field_name,
        **data,
    )


@doc(
    summary="基于下游失败结果构造字段级包装结果",
    parameters={
        "result": "下游返回的失败结果",
        "error": "当前字段包装使用的错误文本",
        "code": "当前字段包装使用的错误码",
        "data": "需要附带的额外上下文",
    },
    returns="一个以 failure_from 形式包装下游失败的结果对象",
)
def _wrap_field_failure(
    result: Result[Any],
    *,
    error: str,
    code: str,
    **data: Any,
) -> Result[Any]:
    return Result.failure_from(
        result,
        error=error,
        code=code,
        **data,
    )


__all__ = [
    "FieldRule",
    "validate_dict_fields",
]
