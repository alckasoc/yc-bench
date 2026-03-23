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
    # Vendor churn signals
    "Excited to work with a new team on this. We've gone through a couple of vendors previously — the project scope evolved as we learned more about the problem space. We're confident the requirements are locked down now. Budget is firm and we pay promptly on delivery.",
    "Looking for a reliable partner after some disappointing experiences with other firms. The project is straightforward on paper, but our last two attempts stalled due to unforeseen complexity. We believe fresh eyes will make the difference.",
    "This is the third time we're putting this project out — not because of the work itself, but because of internal reorganizations. We now have clear ownership and stable requirements. Compensation has been increased to reflect the urgency.",
    "We've worked with several teams on similar initiatives. While those engagements taught us a lot, we're looking for someone who can really own the delivery end-to-end. Our previous partners found the requirements more nuanced than expected.",
    "After parting ways with our last development partner, we're eager to find the right fit. The project itself isn't complicated — it was really a personnel mismatch. We've since clarified our expectations and are ready to move forward.",

    # Scope change signals
    "Great opportunity to build a long-term partnership. Fair warning — our stakeholders are very hands-on and may request adjustments as the project develops. That said, the core deliverables are well-defined and the compensation reflects the complexity.",
    "Our board has made this a top priority for the quarter. Requirements have been refined through several rounds of internal review, though our product team may want to iterate on specifics once work begins. Reward reflects the urgency.",
    "This project supports a critical business initiative. We've invested significantly in planning and are ready to move. Note that our compliance team may need to review deliverables at each milestone, which could require minor scope adjustments.",
    "We're a fast-moving team that values adaptability. The core requirements are solid but we like to stay agile and adjust based on early findings. Previous partners appreciated our collaborative approach — we're very involved in the process.",
    "Strategic initiative backed by new funding. We have a detailed spec but our CTO likes to stay involved and may suggest architectural changes during development. The upside is strong executive support and quick decision-making.",
    "The requirements are 90% locked down. There are a few areas where we're still gathering user feedback, but nothing that should significantly impact the core work. We'll finalize those details in the first week.",
    "We operate in a fast-changing market, so while the technical spec is solid, business priorities could shift the emphasis between deliverables. We'll keep you informed of any pivots and adjust timelines accordingly.",

    # Internal instability signals
    "This is a high-priority initiative for our leadership team. We had an internal team working on it but pivoted our strategy midway. Looking for external expertise to pick up where they left off. Timeline is aggressive but negotiable if you show early progress.",
    "We're restructuring our tech organization and need to move fast on this. Previous contractor had to step away due to capacity issues. The work is well-scoped — just needs the right team to execute. We value quality over speed.",
    "We need to replace a system that's been causing issues for months. Our internal team started this work but got pulled onto other priorities. The requirements doc is thorough, though some edge cases may surface during implementation.",
    "High-visibility project with executive sponsorship. We've been iterating on the spec for a while and are finally ready to engage external help. The timeline is tight because we've already committed to a launch date with our clients.",
    "Our VP of Engineering just joined three months ago and is reshaping our technical direction. This project is part of their new vision. Requirements may evolve as the broader strategy crystallizes, but the core deliverable is clear.",
    "We recently merged two product lines and need to unify the underlying systems. The scope is well-understood at a high level, but some integration details will only become clear once work begins. We're prepared for reasonable adjustments.",

    # Subtle pressure / urgency signals
    "This has been on our backlog for a while and leadership is pushing hard to get it done this quarter. We need someone who can move fast and handle ambiguity. The spec covers the main cases — we'll work through edge cases together as they come up.",
    "Our investors are expecting a demo of this capability next quarter. We've scoped it carefully but the timeline doesn't leave much room for iteration. Need a team that can deliver on the first pass with minimal back-and-forth.",
    "We're under some time pressure due to a regulatory deadline. The core work is well-defined, but there may be last-minute compliance requirements that could affect the final deliverable. We'll compensate for any additional effort.",
    "Critical project that's been escalated to C-suite visibility. Previous timeline was more relaxed but we've had to accelerate. Requirements are solid — we just need execution speed. Prepared to pay a premium for reliable delivery.",

    # Mixed signals (positive framing of negatives)
    "We pride ourselves on being deeply collaborative partners. Our team will be closely involved throughout — reviewing intermediate outputs, suggesting improvements, and ensuring alignment with our evolving vision. This hands-on approach has worked well for us in the past.",
    "Exciting greenfield project with significant strategic importance. We're still exploring the solution space, so the exact approach may shift as we learn more. That said, the problem statement is crystal clear and the budget is generous.",
    "We've learned a lot from previous attempts at this project and have significantly refined our requirements. While we can't guarantee zero changes, we're much better positioned now. The team that takes this on will benefit from all our prior learnings.",
    "Fast-growing startup environment — things move quickly here. The spec reflects our current understanding but we ship and iterate rapidly. Looking for a partner who thrives in dynamic settings and can adapt to changing priorities without losing momentum.",
    "This project has strong organizational support but involves multiple stakeholder groups. We've aligned on the high-level goals, though each group may have specific requirements that emerge during implementation. We see this as collaborative refinement, not scope creep.",
    "Our client base is growing faster than expected, which is driving urgency on this project. The requirements are based on current scale but we may need to adjust targets upward during development. Happy to discuss timeline implications as they arise.",
    "We believe in transparent partnerships. To be upfront: this project has been attempted before and didn't reach completion. However, we've since overhauled our internal processes and believe the issues were on our side, not the technical work itself.",
    "The project touches several systems owned by different teams. While the core scope is well-defined, integration points may require some negotiation as we discover dependencies. Our project manager will help coordinate across teams.",
]

