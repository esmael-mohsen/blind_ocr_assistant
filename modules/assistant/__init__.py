"""Assistant orchestration package exports."""

from modules.assistant.reading_controller import ReadingController
from modules.assistant.reading_controller import __all__ as _reading_exports


def __getattr__(name: str):
    if name == "AssistantWorkflow":
        from modules.assistant.workflow import AssistantWorkflow

        return AssistantWorkflow
    if name == "DialogueManager":
        from modules.assistant.dialogue_manager import DialogueManager

        return DialogueManager
    if name in {
        "AssistantSession",
        "AssistantState",
        "ReadWorkflowResult",
        "SpokenStatus",
        "TranslationWorkflowResult",
        "WorkflowErrorCode",
        "WorkflowFailure",
        "WorkflowMode",
        "WorkflowRequest",
        "WorkflowStatus",
    }:
        from modules.assistant import state

        return getattr(state, name)
    if name == "TranslationController":
        from modules.assistant.translation_controller import TranslationController

        return TranslationController
    raise AttributeError(name)

__all__ = [
    "AssistantSession",
    "AssistantState",
    "AssistantWorkflow",
    "DialogueManager",
    "ReadingController",
    "ReadWorkflowResult",
    "SpokenStatus",
    "TranslationController",
    "TranslationWorkflowResult",
    "WorkflowErrorCode",
    "WorkflowFailure",
    "WorkflowMode",
    "WorkflowRequest",
    "WorkflowStatus",
    *_reading_exports,
]
