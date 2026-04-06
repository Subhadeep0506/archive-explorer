from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from ..logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def load_pdf_content(pdf_url: str) -> str:
    """Load PDF content from a given URL."""
    try:
        loader = PyMuPDF4LLMLoader(file_path=pdf_url)
        content = ""
        async for doc in loader.alazy_load():
            content += doc.page_content + "\n\n"
        return content
    except Exception as e:
        logger.error(f"Error loading PDF content: {e}")
        raise e