# Good client messages — clean, straightforward, no red flags
GOOD_TEMPLATES = [
    # Clear requirements
    "Standard project with clear requirements. We've done similar work with other teams successfully. Timeline is comfortable and requirements are final. Looking forward to a smooth collaboration.",
    "Well-scoped initiative with a dedicated project manager on our side. Requirements have been reviewed and approved by all stakeholders. No expected changes.",
    "Straightforward project for our team. We've used this exact spec with two previous vendors who delivered successfully. Happy to share references. Timeline includes buffer for review cycles.",
    "Clean project with minimal dependencies. Our engineering team has already prototyped the approach, so the requirements are grounded in reality. No surprises expected. Standard payment terms on completion.",
    "Simple, well-defined project. Our team is experienced and low-maintenance — we'll provide clear requirements upfront and stay out of your way. Payment on milestone completion.",
    "The spec has been through three rounds of internal review and a pilot phase. We know exactly what we need and the success criteria are measurable. No ambiguity in the deliverables.",

    # Established process
    "This project is part of our annual roadmap — well-planned and budgeted. Requirements are stable and have been validated with our end users. We're easy to work with and responsive to questions.",
    "We've been running this type of project quarterly for two years. The process is well-established and requirements don't change. Quick onboarding, clear success criteria, reliable payment.",
    "Established project template that we run regularly. No experimentation needed — we know exactly what we want. Fast turnaround expected given the clear scope. We pay within 5 business days of delivery.",
    "Routine engagement for our department. We've refined this process over dozens of iterations. You'll receive a comprehensive brief on day one with everything you need to get started.",
    "This is a repeating project we run each quarter with minor variations. The playbook is well-documented and our team is experienced at supporting external partners through it.",

    # Good track record
    "Our team has deep domain expertise and will provide excellent documentation and support during the project. Requirements are comprehensive and tested. We value long-term relationships with reliable partners.",
    "Budget-approved project with sign-off from all stakeholders. No risk of cancellation or scope change. We've specifically allocated buffer time in the schedule for review and feedback cycles.",
    "This project has full organizational buy-in and a realistic timeline. We've done the groundwork internally and just need execution support. Requirements are final and the success criteria are measurable.",
    "We have a strong track record of successful engagements with external partners. Our internal team will be available for questions and code reviews throughout. Expect clear, timely feedback on all deliverables.",
    "Our project management office runs a tight ship. You'll get a detailed brief, weekly check-ins, and a clear escalation path if any issues arise. We've never had a project go off-rails with this process.",

    # Supportive language
    "We're committed to making this a successful engagement. Our technical lead will be your primary point of contact and is available for daily standups if needed. All resources and access will be provisioned before day one.",
    "We understand that good work requires good support. Our team will handle all data preparation, access provisioning, and stakeholder management. Your team can focus entirely on the technical deliverables.",
    "Looking forward to a productive collaboration. We've prepared thorough documentation, a test environment, and sample data to accelerate onboarding. Previous partners were delivering within the first week.",
    "Our team is responsive and easy to work with. We pride ourselves on clear communication and prompt payment. The requirements are locked — we won't ask for changes after kickoff.",
    "We've invested in making this project as smooth as possible for our partners. Detailed spec, pre-built test harness, and a dedicated Slack channel for quick questions. We want you to succeed.",

    # Confidence signals
    "This is a well-understood problem for our industry. We've benchmarked against several approaches and know exactly what performance targets to hit. The spec reflects battle-tested requirements.",
    "Low-risk project with proven methodology. We're essentially replicating a system that works well in our US market for our European operations. Same architecture, same requirements, different data.",
    "Greenfield project but with clear precedent — we're following an approach that our parent company deployed successfully last year. The architecture decisions are already made, we just need implementation.",
    "Stable, well-funded project with a 6-month runway beyond the expected completion date. No pressure to cut corners. We'd rather get it right than get it fast.",
    "Our engineering team will be running this in production, so they have strong opinions about quality and test coverage. The requirements reflect real operational needs, not theoretical nice-to-haves.",

    # Transparency
    "Full transparency: this is a straightforward project with no hidden complexity. The budget is fair, the timeline is generous, and we won't add requirements after kickoff. We value partners who deliver reliably.",
    "We've been burned by overpromising vendors before, so we keep things simple. The scope is modest, the requirements are clear, and we pay fairly. No games, no surprises.",
    "What you see is what you get. The spec is complete, the data is ready, and our team is standing by to support. We've deliberately kept the scope tight to ensure a clean delivery.",
    "We run our external partnerships like internal projects — clear goals, regular check-ins, and honest feedback. The requirements won't change, and we expect delivery within the agreed timeline. Fair and straightforward.",
]


def generate_client_message(rng, is_rat: bool) -> str:
    """Generate a client message. RAT clients get red-flag templates."""
    templates = RAT_TEMPLATES if is_rat else GOOD_TEMPLATES
    return rng.choice(templates)
