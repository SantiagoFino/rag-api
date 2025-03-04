from typing import List
import re
import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split a text into overlapping chunks of approximately the specified size.

    Parameters:
        text: The text to split into chunks
        chunk_size: The target size for each chunk
        chunk_overlap: The number of characters to overlap between chunks

    Returns:
        A list of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    # Clean the text - remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            # Look for the last period, question mark, or exclamation point followed by a space
            last_sentence_break = max(
                text.rfind('. ', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end)
            )

            # If we found a good sentence break, use it
            if last_sentence_break != -1 and last_sentence_break > start + (chunk_size // 2):
                end = last_sentence_break + 1
            else:
                last_space = text.rfind(' ', start, end)
                if last_space != -1:
                    end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap if end < text_length else text_length

    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks


def chunk_document(document: dict, chunk_size: int = 500, chunk_overlap: int = 50) -> List[dict]:
    """
    Split a document into chunks

    Parameters:
        document: A dictionary containing 'document_id' and 'document_text'
        chunk_size: The target size for each chunk
        chunk_overlap: The number of characters to overlap between chunks

    Returns:
        A list of document chunks with metadata
    """
    document_id = document.get('document_id')
    document_text = document.get('document_text', '')

    if not document_id or not document_text:
        logger.warning(f"Invalid document: missing id or text")
        return []

    text_chunks = chunk_text(
        text=document_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    document_chunks = []
    for i, text in enumerate(text_chunks):
        document_chunks.append({
            'chunk_id': f"{document_id}_{i}",
            'document_id': document_id,
            'chunk_index': i,
            'text': text,
            'chunk_count': len(text_chunks)
        })

    logger.info(f"Document {document_id} split into {len(document_chunks)} chunks")
    return document_chunks
