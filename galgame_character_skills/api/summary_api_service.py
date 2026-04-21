from ..domain import ok_result, fail_result


def scan_summary_roles_result(get_summaries_dir, discover_summary_roles):
    summaries_dir = get_summaries_dir()
    result = discover_summary_roles(summaries_dir)
    result['success'] = True
    return result


def get_summary_files_result(data, get_summaries_dir, find_summary_files_for_role):
    role_name = data.get('role_name', '')
    mode = data.get('mode', 'skills')
    if not role_name:
        return fail_result('请输入角色名称')
    summaries_dir = get_summaries_dir()
    matching_files = find_summary_files_for_role(summaries_dir, role_name, mode=mode)
    return ok_result(files=matching_files)
