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

from app.services.process_log import (
    ProcessLog,
    LogLevel,
    render_process_log,
)

from app.services.node_detector import (
    detect_nodes_from_exchange,
    DetectedNode,
    get_node_type_icon,
    format_detected_node_summary,
    get_node_definition_doc,
)

from app.services.agent_os_service import (
    AgentOSDocument,
    AgentOSSection,
    AgentOSSubsection,
    ClassifiedItem,
    GapItem,
    GapSeverity,
    SECTION_WEIGHTS,
    SECTION_MINIMUMS,
    SECTION_FILL_PROMPTS,
    classify_text,
    generate_agent_os_from_rant,
    create_empty_template,
    get_section_icon,
    get_subsection_icon,
    get_classification_summary,
    build_document_from_items,
    save_raw_rant,
    get_raw_rants,
    get_raw_rant_by_id,
    get_full_conversation_text,
    # Gap detection functions (Phase 2A)
    detect_gaps,
    calculate_completion_percentage,
    get_completion_color,
    generate_fill_prompts,
    process_fill_response,
    get_flash_label_sections,
    # Voice rant functions (Phase 2B)
    VOICE_SECTION_MAP,
    save_voice_rant,
    get_voice_rants,
    add_tagged_content_to_document,
    generate_agent_os_from_tagged_rant,
    get_organized_view,
)

from app.services.voice_service import (
    # Data structures
    VoiceInputMode,
    RecordingState,
    TagEvent,
    TaggedSegment,
    VoiceRantData,
    RecordingSession,
    # Transcription
    transcribe_audio,
    transcribe_audio_file,
    # Processing
    process_click_to_rant,
    process_real_time_rant,
    split_transcript_by_tags,
    # Helpers
    get_taggable_sections,
    get_section_key,
    format_duration,
    create_recording_session,
    start_recording,
    stop_recording,
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
    # Process log service
    "ProcessLog",
    "LogLevel",
    "render_process_log",
    # Node detector service
    "detect_nodes_from_exchange",
    "DetectedNode",
    "get_node_type_icon",
    "format_detected_node_summary",
    "get_node_definition_doc",
    # Agent OS service
    "AgentOSDocument",
    "AgentOSSection",
    "AgentOSSubsection",
    "ClassifiedItem",
    "GapItem",
    "GapSeverity",
    "SECTION_WEIGHTS",
    "SECTION_MINIMUMS",
    "SECTION_FILL_PROMPTS",
    "classify_text",
    "generate_agent_os_from_rant",
    "create_empty_template",
    "get_section_icon",
    "get_subsection_icon",
    "get_classification_summary",
    "build_document_from_items",
    "save_raw_rant",
    "get_raw_rants",
    "get_raw_rant_by_id",
    "get_full_conversation_text",
    # Gap detection functions (Phase 2A)
    "detect_gaps",
    "calculate_completion_percentage",
    "get_completion_color",
    "generate_fill_prompts",
    "process_fill_response",
    "get_flash_label_sections",
    # Voice rant functions (Phase 2B)
    "VOICE_SECTION_MAP",
    "save_voice_rant",
    "get_voice_rants",
    "add_tagged_content_to_document",
    "generate_agent_os_from_tagged_rant",
    "get_organized_view",
    # Voice service (Phase 2B)
    "VoiceInputMode",
    "RecordingState",
    "TagEvent",
    "TaggedSegment",
    "VoiceRantData",
    "RecordingSession",
    "transcribe_audio",
    "transcribe_audio_file",
    "process_click_to_rant",
    "process_real_time_rant",
    "split_transcript_by_tags",
    "get_taggable_sections",
    "get_section_key",
    "format_duration",
    "create_recording_session",
    "start_recording",
    "stop_recording",
]
