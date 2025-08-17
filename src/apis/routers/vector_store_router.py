from src.config.vector_store import vector_store_crud
from typing import List
from fastapi import APIRouter, Query, UploadFile, File
from pydantic import Field, BaseModel
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import tempfile
import shutil
from uuid import uuid4

router = APIRouter(prefix="/vector-store", tags=["Vector Store"])


@router.get("/get-documents")
async def get_documents():
    documents = await vector_store_crud.get_documents()
    return [doc.__dict__ for doc in documents]


@router.get("/search")
async def search(query: str):
    documents = await vector_store_crud.search(query)
    return [doc.__dict__ for doc in documents]


class FileIngressResponse(BaseModel):
    file_path: str = Field(..., title="Path to the processed file")
    chunks_count: int = Field(..., title="Number of chunks created")
    success: bool = Field(..., title="Whether the ingestion was successful")
    message: str = Field(
        "File processed and indexed successfully", title="Status message"
    )


@router.post("/add-documents", response_model=List[FileIngressResponse])
async def add_documents(
    files: List[UploadFile] = File(...),
):
    responses = []
    
    for file in files:
        try:
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, file.filename)

            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            if file.filename.endswith(".pdf"):
                loader = PyMuPDFLoader(temp_file_path)
            elif file.filename.endswith(".docx"):
                loader = UnstructuredWordDocumentLoader(temp_file_path)
            elif file.filename.endswith(".txt"):
                loader = TextLoader(temp_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file.filename}")

            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)

            for chunk in chunks:
                chunk.metadata.update({'source_file': file.filename})

            ids = [str(uuid4()) for _ in chunks]
            await vector_store_crud.add_documents(chunks, ids=ids)

            shutil.rmtree(temp_dir)
            chunks_count = len(chunks)

            responses.append(
                FileIngressResponse(
                    file_path=file.filename,
                    chunks_count=chunks_count,
                    success=True,
                    message=f"File processed and indexed successfully. Created {chunks_count} chunks.",
                )
            )

        except Exception as e:
            responses.append(
                FileIngressResponse(
                    file_path=file.filename if file else "unknown",
                    chunks_count=0,
                    success=False,
                    message=f"Error processing file: {str(e)}",
                )
            )
    
    return responses


@router.delete("/delete-documents")
async def delete_documents(filenames: List[str] = Query(None)):
    document_data = await vector_store_crud.get_documents()
    
    if not filenames:
        # If no filenames provided, delete all documents
        document_ids = [doc.id for doc in document_data]
        await vector_store_crud.delete_documents(ids=document_ids)
        return {"message": f"Deleted all {len(document_ids)} documents"}
    
    # Filter documents by source matching the provided filenames
    docs_to_delete = []
    for doc in document_data:
        if "source" in doc.metadata and doc.metadata["source"] in filenames:
            docs_to_delete.append(doc)
    
    if not docs_to_delete:
        return {"message": "No matching documents found to delete"}
    
    # Extract IDs of documents to delete
    delete_ids = [doc.id for doc in docs_to_delete]
    
    await vector_store_crud.delete_documents(ids=delete_ids)
    return {
        "message": f"Deleted {len(delete_ids)} chunks from files: {list(set([doc.metadata.get('source') for doc in docs_to_delete]))}"
    }