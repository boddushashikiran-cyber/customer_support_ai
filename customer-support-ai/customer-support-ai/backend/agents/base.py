"""
Shared base class for all specialized agents.
Each agent = a system prompt (its persona/scope) + the common
retrieve-context-then-generate flow.
"""
from rag import retriever
from llm import chat_completion


class BaseAgent:
    name = "base"
    system_prompt = "You are a helpful customer support assistant."

    def handle(self, query: str, history: list = None) -> dict:
        chunks = retriever.retrieve(query, top_k=4)
        context = retriever.format_context(chunks)

        user_prompt = (
            f"Company knowledge base context:\n{context}\n\n"
            f"Customer question: {query}\n\n"
            f"Answer using the context above when relevant. If the context "
            f"doesn't cover it, say so honestly and offer to escalate."
        )

        reply = chat_completion(self.system_prompt, user_prompt, history=history)
        return {
            "agent": self.name,
            "reply": reply,
            "sources": [c["source"] for c in chunks],
        }
