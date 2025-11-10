"""
Educational prompt templates for IB Chemistry tutoring.
"""

SYSTEM_PROMPT = """You are an expert IB Chemistry tutor with deep knowledge of covalent bonding and molecular chemistry. Your role is to help IB Diploma students (ages 16-18) understand complex chemical concepts.

Guidelines:
1. Provide detailed, scientifically accurate explanations suitable for IB Diploma level
2. Use clear examples and relate concepts to real-world applications
3. Encourage critical thinking and deeper understanding
4. Use appropriate scientific terminology and notation
5. If asked about calculations, show step-by-step workings
6. Reference specific concepts from the IB Chemistry curriculum where relevant
7. ONLY answer based on the provided context from the educational materials
8. If information is not in the provided context, clearly state: "I don't have enough information in the provided materials to answer that question fully."

Remember:
- You are an educational tutor, not a homework solver
- Guide students to understanding rather than just providing answers
- Maintain an encouraging and supportive tone
"""


def create_rag_prompt(question: str, context_chunks: list) -> list:
    """
    Create a RAG prompt with context and question, including source attribution.
    
    Args:
        question: Student's question
        context_chunks: Retrieved context chunks with metadata
    
    Returns:
        List of messages for chat completion
    """
    # Combine context chunks with source metadata
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        metadata = chunk.get('metadata', {})
        doc_title = metadata.get('document_title', 'Unknown Document')
        uploader_name = metadata.get('uploader_name', 'Unknown')
        upload_date = metadata.get('upload_date', 'Unknown')
        
        # Format source header
        source_header = f"[Source {i+1}: {doc_title} (uploaded by {uploader_name} on {upload_date[:10]})]"
        source_text = chunk['text']
        
        context_parts.append(f"{source_header}\n{source_text}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    user_message = f"""Based on the following educational content:

{context}

Student Question: {question}

Please provide a clear, educational response that helps the student understand the concept. When referencing information, cite the sources using the format [Source N] (e.g., "As explained in [Source 1]...")."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    return messages


def create_fallback_prompt(question: str) -> list:
    """
    Create a fallback prompt when no context is found.
    
    Args:
        question: Student's question
    
    Returns:
        List of messages for chat completion
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""I don't have specific educational materials to reference for this question: {question}

Please let the student know that their question is outside the scope of the provided materials, but offer a brief, general guidance if appropriate for IB Chemistry level."""}
    ]
    
    return messages


def create_global_rag_prompt(context: str, question: str, num_documents: int) -> str:
    """
    Create a prompt for global chat across multiple documents.
    
    Args:
        context: Combined context from multiple documents
        question: Student's question
        num_documents: Number of documents being searched
    
    Returns:
        Formatted prompt string
    """
    global_system = """You are an expert educational AI tutor with access to multiple documents across various subjects. Your role is to synthesize information from different sources to provide comprehensive, cross-referenced answers.

Guidelines:
1. Base your answer ONLY on the provided context from the documents
2. When information comes from multiple sources, synthesize them coherently
3. Compare and contrast concepts when relevant
4. Cite sources using [Source N] format
5. If documents disagree or show different perspectives, mention this
6. Provide a well-rounded, comprehensive answer that connects ideas
7. Use appropriate academic terminology for the subject level
8. If the context doesn't contain relevant information, state this clearly
"""
    
    prompt = f"""{global_system}

Context from {num_documents} documents:

{context}

Student Question: {question}

Please provide a comprehensive answer that synthesizes information from the sources above. When referencing specific information, cite the source using [Source N] notation."""
    
    return prompt

