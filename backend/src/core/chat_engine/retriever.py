from langchain.tools import tool
from ..embedding import EmbeddingFactory
from ..vectorstore import VectorStoreFactory


@tool("retriever", return_direct=True)
def retriever(query: str, top_k: int = 5, paper_id: str = None):
    vectorstore = VectorStoreFactory.build_vector_store(
        embedding_model=EmbeddingFactory.build_embedding_model(
            "embed-multilingual-v3.0"
        )
    )
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": top_k, "filter": {"paper_id": paper_id}}
    )
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])
