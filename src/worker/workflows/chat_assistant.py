import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai

STOP_WORDS = {"стоп", "stop", "выход", "quit", "exit", "пока", "bye"}

ASSISTANT_INSTRUCTIONS = """Ты — дружелюбный и полезный ИИ-ассистент.
Отвечай на языке пользователя, кратко и по делу.
Помни контекст диалога и учитывай предыдущие сообщения.
Если пользователь прощается, попрощайся в ответ."""

DEFAULT_MODEL = "mistral-medium-latest"

STOP_FAREWELL = "Было приятно пообщаться! Возвращайся, если понадоблюсь. 👋"


def normalize(text: str) -> str:
    return text.strip().lower().strip(" !.,?;:")


def is_stop_command(text: str) -> bool:
    return normalize(text) in STOP_WORDS


def extract_text(user_input: workflows_mistralai.ChatInputModel | None) -> str:
    if user_input is None or not user_input.message:
        return ""
    return "".join(getattr(chunk, "text", "") for chunk in user_input.message)


@workflows.workflow.define(
    name="chat-assistant",
    workflow_display_name="Chat Assistant",
    workflow_description="Многошаговый чат-ассистент: отвечает на вопросы и помнит контекст диалога.",
)
class ChatAssistantWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(self) -> workflows_mistralai.ChatAssistantWorkflowOutput:
        agent = workflows_mistralai.Agent(
            model=DEFAULT_MODEL,
            name="chat-assistant",
            description="Multiturn chat assistant",
            instructions=ASSISTANT_INSTRUCTIONS,
        )
        session = workflows_mistralai.RemoteSession(stream=True)

        await workflows_mistralai.send_assistant_message(
            "Привет! Я ИИ-ассистент. Спроси что-нибудь — а чтобы закончить диалог, напиши «стоп»."
        )

        while True:
            user_input = await self.wait_for_input(
                workflows_mistralai.ChatInput("Напишите сообщение…")
            )
            text = extract_text(user_input)
            if not text.strip():
                continue
            if is_stop_command(text):
                return workflows_mistralai.ChatAssistantWorkflowOutput(
                    content=[workflows_mistralai.TextOutput(text=STOP_FAREWELL)]
                )
            await workflows_mistralai.Runner.run(agent=agent, inputs=text, session=session)
