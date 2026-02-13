import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


class LLMFactory:
    @staticmethod
    def build_llm(
        cls, model_name: str, max_tokens: int = 2048, temperature: float = 0.7
    ):
        try:
            if "gemini" in model_name.lower():
                llm = ChatGoogleGenerativeAI(
                    model=model_name, google_api_key=os.getenv("GEMINI_API_KEY")
                )
            else:
                llm = ChatGroq(
                    model=model_name,
                    api_key=os.getenv("GROQ_API_KEY"),
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            return llm
        except Exception as e:
            print(f"Error building LLM: {e}")
            raise e
