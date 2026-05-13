from ..agent_state import AgentState
from ....core.logger import SingletonLogger
from ....core.llm import LLMFactory
from langgraph.config import get_stream_writer
from langchain_core.runnables import RunnableConfig
from ....config.prompts import CHAT_RESPONSE_GENERATION_SYSTEM_PROMPT


async def generate_response_node(state: AgentState, config: RunnableConfig):
    """Generates a response based on the provided state."""
    logger = SingletonLogger().get_logger()
    stream_writer = get_stream_writer()

    def truncate_content(content: str, max_chars: int = 3000) -> str:
        """Truncate content to prevent excessive context size."""
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + "\n[... content truncated ...]"

    try:
        llm = LLMFactory.build_llm(
            model_name=state["model_name"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
            request=state.get("request"),
            streaming=True,
        )
        docs_context = "\n\n".join(
            [
                f"Document {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(state.get("retrieved_docs", []))
            ]
        )
        web_context = "\n\n".join(
            [
                f"Web Source {i+1}:\n{truncate_content(doc.page_content)}"
                for i, doc in enumerate(state.get("web_search_results", []))
            ]
        )
        stream_writer(
            {
                "type": "Generate Response",
                "message": "Generating response based on retrieved documents and web search results...",
            }
        )
        messages = state.get("messages", [])
        flattened_messages = []
        for msg in messages:
            if hasattr(msg, "content"):
                content = msg.content
            else:
                content = msg

            if isinstance(content, list):
                flattened_messages.extend(content)
            elif isinstance(content, dict):
                flattened_messages.append(content)
        recent_messages = flattened_messages[-10:]
        new_messages = [
            {
                "role": "system",
                "content": CHAT_RESPONSE_GENERATION_SYSTEM_PROMPT.format(
                    retrieved_docs=docs_context, web_search_results=web_context
                ),
            },
            *recent_messages,
            {
                "role": "user",
                "content": state.get("query", ""),
            },
        ]

        # Pass config to ainvoke() to enable streaming in async context
        response = await llm.ainvoke(new_messages, config=config)
        stream_writer(
            {"type": "Generate Response", "message": "Response generation complete."}
        )
        return {
            "response": (
                response.content
                if isinstance(response.content, str)
                else str(response.text)
            ),
            "messages": [{"role": "assistant", "content": response.content}],
            "response_metadata": {
                "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                "total_tokens": response.usage_metadata.get("total_tokens", 0),
            },
        }
    except Exception as e:
        logger.exception(f"Error generating response: {e}")
        stream_writer(
            {
                "type": "Generate Response",
                "message": "An error occurred while generating the response.",
            }
        )
        return {
            "response": "Sorry, I encountered an error while generating the response. Try reducing the `top_k` parameter or changing the model.",
        }
