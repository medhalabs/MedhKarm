"""Developer engine backed by the OpenHands agent (openhands-sdk).

The agent runs inside the sandbox's agent server with OpenHands' own tools (a persistent
terminal, a file editor with targeted edits, a task tracker). It must be paired with
`OpenHandsSandboxProvider`; any other sandbox is refused.

As with every engine, success is decided by running the task's tests ourselves afterwards.
"""

import asyncio
from typing import Any

from openhands.sdk import LLM, Agent, BaseConversation, Conversation
from openhands.sdk.conversation.response_utils import get_agent_final_response
from openhands.sdk.workspace import RemoteWorkspace
from openhands.tools.preset.default import get_default_tools

from app.features.developer_engine.engines.workspace_snapshot import changed_files, snapshot
from app.features.developer_engine.exceptions import IncompatibleSandboxError
from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.models.schemas import ModelConfig
from app.features.sandbox.interfaces import AgentServerSandbox, Sandbox

TASK_PROMPT = """You are working in the directory {workspace}. Complete this task:

{description}

When you are done, this test command must exit with code 0 when run in {workspace}:
    {test_command}

Run it yourself to check your work and fix any failures. Keep the solution small and clear.
When the tests pass, finish with a one-line summary of what you did."""


class OpenHandsEngine:
    def __init__(self, model: ModelConfig, max_iterations: int = 50) -> None:
        self._model = model
        self._max_iterations = max_iterations  # bounds the run; the SDK also stops at 1 hour

    async def run_task(self, task: DevTask, sandbox: Sandbox) -> DevResult:
        if not isinstance(sandbox, AgentServerSandbox):
            raise IncompatibleSandboxError(
                "OpenHandsEngine needs a sandbox running an OpenHands agent server "
                "(OpenHandsSandboxProvider)."
            )

        before = await snapshot(sandbox)
        summary, tokens, steps = await asyncio.to_thread(self._run_agent, task, sandbox)
        test = await sandbox.run(task.test_command)
        after = await snapshot(sandbox)

        return DevResult(
            success=test.ok,
            summary=summary or "OpenHands finished without a summary.",
            files_changed=changed_files(before, after),
            test_output=test.output[-4000:],
            steps=steps,
            total_tokens=tokens,
        )

    def _run_agent(self, task: DevTask, sandbox: AgentServerSandbox) -> tuple[str, int, int]:
        """Blocking: runs one OpenHands conversation to completion. Called in a thread."""
        llm = LLM(
            model=self._model.model,
            base_url=self._model.api_base,
            api_key=self._model.api_key,
            usage_id="developer",
        )
        agent = Agent(llm=llm, tools=get_default_tools(enable_browser=False))
        workspace = RemoteWorkspace(
            host=sandbox.agent_server_url, working_dir=sandbox.workspace_dir
        )
        conversation: BaseConversation = Conversation(
            agent=agent,
            workspace=workspace,
            max_iteration_per_run=self._max_iterations,
            visualizer=None,
        )
        try:
            conversation.send_message(
                TASK_PROMPT.format(
                    workspace=sandbox.workspace_dir,
                    description=task.description,
                    test_command=task.test_command,
                )
            )
            conversation.run()
            events: list[Any] = list(conversation.state.events)
            summary = get_agent_final_response(events)
            usage = conversation.conversation_stats.get_combined_metrics().accumulated_token_usage
            tokens = (usage.prompt_tokens + usage.completion_tokens) if usage else 0
            steps = sum(1 for event in events if type(event).__name__ == "ActionEvent")
            return summary.strip(), tokens, steps
        finally:
            conversation.close()
