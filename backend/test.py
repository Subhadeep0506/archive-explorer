from dotenv import load_dotenv

load_dotenv()
from src.core.vectorstore import VectorStoreFactory
from src.core.embedding import EmbeddingFactory
from src.lib.langsearch import LangSearchClient


async def main():
    embedding = EmbeddingFactory.build_embedding_model()
    vectorstore = VectorStoreFactory.build_vector_store(embedding_model=embedding)

    docs = vectorstore.similarity_search(
        "What is the main contribution of the paper?", k=10
    )
    langsearch = await LangSearchClient.rerank_docs(
        query="What is the main contribution of the paper?", documents=docs, top_n=4
    )
    print(langsearch)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
