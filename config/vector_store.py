import os
import logging
import numpy as np
from typing import List, Optional
from dotenv import load_dotenv

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

# Pinecone imports
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

# Setup logger
logger = logging.getLogger(__name__)


def format_documents(docs: List[Document]) -> str:
    """Format retrieved documents into a single string."""
    return "\n===============\n".join([doc.page_content for doc in docs])


class Embeddings:
    """
    Class để xử lý embeddings và vector store sử dụng Google Embeddings và Pinecone
    """
    
    def __init__(self, 
                 model_name: str = 'models/embedding-001',
                 pinecone_index_name: str = 'hackathon-index',
                 dimension: int = 768,
                 namespace: str = "school_info"):
        """
        Khởi tạo Embeddings class
        
        Args:
            model_name: Tên model Google Embeddings
            pinecone_index_name: Tên index trong Pinecone
            dimension: Số chiều của embeddings
        """
        self.model_name = model_name
        self.pinecone_index_name = pinecone_index_name
        self.dimension = dimension
        self.namespace = namespace

        # Initialize Google Embeddings
        self.embedding_model = self._initialize_google_embeddings()
        
        # Initialize Pinecone
        self.pinecone_client = self._initialize_pinecone()
        self.vector_store = None

        # Document processing settings
        self.chunk_size = None
        self.chunks_overlap = None
        self.retriever = None

    def _initialize_google_embeddings(self):
        """Khởi tạo Google Embeddings"""
        try:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            return GoogleGenerativeAIEmbeddings(
                model=self.model_name,
                google_api_key=google_api_key
            )
        except Exception as e:
            logger.error(f'Failed to initialize Google Embeddings: {e}')
            raise

    def _initialize_pinecone(self):
        """Khởi tạo Pinecone client và tạo index nếu cần"""
        try:
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables")
            
            # Initialize Pinecone
            pc = Pinecone(api_key=pinecone_api_key)
            
            # Check if index exists, create if not
            existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
            
            if self.pinecone_index_name not in existing_indexes:
                logger.info(f'Creating new Pinecone index: {self.pinecone_index_name}')
                pc.create_index(
                    name=self.pinecone_index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            else:
                logger.info(f'Using existing Pinecone index: {self.pinecone_index_name}')
            
            return pc
            
        except Exception as e:
            logger.error(f'Failed to initialize Pinecone: {e}')
            raise

    def load_documents(self, 
                      directory_path: str, 
                      force_reload: bool = False, 
                      chunk_size: int = 1000, 
                      chunk_overlap: int = 200):
        """
        Load documents từ thư mục và lưu vào Pinecone
        
        Args:
            directory_path: Đường dẫn thư mục chứa documents
            force_reload: Có force reload documents không
            chunk_size: Kích thước chunk
            chunk_overlap: Overlap giữa các chunks
        """
        try:
            self.chunk_size = chunk_size
            self.chunks_overlap = chunk_overlap
            
            # Initialize vector store với namespace mặc định
            self.vector_store = PineconeVectorStore(
                index_name=self.pinecone_index_name,
                embedding=self.embedding_model,
                namespace=self.namespace
            )
            
            if force_reload:
                logger.info(f'Loading documents from {directory_path}')
                
                # Delete existing documents in namespace if force reload
                index = self.pinecone_client.Index(self.pinecone_index_name)
                
                try:
                    # Kiểm tra xem namespace có tồn tại không trước khi xóa
                    stats = index.describe_index_stats()
                    
                    # Nếu có namespace cụ thể
                    if 'namespaces' in stats and self.namespace in stats['namespaces']:
                        logger.info(f'Namespace "{self.namespace}" exists, clearing it...')
                        index.delete(delete_all=True, namespace=self.namespace)
                        logger.info(f'Cleared existing documents in namespace "{self.namespace}"')
                    else:
                        logger.info(f'Namespace "{self.namespace}" does not exist yet, will be created when adding documents')
                            
                except Exception as e:
                    logger.warning(f'Could not check/clear namespace: {e}')
                    logger.info('Continuing with document loading...')
                
                # Text splitter
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size, 
                    chunk_overlap=chunk_overlap
                )

                all_documents = []
                
                # Load documents from directory
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        logger.info(f'Loading document: {file}')
                        file_path = str(os.path.join(root, file))

                        try:
                            if file.endswith('.pdf'):
                                loaded_file = PyPDFLoader(file_path).load()
                            elif file.endswith('.docx'):
                                loaded_file = UnstructuredWordDocumentLoader(file_path).load()
                            elif file.endswith('.pptx'):
                                loaded_file = UnstructuredPowerPointLoader(file_path).load()
                            else:
                                logger.warning(f'Unsupported file type: {file}')
                                continue

                            # Split documents into chunks
                            chunks = text_splitter.split_documents(loaded_file)
                            
                            # Add metadata
                            for chunk in chunks:
                                chunk.metadata.update({
                                    'source_file': file,
                                    'file_path': file_path,
                                    'chunk_size': chunk_size,
                                    'chunk_overlap': chunk_overlap
                                })
                            
                            all_documents.extend(chunks)
                            
                        except Exception as e:
                            logger.error(f'Failed to load file {file}: {e}')
                            continue

                if all_documents:
                    # Add documents to Pinecone
                    logger.info(f'Adding {len(all_documents)} document chunks to Pinecone')
                    self.vector_store.add_documents(all_documents)
                    logger.info('Documents successfully added to Pinecone')
                    self.retriever = self.vector_store.as_retriever()
                    return self.retriever
                else:
                    logger.warning('No documents were loaded')
            else:
                logger.info('Using existing documents in Pinecone, no reload required')
                # Nếu không force reload, chỉ cần lấy retriever từ vector store
                if self.vector_store:
                    self.retriever = self.vector_store.as_retriever()
                    return self.retriever
                else:
                    logger.warning('Vector store is not initialized, please load documents first')
        except Exception as e:
            logger.error(f'Failed to load documents: {e}')
            raise

    def get_documents(self, question: str, k: int = 3) -> str:
        """
        Lấy documents liên quan đến câu hỏi
        
        Args:
            question: Câu hỏi cần tìm documents
            k: Số lượng documents trả về
            
        Returns:
            str: Formatted documents
        """
        if not self.vector_store:
            # Initialize vector store nếu chưa có
            self.vector_store = PineconeVectorStore(
                index_name=self.pinecone_index_name,
                embedding=self.embedding_model,
                namespace=self.namespace
            )
        
        try:
            # Get relevant docs directly từ Pinecone (đã ranked)
            docs = self.vector_store.similarity_search(
                query=question,
                k=k,
                namespace=self.namespace
            )
            logger.info(f'Retrieved {len(docs)} documents from Pinecone')
            
            if docs:
                formatted_docs = format_documents(docs)
                logger.info(f'Returning {len(docs)} documents')
                return formatted_docs
            else:
                logger.warning('No documents retrieved for the query')
                return ""
                
        except Exception as e:
            logger.error(f'Failed to get documents: {e}')
            raise
