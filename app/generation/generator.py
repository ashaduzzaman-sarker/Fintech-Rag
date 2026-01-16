"""
RAG answer generation with citations.
Combines retrieved context with LLM generation to produce grounded answers.
"""

from typing import List, Dict, Any, Optional
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document

from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)


class RAGGenerator:
    """
    RAG answer generator with citation tracking.
    
    Design principles:
    - Grounded: Every claim must be supported by context
    - Cited: Provide source attribution (document, page)
    - Transparent: Acknowledge limitations when context is insufficient
    """
    
    # System prompts for different versions
    SYSTEM_PROMPTS = {
        "v1": """You are a FinTech knowledge assistant. Your role is to answer questions based strictly on the provided context from internal documents.

CRITICAL RULES:
1. ONLY use information from the provided context
2. CITE sources for every claim using [Source: filename, Page: X]
3. If the context doesn't contain the answer, say "I don't have enough information to answer this question based on the available documents."
4. Be precise with financial terms, regulations, and numbers
5. If multiple documents provide conflicting information, acknowledge this
6. Use clear, professional language suitable for financial professionals

RESPONSE FORMAT:
- Start with a direct answer
- Support claims with evidence from context
- End with relevant source citations
- If uncertain, express confidence level""",
        
        "v2": """You are an expert FinTech compliance and risk analyst. Answer questions using ONLY the provided document context.

GUIDELINES:
- Accuracy is paramount: never guess or extrapolate beyond the documents
- Financial precision: be exact with numbers, dates, and regulatory references
- Citation discipline: every fact needs [Source: doc, Page: N]
- Conflict resolution: if sources disagree, present both perspectives
- Limitations: clearly state when information is incomplete

FORMAT:
1. Direct answer (2-3 sentences)
2. Supporting details with citations
3. Relevant caveats or limitations
4. Summary of sources used"""
    }
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = None,
        system_prompt_version: str = None
    ):
        """
        Initialize RAG generator.
        
        Args:
            model_name: OpenAI model name
            temperature: Generation temperature
            system_prompt_version: System prompt version
        """
        
        self.model_name = model_name or settings.openai_model
        self.temperature = temperature if temperature is not None else settings.openai_temperature
        self.system_prompt_version = system_prompt_version or settings.rag_system_prompt_version
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=settings.openai_api_key,
            max_tokens=settings.openai_max_tokens
        )
        
        # Build prompt template
        self.prompt = self._build_prompt_template()
        
        # Stats
        self.stats = {
            "total_generations": 0,
            "avg_context_length": 0,
            "avg_response_length": 0
        }
        
        logger.info(
            "RAG generator initialized",
            extra={
                "model": self.model_name,
                "temperature": self.temperature,
                "prompt_version": self.system_prompt_version
            }
        )
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build prompt template with system and user messages."""
        
        system_prompt = self.SYSTEM_PROMPTS.get(
            self.system_prompt_version,
            self.SYSTEM_PROMPTS["v1"]
        )
        
        template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Context from documents:
{context}

Question: {question}

Provide a comprehensive answer with proper citations.""")
        ])
        
        return template
    
    def generate(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        max_context_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate answer with citations.
        
        Args:
            question: User question
            context_documents: Retrieved and reranked documents
            max_context_length: Maximum context length in tokens
            
        Returns:
            Dict with answer, citations, and metadata
        """
        
        if not context_documents:
            logger.warning("No context documents provided")
            return {
                "answer": "I don't have any relevant documents to answer this question.",
                "citations": [],
                "context_used": []
            }
        
        logger.info(
            f"Generating answer for: '{question[:50]}...'",
            extra={"num_context_docs": len(context_documents)}
        )
        
        # Build context string
        max_length = max_context_length or settings.rag_context_window
        context_str = self._build_context_string(
            context_documents,
            max_length=max_length
        )
        
        # Generate answer
        try:
            # Format prompt
            messages = self.prompt.format_messages(
                context=context_str,
                question=question
            )
            
            # Call LLM
            response = self.llm.invoke(messages)
            answer = response.content
            
            # Extract citations from answer
            citations = self._extract_citations(answer, context_documents)
            
            # Update stats
            self.stats["total_generations"] += 1
            self.stats["avg_context_length"] = (
                (self.stats["avg_context_length"] * (self.stats["total_generations"] - 1) + len(context_str))
                / self.stats["total_generations"]
            )
            self.stats["avg_response_length"] = (
                (self.stats["avg_response_length"] * (self.stats["total_generations"] - 1) + len(answer))
                / self.stats["total_generations"]
            )
            
            result = {
                "answer": answer,
                "citations": citations,
                "context_used": [
                    {
                        "source": doc.get("metadata", {}).get("source", "unknown"),
                        "page": doc.get("metadata", {}).get("page", "N/A"),
                        "score": doc.get("rerank_score", doc.get("rrf_score", 0))
                    }
                    for doc in context_documents
                ],
                "model": self.model_name,
                "temperature": self.temperature
            }
            
            logger.info(
                "Answer generated successfully",
                extra={
                    "answer_length": len(answer),
                    "num_citations": len(citations)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return {
                "answer": "I encountered an error generating the answer. Please try again.",
                "citations": [],
                "context_used": [],
                "error": str(e)
            }
    
    def _build_context_string(
        self,
        documents: List[Dict[str, Any]],
        max_length: int
    ) -> str:
        """
        Build context string from documents.
        
        Args:
            documents: Retrieved documents
            max_length: Maximum length in characters (rough proxy for tokens)
            
        Returns:
            Formatted context string
        """
        
        context_parts = []
        total_length = 0
        
        for idx, doc in enumerate(documents, 1):
            # Extract document info
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown")
            page = metadata.get("page", "N/A")
            
            # Format document
            doc_str = f"""
[Document {idx}]
Source: {source}
Page: {page}
Content: {content}

"""
            
            # Check length
            if total_length + len(doc_str) > max_length:
                logger.debug(
                    f"Context limit reached at document {idx}/{len(documents)}"
                )
                break
            
            context_parts.append(doc_str)
            total_length += len(doc_str)
        
        return "\n".join(context_parts)
    
    def _extract_citations(
        self,
        answer: str,
        context_documents: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Extract citation references from answer.
        
        Looks for patterns like:
        - [Source: filename, Page: X]
        - (Source: filename)
        
        Args:
            answer: Generated answer
            context_documents: Context documents
            
        Returns:
            List of citations
        """
        
        import re
        
        citations = []
        
        # Pattern 1: [Source: ..., Page: ...]
        pattern1 = r'\[Source:\s*([^,]+),\s*Page:\s*([^\]]+)\]'
        matches1 = re.findall(pattern1, answer)
        
        for source, page in matches1:
            citations.append({
                "source": source.strip(),
                "page": page.strip(),
                "type": "explicit"
            })
        
        # Pattern 2: (Source: ...)
        pattern2 = r'\(Source:\s*([^)]+)\)'
        matches2 = re.findall(pattern2, answer)
        
        for source in matches2:
            citations.append({
                "source": source.strip(),
                "page": "N/A",
                "type": "explicit"
            })
        
        # If no explicit citations found, infer from context usage
        if not citations:
            # Assume top documents were used
            for doc in context_documents[:3]:
                metadata = doc.get("metadata", {})
                citations.append({
                    "source": metadata.get("source", "Unknown"),
                    "page": str(metadata.get("page", "N/A")),
                    "type": "inferred"
                })
        
        return citations
    
    def generate_with_confidence(
        self,
        question: str,
        context_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate answer with confidence scoring.
        
        Confidence is based on:
        - Rerank scores of context documents
        - Number of supporting documents
        - Presence of explicit citations
        
        Args:
            question: User question
            context_documents: Context documents
            
        Returns:
            Result with confidence score (0-1)
        """
        
        result = self.generate(question, context_documents)
        
        # Calculate confidence
        if not context_documents:
            confidence = 0.0
        else:
            # Average rerank score of top 3 documents
            top_scores = [
                doc.get("rerank_score", doc.get("rrf_score", 0))
                for doc in context_documents[:3]
            ]
            avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
            
            # Bonus for multiple supporting documents
            doc_bonus = min(len(context_documents) / 5.0, 0.2)
            
            # Bonus for explicit citations
            citation_bonus = 0.1 if result["citations"] else 0
            
            confidence = min(avg_score + doc_bonus + citation_bonus, 1.0)
        
        result["confidence"] = confidence
        result["confidence_level"] = (
            "high" if confidence >= 0.7 else
            "medium" if confidence >= 0.4 else
            "low"
        )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return self.stats.copy()