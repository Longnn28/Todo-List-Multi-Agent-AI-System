from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.vectorstores import VectorStore
from dotenv import load_dotenv
load_dotenv()


class VectorStoreCRUD:
    def __init__(self) -> VectorStore:
        self.embeddings = HuggingFaceEmbeddings(
            model_name="Alibaba-NLP/gte-multilingual-base",
            model_kwargs={
                'device': 'cpu',  # Dùng 'cuda' nếu có GPU
                'trust_remote_code': True  # Required for Alibaba GTE models
            },
            encode_kwargs={'normalize_embeddings': True}  # Normalize embeddings
        )
        self.vector_store = PineconeVectorStore(
            index_name="school-info",
            embedding=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.3},
        )

    async def search(self, query: str, filter: Optional[Dict[str, Any]] = None):
        return await self.retriever.ainvoke(query, filter=filter)

    async def add_documents(self, documents: List[Document], ids: List[str]):
        await self.vector_store.aadd_documents(documents, ids=ids)

    async def get_documents(self, filter: Optional[Dict[str, Any]] = None):
        return await self.vector_store.asimilarity_search("", k=10000, filter=filter)

    async def delete_documents(self, ids: List[str]):
        await self.vector_store.adelete(ids=ids)