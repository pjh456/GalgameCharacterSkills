from ..domain import ok_result, fail_result


def ok_task_result(message=None, checkpoint_id=None, can_resume=None, **payload):
    extra = dict(payload)
    if checkpoint_id is not None:
        extra["checkpoint_id"] = checkpoint_id
    if can_resume is not None:
        extra["can_resume"] = can_resume
    return ok_result(message=message, **extra)


def fail_task_result(message, checkpoint_id=None, can_resume=None, **payload):
    extra = dict(payload)
    if checkpoint_id is not None:
        extra["checkpoint_id"] = checkpoint_id
    if can_resume is not None:
        extra["can_resume"] = can_resume
    return fail_result(message, **extra)


__all__ = ["ok_task_result", "fail_task_result"]
