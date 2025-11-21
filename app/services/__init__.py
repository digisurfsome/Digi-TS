"""Business logic and service layer."""

from app.services.user_service import (
    get_or_create_default_user,
    list_all_users,
    create_user,
    get_user_by_id,
)

from app.services.project_service import (
    list_user_projects,
    create_project,
    get_project_by_id,
    update_project,
    delete_project,
    get_project_context,
    update_project_context,
)

from app.services.settings_service import (
    get_setting,
    set_setting,
    get_all_settings,
    set_multiple_settings,
    delete_setting,
    get_setting_as_int,
    get_setting_as_bool,
    DEFAULT_SETTINGS,
)

from app.services.chat_service import (
    get_or_create_chat_session,
    get_chat_history,
    send_chat_message,
    clear_chat_history,
    get_token_usage,
)

from app.services.node_service import (
    list_project_nodes,
    get_nodes_by_domain,
    get_draft_nodes,
    get_node_by_id,
    create_node,
    create_node_version,
    get_node_versions,
    get_node_current_version,
    update_node_status,
    update_node_basic_info,
    delete_node,
    commit_draft_node,
    summarize_rant,
    attach_summary_to_node,
    create_node_from_summary,
)

from app.services.baton_service import (
    generate_baton,
    check_auto_baton_trigger,
    get_warmed_sessions,
    switch_to_session,
)

from app.services.summary_service import (
    generate_auto_project_description,
    get_combined_description,
    update_description_mode,
)

from app.services.export_truth_doc import (
    export_truth_doc,
    get_truth_doc_filename,
    get_truth_doc_preview,
)

__all__ = [
    # User service
    "get_or_create_default_user",
    "list_all_users",
    "create_user",
    "get_user_by_id",
    # Project service
    "list_user_projects",
    "create_project",
    "get_project_by_id",
    "update_project",
    "delete_project",
    "get_project_context",
    "update_project_context",
    # Settings service
    "get_setting",
    "set_setting",
    "get_all_settings",
    "set_multiple_settings",
    "delete_setting",
    "get_setting_as_int",
    "get_setting_as_bool",
    "DEFAULT_SETTINGS",
    # Chat service
    "get_or_create_chat_session",
    "get_chat_history",
    "send_chat_message",
    "clear_chat_history",
    "get_token_usage",
    # Node service
    "list_project_nodes",
    "get_nodes_by_domain",
    "get_draft_nodes",
    "get_node_by_id",
    "create_node",
    "create_node_version",
    "get_node_versions",
    "get_node_current_version",
    "update_node_status",
    "update_node_basic_info",
    "delete_node",
    "commit_draft_node",
    "summarize_rant",
    "attach_summary_to_node",
    "create_node_from_summary",
    # Baton service
    "generate_baton",
    "check_auto_baton_trigger",
    "get_warmed_sessions",
    "switch_to_session",
    # Summary service
    "generate_auto_project_description",
    "get_combined_description",
    "update_description_mode",
    # Export service
    "export_truth_doc",
    "get_truth_doc_filename",
    "get_truth_doc_preview",
]
