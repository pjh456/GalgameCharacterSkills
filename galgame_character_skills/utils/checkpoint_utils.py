from ..domain import ok_result, fail_result


def load_resumable_checkpoint(ckpt_manager, checkpoint_id):
    ckpt = ckpt_manager.load_checkpoint(checkpoint_id)
    if not ckpt:
        return fail_result(f'未找到Checkpoint: {checkpoint_id}')
    if ckpt['status'] == 'completed':
        return fail_result('该任务已完成，无需恢复')
    return ok_result(checkpoint=ckpt)
