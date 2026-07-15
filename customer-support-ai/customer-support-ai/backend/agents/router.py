"""
Agent Router (Module 4) + Response Aggregator.

Takes a customer query, detects intent(s), invokes the matching
specialized agent(s), and combines their replies into one final response.
"""
from .intent_detection import detect_intents
from .billing import BillingAgent
from .technical import TechnicalAgent
from .product import ProductAgent
from .complaint import ComplaintAgent
from .faq import FAQAgent

AGENTS = {
    "billing": BillingAgent(),
    "technical": TechnicalAgent(),
    "product": ProductAgent(),
    "complaint": ComplaintAgent(),
    "faq": FAQAgent(),
}


def route_query(query: str, history: list = None) -> dict:
    intents = detect_intents(query)
    agent_results = []

    for intent in intents:
        agent = AGENTS.get(intent, AGENTS["faq"])
        agent_results.append(agent.handle(query, history=history))

    return aggregate_responses(intents, agent_results)


def aggregate_responses(intents: list[str], agent_results: list[dict]) -> dict:
    """Combines one or more agent replies into a single response payload."""
    if len(agent_results) == 1:
        final_text = agent_results[0]["reply"]
    else:
        # Multi-agent query (e.g. billing + technical) — label each section.
        sections = []
        for r in agent_results:
            sections.append(f"**{r['agent'].capitalize()} Agent:**\n{r['reply']}")
        final_text = "\n\n".join(sections)

    all_sources = sorted(set(s for r in agent_results for s in r["sources"]))
    should_escalate = any(r.get("escalate") for r in agent_results)

    return {
        "intents": intents,
        "agents_invoked": [r["agent"] for r in agent_results],
        "final_response": final_text,
        "sources": all_sources,
        "escalated": should_escalate,
    }
