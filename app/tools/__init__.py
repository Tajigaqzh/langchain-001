from app.tools.filesystem import (
    append_text_file,
    copy_file,
    list_directory,
    make_directory,
    move_file,
    path_info,
    read_csv_preview,
    read_json_file,
    read_text_file,
    search_text,
    tail_text_file,
    write_json_file,
    write_text_file,
)
from app.tools.git_tools import git_diff, git_status
from app.tools.mcp import load_mcp_tools
from app.tools.network_tools import get_local_ip, get_public_ip
from app.tools.python_tools import (
    compile_project,
    run_pytest,
    run_python_module,
    run_python_script,
)
from app.tools.shell_tools import run_shell_command
from app.tools.utility import (
    calculator,
    current_datetime_info,
    current_date,
    current_time,
    current_time_parts,
    current_timestamp,
    current_weekday,
    format_current_time,
    convert_timestamp,
    parse_datetime_string,
)
from app.tools.web_tools import fetch_webpage, web_search

__all__ = ["get_tools"]


def get_local_tools():
    """Return all tools available to the default Agent."""
    return [
        current_time,
        current_date,
        current_weekday,
        current_time_parts,
        current_timestamp,
        current_datetime_info,
        format_current_time,
        convert_timestamp,
        parse_datetime_string,
        calculator,
        get_local_ip,
        get_public_ip,
        list_directory,
        read_text_file,
        read_json_file,
        read_csv_preview,
        search_text,
        write_text_file,
        append_text_file,
        tail_text_file,
        write_json_file,
        make_directory,
        copy_file,
        move_file,
        path_info,
        run_pytest,
        git_status,
        git_diff,
        run_python_module,
        run_python_script,
        run_shell_command,
        compile_project,
        web_search,
        fetch_webpage,
    ]


def get_tools(settings=None):
    """Return local tools plus any tools loaded from configured MCP servers."""
    tools = get_local_tools()
    if settings is not None:
        tools.extend(load_mcp_tools(settings))
    return tools
