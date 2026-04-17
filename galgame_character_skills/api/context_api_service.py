from ..domain import ok_result


def get_context_limit_result(data, get_model_context_limit):
    model_name = data.get('model_name', '')
    limit = get_model_context_limit(model_name)
    return ok_result(context_limit=limit)
