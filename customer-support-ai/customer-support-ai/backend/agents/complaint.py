from .base import BaseAgent


class ComplaintAgent(BaseAgent):
    name = "complaint"
    system_prompt = (
        "You are the Complaint & Escalation Agent for TechMart Electronics. "
        "The customer is likely frustrated. Acknowledge their frustration "
        "genuinely and briefly, avoid generic corporate phrasing, and focus "
        "on concrete next steps. If the issue can't be resolved directly, "
        "tell the customer it will be escalated to a human agent and a "
        "ticket will be created."
    )

    def handle(self, query: str, history: list = None) -> dict:
        result = super().handle(query, history)
        result["escalate"] = True
        return result
