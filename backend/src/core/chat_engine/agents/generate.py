from ..agent_state import AgentState
from ....core.logger import SingletonLogger
from ....core.llm import LLMFactory
from langgraph.config import get_stream_writer


async def generate_response_node(state: AgentState):
    """Generates a response based on the provided state."""
    logger = SingletonLogger().get_logger()
    stream_writer = get_stream_writer()
    try:
        llm = LLMFactory.build_llm(
            model_name=state["model_name"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
        )
        docs_context = "\n\n".join(
            [
                f"Document {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(state.get("retrieved_docs", []))
            ]
        )
        web_context = "\n\n".join(
            [
                f"Web Source {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(state.get("web_search_results", []))
            ]
        )
        system_prompt = """You are an assistant for helping researchers understand scientific papers. You will be provided with a question, a list of retrieved documents relevant to that question, and the results of a web crawl on the topic. Your task is to synthesize this information and generate a concise, informative response that directly answers the question. Use the previous conversation history, retrieved documents and web crawl results as evidence to support your answer, and make sure to cite specific documents or web sources when relevant.
        Retrieved documents:
        {retrieved_docs}
        Web crawl results:
        {web_search_results}
        """
        stream_writer(
            {
                "type": "Generate Response",
                "message": "Generating response based on retrieved documents and web search results...",
            }
        )
        messages = state.get("messages", [])
        messages.extend(
            [
                {
                    "role": "system",
                    "content": system_prompt.format(
                        retrieved_docs=docs_context, web_search_results=web_context
                    ),
                },
                {
                    "role": "user",
                    "content": state.get("query", ""),
                },
            ]
        )
        response = await llm.ainvoke(messages)
        stream_writer(
            {"type": "Generate Response", "message": "Response generation complete."}
        )
        return {
            "response": response.content,
            "messages": [{"role": "assistant", "content": response.content}],
            "response_metadata": {
                "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                "total_tokens": response.usage_metadata.get("total_tokens", 0),
            },
        }
    except Exception as e:
        logger.exception(f"Error generating response: {e}")
        stream_writer({
            "type": "Generate Response",
            "message": "An error occurred while generating the response.",
        })
        return {
            "response": "Sorry, I encountered an error while generating the response.",
        }
