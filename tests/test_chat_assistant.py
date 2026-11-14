import asyncio
from unittest.mock import AsyncMock, patch

from mistralai.client.models.textchunk import TextChunk

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.workflows.core._events.event_activities import (
    _emit_task_completed,
    _emit_task_failed,
    _emit_task_in_progress,
    _emit_task_started,
)
from mistralai.workflows.testing import create_test_worker

from worker.workflows.chat_assistant import (
    STOP_FAREWELL,
    ChatAssistantWorkflow,
    extract_text,
    is_stop_command,
)

TEST_TASK_QUEUE = "test-task-queue"


def test_is_stop_command() -> None:
    assert is_stop_command("стоп")
    assert is_stop_command("  Стоп! ")
    assert is_stop_command("Stop.")
    assert is_stop_command("пока")
    assert not is_stop_command("стоп-слово")
    assert not is_stop_command("расскажи анекдот")


def test_extract_text() -> None:
    user_input = workflows_mistralai.ChatInputModel(
        message=[workflows_mistralai.TextChunk(text="при"), workflows_mistralai.TextChunk(text="вет")]
    )
    assert extract_text(user_input) == "привет"
    assert extract_text(None) == ""
    assert extract_text(workflows_mistralai.ChatInputModel(message=[])) == ""


async def test_workflow_is_registered() -> None:
    spec = workflows.get_workflow_definition(ChatAssistantWorkflow)
    assert spec.name == "chat-assistant"
    assert spec.display_name == "Chat Assistant"


async def _wait_for_pending_input(handle, attempts: int = 50) -> str:
    for _ in range(attempts):
        pending = await handle.query("__get_pending_inputs")
        tasks = pending["pending_inputs"] if isinstance(pending, dict) else pending.pending_inputs
        if tasks:
            return tasks[0]["task_id"] if isinstance(tasks[0], dict) else tasks[0].task_id
        await asyncio.sleep(0.1)
    raise AssertionError("workflow never asked for input")


async def test_chat_assistant_conversation(temporal_env) -> None:
    runner_mock = AsyncMock(return_value=[TextChunk(text="Ответ ассистента")])
    with patch.object(workflows_mistralai.Runner, "run", runner_mock):
        async with create_test_worker(
            temporal_env,
            [ChatAssistantWorkflow],
            activities=[_emit_task_started, _emit_task_in_progress, _emit_task_completed, _emit_task_failed],
        ):
            handle = await temporal_env.client.start_workflow(
                "chat-assistant",
                id="chat-assistant-test",
                task_queue=TEST_TASK_QUEUE,
            )

            async def submit(text: str) -> None:
                task_id = await _wait_for_pending_input(handle)
                await handle.execute_update(
                    "__submit_input",
                    {"task_id": task_id, "input": {"message": [{"type": "text", "text": text}]}},
                )

            await submit("привет")
            await submit("стоп")

            result = await handle.result()

    content = result["content"] if isinstance(result, dict) else result.content
    first = content[0]["text"] if isinstance(content[0], dict) else content[0].text
    assert first == STOP_FAREWELL
    assert runner_mock.await_count == 1
    assert runner_mock.await_args.kwargs["inputs"] == "привет"
