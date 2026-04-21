from .checkpoint_prepare import prepare_request_with_checkpoint


def prepare_task_context(
    data,
    runtime,
    *,
    from_payload,
    config_builder,
    checkpoint_task_type,
    load_resume_state,
    build_initial_state,
    load_resumable_checkpoint_fn,
    build_prepared,
    validate_before_checkpoint=None,
    validate_after_checkpoint=None,
    on_resumed=None,
):
    request_data = from_payload(data, runtime)

    if validate_before_checkpoint:
        error = validate_before_checkpoint(request_data, data, runtime)
        if error:
            return None, error

    config = config_builder(data)

    checkpoint_data, error = prepare_request_with_checkpoint(
        request_data=request_data,
        checkpoint_gateway=runtime.checkpoint_gateway,
        task_type=checkpoint_task_type,
        load_resume_state=load_resume_state,
        build_initial_state=build_initial_state,
        load_resumable_checkpoint_fn=load_resumable_checkpoint_fn,
    )
    if error:
        return None, error

    if checkpoint_data.resumed and on_resumed:
        on_resumed(request_data, checkpoint_data, runtime)

    if validate_after_checkpoint:
        error = validate_after_checkpoint(request_data, data, runtime, checkpoint_data)
        if error:
            return None, error

    return build_prepared(request_data, config, checkpoint_data), None


__all__ = ["prepare_task_context"]
