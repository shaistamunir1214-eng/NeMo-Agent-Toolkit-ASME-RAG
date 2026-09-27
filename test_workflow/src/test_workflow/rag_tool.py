# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path
from typing import Any

from pydantic import Field

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

DEFAULT_PERSIST_DIR = Path("data/asme_chroma")
DEFAULT_PDF_PATH = Path("ASME B31.8-2010 .pdf")


def get_or_build_vectorstore(
    pdf_path: Path = DEFAULT_PDF_PATH,
    persist_dir: Path = DEFAULT_PERSIST_DIR,
) -> Any:
    """Initializes or loads the persistent Chroma vector store for ASME B31.8-2010."""
    import chromadb
    from langchain_community.vectorstores import Chroma
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import pypdf
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    embedder = NVIDIAEmbeddings(
        model="nvidia/nemotron-3-embed-1b",
        api_key=api_key,
        base_url=base_url,
    )

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection_name = "asme_b31_8"

    existing_collections = [c.name for c in client.list_collections()]
    if collection_name in existing_collections:
        col = client.get_collection(collection_name)
        if col.count() > 0:
            logger.info("Loaded existing ASME B31.8 index with %d chunks.", col.count())
            return Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=embedder,
            )

    logger.info("Building new ASME B31.8 index from '%s'...", pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"ASME standard PDF not found at {pdf_path.resolve()}")

    reader = pypdf.PdfReader(str(pdf_path))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    docs = []
    metadatas = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(chunk)
            metadatas.append({"source": "ASME B31.8-2010", "page": idx + 1})

    logger.info("Extracted %d chunks from %d pages. Generating embeddings...", len(docs), len(reader.pages))

    # Batch insert to avoid payload limits
    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedder,
    )

    batch_size = 50
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i : i + batch_size]
        batch_metas = metadatas[i : i + batch_size]
        vectorstore.add_texts(texts=batch_docs, metadatas=batch_metas)
        logger.info("Indexed %d/%d chunks.", min(i + batch_size, len(docs)), len(docs))

    logger.info("Successfully built and persisted ASME B31.8 vector store to '%s'.", persist_dir)
    return vectorstore


class ASMEB318RAGConfig(FunctionBaseConfig, name="asme_b31_8_search"):
    """
    Search tool for ASME B31.8-2010 'Gas Transmission and Distribution Piping Systems'.
    """
    top_k: int = Field(
        default=5,
        description="Number of relevant standard excerpts to retrieve.",
    )
    pdf_path: str = Field(
        default="ASME B31.8-2010 .pdf",
        description="Path to the ASME B31.8 PDF document.",
    )
    persist_dir: str = Field(
        default="data/asme_chroma",
        description="Directory for the persistent Chroma vector store.",
    )


@register_function(config_type=ASMEB318RAGConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def asme_b31_8_search_tool(config: ASMEB318RAGConfig, builder: Builder):
    """
    Registers the ASME B31.8 RAG search tool with NeMo Agent Toolkit.
    """
    vectorstore = get_or_build_vectorstore(
        pdf_path=Path(config.pdf_path),
        persist_dir=Path(config.persist_dir),
    )

    async def search_asme(query: str) -> str:
        """
        Searches the ASME B31.8-2010 standard for rules, formulas, summaries, tables, or requirements.

        Args:
            query (str): The search query or technical topic (e.g., 'pipe design formula', 'Class 1 location factor', 'leak tests').

        Returns:
            str: Relevant excerpts from ASME B31.8-2010 with page numbers and citations.
        """
        results = vectorstore.similarity_search(query, k=config.top_k)
        if not results:
            return "No matching sections found in ASME B31.8-2010 standard."

        formatted_parts = []
        for i, doc in enumerate(results, 1):
            page_num = doc.metadata.get("page", "Unknown")
            source = doc.metadata.get("source", "ASME B31.8-2010")
            formatted_parts.append(
                f"--- [Excerpt {i} | Source: {source} | Page: {page_num}] ---\n{doc.page_content.strip()}"
            )

        return "\n\n".join(formatted_parts)

    yield FunctionInfo.from_fn(
        search_asme,
        description=(
            "Searches the ASME B31.8-2010 standard ('Gas Transmission and Distribution Piping Systems') "
            "for design criteria, formulas, piping materials, testing requirements, safety standards, "
            "operating pressures, and definitions. Input should be a specific question or topic."
        ),
    )
