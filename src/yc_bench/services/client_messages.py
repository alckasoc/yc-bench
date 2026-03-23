"""Client message templates for task listings.

Each client sends a message with their task listing. RAT clients' messages
contain subtle red flags mixed with reassuring language. Good clients'
messages are straightforward. The agent must read and weigh competing
signals to assess risk.

Deterministic per seed via seeded RNG.
"""
from __future__ import annotations

# RAT client messages — contain red flags buried in positive language
RAT_TEMPLATES = [
    "Excited to work with a new team on this. We've gone through a couple of vendors previously — the project scope evolved as we learned more about the problem space. We're confident the requirements are locked down now. Budget is firm and we pay promptly on delivery.",
    "This is a high-priority initiative for our leadership team. We had an internal team working on it but pivoted our strategy midway. Looking for external expertise to pick up where they left off. Timeline is aggressive but negotiable if you show early progress.",
    "Great opportunity to build a long-term partnership. Fair warning — our stakeholders are very hands-on and may request adjustments as the project develops. That said, the core deliverables are well-defined and the compensation reflects the complexity.",
    "We're restructuring our tech organization and need to move fast on this. Previous contractor had to step away due to capacity issues. The work is well-scoped — just needs the right team to execute. We value quality over speed.",
    "Our board has made this a top priority for the quarter. Requirements have been refined through several rounds of internal review, though our product team may want to iterate on specifics once work begins. Reward reflects the urgency.",
    "Looking for a reliable partner after some disappointing experiences with other firms. The project is straightforward on paper, but our last two attempts stalled due to unforeseen complexity. We believe fresh eyes will make the difference.",
    "This project supports a critical business initiative. We've invested significantly in planning and are ready to move. Note that our compliance team may need to review deliverables at each milestone, which could require minor scope adjustments.",
    "We need to replace a system that's been causing issues for months. Our internal team started this work but got pulled onto other priorities. The requirements doc is thorough, though some edge cases may surface during implementation.",
    "High-visibility project with executive sponsorship. We've been iterating on the spec for a while and are finally ready to engage external help. The timeline is tight because we've already committed to a launch date with our clients.",
    "This is the third time we're putting this project out — not because of the work itself, but because of internal reorganizations. We now have clear ownership and stable requirements. Compensation has been increased to reflect the urgency.",
    "We're a fast-moving team that values adaptability. The core requirements are solid but we like to stay agile and adjust based on early findings. Previous partners appreciated our collaborative approach — we're very involved in the process.",
    "Strategic initiative backed by new funding. We have a detailed spec but our CTO likes to stay involved and may suggest architectural changes during development. The upside is strong executive support and quick decision-making.",
]

# Good client messages — clean, straightforward, no red flags
GOOD_TEMPLATES = [
    "Standard project with clear requirements. We've done similar work with other teams successfully. Timeline is comfortable and requirements are final. Looking forward to a smooth collaboration.",
    "Well-scoped initiative with a dedicated project manager on our side. Requirements have been reviewed and approved. No expected changes. We have a good track record of on-time payments.",
    "Straightforward project for our team. We've used this exact spec with two previous vendors who delivered successfully. Happy to share references. Timeline includes buffer for review cycles.",
    "This project is part of our annual roadmap — well-planned and budgeted. Requirements are stable and have been validated with our end users. We're easy to work with and responsive to questions.",
    "Clean project with minimal dependencies. Our engineering team has already prototyped the approach, so the requirements are grounded in reality. No surprises expected. Standard payment terms on completion.",
    "We've been running this type of project quarterly for two years. The process is well-established and requirements don't change. Quick onboarding, clear success criteria, reliable payment.",
    "Simple, well-defined project. Our team is experienced and low-maintenance — we'll provide clear requirements upfront and stay out of your way. Payment on milestone completion, no disputes.",
    "Routine project for our department. The spec has been through three rounds of internal review. We pride ourselves on being good clients — clear communication, no scope changes, prompt payment.",
    "This project has full organizational buy-in and a realistic timeline. We've done the groundwork internally and just need execution support. Requirements are final and the success criteria are measurable.",
    "Established project template that we run regularly. No experimentation needed — we know exactly what we want. Fast turnaround expected given the clear scope. We pay within 5 business days of delivery.",
    "Our team has deep domain expertise and will provide excellent documentation and support during the project. Requirements are comprehensive and tested. We value long-term relationships with reliable partners.",
    "Budget-approved project with sign-off from all stakeholders. No risk of cancellation or scope change. We've specifically allocated buffer time in the schedule for review and feedback cycles.",
]


def generate_client_message(rng, is_rat: bool) -> str:
    """Generate a client message. RAT clients get red-flag templates."""
    templates = RAT_TEMPLATES if is_rat else GOOD_TEMPLATES
    return rng.choice(templates)
