import asyncio
from typing import List, Dict, Any, Tuple, Optional
from .openrouter import query_models_parallel, query_model, query_model_stream
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL


# Specialized Council Modes / Personas Catalog
COUNCIL_PERSONAS = {
    "strict_truth": {
        "id": "strict_truth",
        "name": "Strict Truth & Logic",
        "icon": "⚖️",
        "badge": "Strict Truth Engine",
        "description": "Uncompromising accuracy, zero sycophancy, instant error debunking, and mathematical logic.",
        "system_stage1": (
            "You are a rigorous, highly disciplined, and strictly objective expert. "
            "Your top priority is uncompromising truth and technical accuracy. "
            "CRITICAL RULES:\n"
            "1. If the user's premise, statement, question, or code contains ANY mistake, misconception, invalid assumption, or false claim: "
            "CALL IT OUT IMMEDIATELY AND DIRECTLY. Do NOT sugar-coat, pander, or agree with false ideas.\n"
            "2. Zero sycophancy: Never use empty praise like 'Great question!' or apologetic filler. Be direct, authoritative, and precise.\n"
            "3. Provide the exact, correct reality with rock-solid logic and proof."
        ),
        "stage2_criteria": (
            "1. **Error Detection & Strictness**: Did the user state a misconception or error? If so, which models boldly and accurately corrected the user without sugar-coating or sycophancy? Reward models that strictly call out mistakes. Heavily penalize models that blindly agreed with false premises.\n"
            "2. **Factuality & Rigor**: Precision, completeness, absence of hallucinations.\n"
            "3. **No Fluff**: Penalize verbose filler and praise."
        ),
        "stage3_system": (
            "You are the Chairman of an elite AI Council operating in Strict Truth & Logic mode. "
            "Your task is to provide the definitive, direct, comprehensive, and authoritative answer to the user's question.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user answering their question. Do NOT act like a peer reviewer. "
            "Do NOT say 'Response A is...', 'Model 1', or 'FINAL RANKING:'.\n"
            "2. Zero sycophancy: If the user's premise has any misconception or error, call it out immediately and firmly at the very top.\n"
            "3. Deliver a complete, rock-solid technical explanation with clean Markdown headings, code snippets, or bullet points."
        )
    },
    "cybersecurity": {
        "id": "cybersecurity",
        "name": "Security & Red Team",
        "icon": "🛡️",
        "badge": "Red Team Security Audit",
        "description": "Deep vulnerability analysis, exploit vectors (OWASP Top 10, memory safety, logic flaws), and threat modeling.",
        "system_stage1": (
            "You are a world-class Principal Application Security Engineer and Offensive Red-Team Specialist. "
            "Your objective is to identify security vulnerabilities, exploit vectors, auth flaws, memory safety issues, injection risks, "
            "and architectural attack surfaces in the user's code, design, or query. "
            "Always point out risks (OWASP Top 10, CWE, CVSS impact) and provide hardened, secure-by-default production code and mitigation steps."
        ),
        "stage2_criteria": (
            "1. **Vulnerability Depth**: Which response identified the most critical security flaws, edge-case exploit vectors, and architectural blind spots?\n"
            "2. **Actionable Hardening**: Are the proposed security remediations realistic, secure-by-default, and comprehensive?\n"
            "3. **Technical Precision**: Zero false sense of security; penalize hand-wavy or incomplete security advice."
        ),
        "stage3_system": (
            "You are the Chairman of the AI Security Council (Red Team / AppSec Lead). "
            "Synthesize the candidate security evaluations into an authoritative Security Assessment and Hardening Guide.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user. Do NOT mention 'Response A' or 'FINAL RANKING:'.\n"
            "2. Clearly identify all security vulnerabilities, threat vectors, and provide hardened code fixes.\n"
            "3. Structure with: 🚨 Vulnerability Breakdown, 🎯 Attack Vectors / Impact, 🛡️ Hardened Remediation & Code."
        )
    },
    "code_architect": {
        "id": "code_architect",
        "name": "Principal Architect",
        "icon": "💻",
        "badge": "System Architecture & Scale",
        "description": "High-scale system design, Big-O complexity, architectural trade-offs, clean code, and production reliability.",
        "system_stage1": (
            "You are a Principal Software Architect and Staff Engineer at a hyper-scale tech company. "
            "Evaluate everything through the lens of high scalability, concurrency, low latency, Big-O algorithmic efficiency, "
            "maintainability, clean modular design patterns, fault tolerance, and production trade-offs. "
            "Provide production-grade code, clear architectural diagrams/flow, and concrete trade-off matrices."
        ),
        "stage2_criteria": (
            "1. **Architectural Excellence**: Which response proposes the cleanest, most scalable, and maintainable engineering design?\n"
            "2. **Algorithmic & System Rigor**: Big-O analysis, concurrency handling, bottleneck avoidance.\n"
            "3. **Pragmatism & Trade-offs**: Concrete evaluation of latency vs throughput, consistency vs availability."
        ),
        "stage3_system": (
            "You are the Chairman of the Principal Architecture Council. "
            "Synthesize the candidate engineering designs into a definitive Architectural Decision Record (ADR) and implementation guide.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user. Do NOT mention 'Response A' or 'FINAL RANKING:'.\n"
            "2. Provide the definitive architecture, design patterns, clean code implementation, and trade-off analysis.\n"
            "3. Structure with: 🏛️ Architecture & Core Strategy, ⚙️ Implementation & Code, 📊 Trade-Offs & Complexity."
        )
    },
    "scientific_proof": {
        "id": "scientific_proof",
        "name": "Scientific & Math Rigor",
        "icon": "🔬",
        "badge": "Formal Scientific Rigor",
        "description": "Formal proofs, mathematical precision, empirical citations, edge cases, and first-principles derivation.",
        "system_stage1": (
            "You are a Distinguished Theoretical Scientist and Applied Mathematician. "
            "Approach every question with formal proof techniques, mathematical rigor, first-principles derivation, and empirical exactness. "
            "Explicitly state all axioms, lemmas, boundary conditions, edge cases, and mathematical formalisms. Avoid hand-wavy intuitive claims."
        ),
        "stage2_criteria": (
            "1. **Mathematical & Formal Rigor**: Which response has the most mathematically sound proofs, derivations, and boundary condition checks?\n"
            "2. **Absence of Flaws**: Heavily penalize arithmetic mistakes, flawed proofs, or unsupported claims.\n"
            "3. **Completeness**: Exact formulas, proofs, and edge case coverage."
        ),
        "stage3_system": (
            "You are the Chairman of the Scientific & Mathematical Council. "
            "Deliver the definitive, formal, and scientifically proven answer to the user.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user. Do NOT mention 'Response A' or 'FINAL RANKING:'.\n"
            "2. Present the rigorous derivation, proofs, and final definitive theorem/result with mathematical clarity.\n"
            "3. Structure with: 📐 Formal Definition & Axioms, 🔬 Step-by-Step Derivation/Proof, 📌 Definitive Theorem & Edge Cases."
        )
    },
    "product_strategy": {
        "id": "product_strategy",
        "name": "Startup & Product Strategy",
        "icon": "🚀",
        "badge": "Product Strategy & Growth",
        "description": "Product-market fit, unit economics, go-to-market moat, growth velocity, and ruthless ROI prioritization.",
        "system_stage1": (
            "You are an Elite Venture Capitalist and Veteran Silicon Valley Product Executive. "
            "Analyze questions through the lens of Product-Market Fit (PMF), defensible moats, unit economics (LTV/CAC, margins), "
            "distribution flywheels, user retention, competitive positioning, and ruthless prioritization. Be candid, strategic, and practical."
        ),
        "stage2_criteria": (
            "1. **Strategic Depth**: Which response identified the most defensible moat, distribution advantage, and business model feasibility?\n"
            "2. **Execution Realism**: Are the proposed milestones, product loops, and go-to-market motions grounded in real market dynamics?\n"
            "3. **Ruthless Prioritization**: Clear ROI focus vs distraction."
        ),
        "stage3_system": (
            "You are the Chairman of the Executive Product & Strategy Council. "
            "Synthesize the candidate product analyses into a sharp, actionable Executive Strategy Blueprint.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user. Do NOT mention 'Response A' or 'FINAL RANKING:'.\n"
            "2. Provide an actionable strategic roadmap, competitive moat analysis, and high-impact growth strategy.\n"
            "3. Structure with: 🎯 Executive Summary & Moat, 📈 GTM & Product Loop Roadmap, ⚠️ Key Risks & Unit Economics."
        )
    },
    "devils_advocate": {
        "id": "devils_advocate",
        "name": "Devil's Advocate",
        "icon": "🧑‍⚖️",
        "badge": "Contrarian Stress-Test",
        "description": "Challenges conventional wisdom, stress-tests unexamined assumptions, and uncovers hidden risks and blind spots.",
        "system_stage1": (
            "You are a master Devil's Advocate and Contrarian Analyst. "
            "Your mission is to rigorously stress-test the user's premise, thesis, or proposed idea. "
            "Uncover hidden assumptions, failure modes, counterexamples, second-order consequences, blind spots, and worst-case scenarios. "
            "Do NOT merely disagree for the sake of it; provide brilliant, highly defensible contrarian arguments and stress tests."
        ),
        "stage2_criteria": (
            "1. **Stress-Testing Depth**: Which response uncovered the most devastating failure modes, blind spots, and counter-intuitive risks?\n"
            "2. **Argument Quality**: Are the counter-arguments logically compelling, evidence-backed, and non-trivial?\n"
            "3. **Constructive Critique**: Does it push the user towards a much stronger, antifragile conclusion?"
        ),
        "stage3_system": (
            "You are the Chairman of the Contrarian Council. "
            "Deliver the definitive, high-impact Stress-Test & Antifragile Evaluation to the user.\n"
            "STRICT INSTRUCTIONS:\n"
            "1. Speak DIRECTLY to the user. Do NOT mention 'Response A' or 'FINAL RANKING:'.\n"
            "2. Clearly lay out the critical blind spots, contrarian perspectives, and how to make the idea antifragile.\n"
            "3. Structure with: ⚡ Critical Blind Spots & Vulnerabilities, 🔍 Contrarian Arguments & Evidence, 🛡️ Antifragile Hardening Strategy."
        )
    }
}


def get_persona(persona_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve persona configuration with fallback to strict_truth."""
    if persona_id and persona_id in COUNCIL_PERSONAS:
        return COUNCIL_PERSONAS[persona_id]
    return COUNCIL_PERSONAS["strict_truth"]


async def stage1_collect_responses(
    user_query: str,
    council_models: Optional[List[str]] = None,
    persona: Optional[str] = "strict_truth"
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models using active persona.
    """
    active_models = council_models if council_models else COUNCIL_MODELS
    p_config = get_persona(persona)

    messages = [
        {"role": "system", "content": p_config["system_stage1"]},
        {"role": "user", "content": user_query}
    ]

    # Query all models in parallel
    responses = await query_models_parallel(active_models, messages)

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None and response.get('content'):
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })

    return stage1_results



async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    council_models: Optional[List[str]] = None,
    persona: Optional[str] = "strict_truth"
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses based on persona evaluation criteria.
    """
    p_config = get_persona(persona)
    responding_models = [r['model'] for r in stage1_results if r.get('response')]
    active_models = responding_models if responding_models else (council_models or COUNCIL_MODELS)

    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are an elite peer evaluator judging candidate responses for a council operating in {p_config['name']} mode.

User Inquiry: {user_query}

Candidate Responses (anonymized):
{responses_text}

Evaluation Criteria:
{p_config['stage2_criteria']}

Your task:
1. First, strictly critique each candidate response individually (strengths, fatal flaws, inaccuracies, or blind spots).
2. Then, provide the final ranking at the very end.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any text after the ranking section

Example:
Response A provided accurate, deep analysis...
Response B contained critical flaws and missed edge cases...

FINAL RANKING:
1. Response A
2. Response B

Now provide your critique and final ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(active_models, messages)

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None and response.get('content'):
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: Optional[str] = None,
    persona: Optional[str] = "strict_truth"
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes a definitive final answer according to the active persona.
    """
    active_chairman = chairman_model if chairman_model else CHAIRMAN_MODEL
    p_config = get_persona(persona)

    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_system = p_config["stage3_system"]

    chairman_user_prompt = f"""The user asked the following question:
\"\"\"{user_query}\"\"\"

---
For reference, here is the background deliberation from council models:
[Candidate Responses]
{stage1_text}

[Peer Evaluations]
{stage2_text}
---

Write the definitive, complete, and solid final answer addressing the user's question directly:"""

    messages = [
        {"role": "system", "content": chairman_system},
        {"role": "user", "content": chairman_user_prompt}
    ]

    # Query the chairman model
    response = await query_model(active_chairman, messages)

    if response is not None and response.get('content'):
        raw_text = response.get('content', '')
        # Ensure it doesn't echo a peer review evaluation
        if "FINAL RANKING:" in raw_text and raw_text.strip().startswith("Response ") and stage1_results:
            raw_text = stage1_results[0].get('response', raw_text)
        return {
            "model": active_chairman,
            "response": raw_text
        }

    # If primary chairman fails, fallback to one of the council models that responded
    for result in stage1_results:
        fallback_model = result.get('model')
        if fallback_model and fallback_model != active_chairman:
            print(f"Chairman {active_chairman} failed, falling back to {fallback_model}...")
            response = await query_model(fallback_model, messages)
            if response is not None and response.get('content'):
                return {
                    "model": f"{fallback_model} (fallback chairman)",
                    "response": response.get('content', '')
                }

    return {
        "model": active_chairman,
        "response": stage1_results[0]['response'] if stage1_results else "Error: Unable to generate final synthesis."
    }



async def stage1_collect_responses_stream(
    user_query: str,
    council_models: Optional[List[str]] = None,
    persona: Optional[str] = "strict_truth"
):
    """
    Stage 1 streaming: Query all council models in parallel and yield tokens as they arrive.
    """
    active_models = council_models if council_models else COUNCIL_MODELS
    p_config = get_persona(persona)

    messages = [
        {"role": "system", "content": p_config["system_stage1"]},
        {"role": "user", "content": user_query}
    ]

    queue = asyncio.Queue()
    accumulated = {model: [] for model in active_models}

    async def _stream_worker(model: str, delay: float):
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            async for token in query_model_stream(model, messages):
                accumulated[model].append(token)
                await queue.put({"type": "token", "model": model, "token": token})
        except Exception as e:
            print(f"Error in stage1 stream worker for {model}: {e}")
        finally:
            await queue.put({"type": "worker_done", "model": model})

    tasks = [
        asyncio.create_task(_stream_worker(model, i * 0.3))
        for i, model in enumerate(active_models)
    ]

    active_count = len(active_models)
    while active_count > 0:
        event = await queue.get()
        if event["type"] == "worker_done":
            active_count -= 1
        elif event["type"] == "token":
            yield event

    await asyncio.gather(*tasks, return_exceptions=True)

    stage1_results = []
    for model in active_models:
        content = "".join(accumulated[model]).strip()
        if content:
            stage1_results.append({
                "model": model,
                "response": content
            })

    yield {"type": "complete", "data": stage1_results}


async def stage2_collect_rankings_stream(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    council_models: Optional[List[str]] = None,
    persona: Optional[str] = "strict_truth"
):
    """
    Stage 2 streaming: Query peer evaluators in parallel and yield tokens as they arrive.
    """
    p_config = get_persona(persona)
    responding_models = [r['model'] for r in stage1_results if r.get('response')]
    active_models = responding_models if responding_models else (council_models or COUNCIL_MODELS)

    labels = [chr(65 + i) for i in range(len(stage1_results))]
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are an elite peer evaluator judging candidate responses for a council operating in {p_config['name']} mode.

User Inquiry: {user_query}

Candidate Responses (anonymized):
{responses_text}

Evaluation Criteria:
{p_config['stage2_criteria']}

Your task:
1. First, strictly critique each candidate response individually (strengths, fatal flaws, inaccuracies, or blind spots).
2. Then, provide the final ranking at the very end.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any text after the ranking section

Example:
Response A provided accurate, deep analysis...
Response B contained critical flaws and missed edge cases...

FINAL RANKING:
1. Response A
2. Response B

Now provide your critique and final ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    queue = asyncio.Queue()
    accumulated = {model: [] for model in active_models}

    async def _stream_worker(model: str, delay: float):
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            async for token in query_model_stream(model, messages):
                accumulated[model].append(token)
                await queue.put({"type": "token", "model": model, "token": token})
        except Exception as e:
            print(f"Error in stage2 stream worker for {model}: {e}")
        finally:
            await queue.put({"type": "worker_done", "model": model})

    tasks = [
        asyncio.create_task(_stream_worker(model, i * 0.3))
        for i, model in enumerate(active_models)
    ]

    active_count = len(active_models)
    while active_count > 0:
        event = await queue.get()
        if event["type"] == "worker_done":
            active_count -= 1
        elif event["type"] == "token":
            yield event

    await asyncio.gather(*tasks, return_exceptions=True)

    stage2_results = []
    for model in active_models:
        full_text = "".join(accumulated[model]).strip()
        if full_text:
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    yield {
        "type": "complete",
        "data": stage2_results,
        "label_to_model": label_to_model
    }


async def stage3_synthesize_final_stream(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: Optional[str] = None,
    persona: Optional[str] = "strict_truth"
):
    """
    Stage 3 streaming: Chairman streams tokens of the final synthesized verdict in real-time.
    """
    active_chairman = chairman_model if chairman_model else CHAIRMAN_MODEL
    p_config = get_persona(persona)

    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_system = p_config["stage3_system"]

    chairman_user_prompt = f"""The user asked the following question:
\"\"\"{user_query}\"\"\"

---
For reference, here is the background deliberation from council models:
[Candidate Responses]
{stage1_text}

[Peer Evaluations]
{stage2_text}
---

Write the definitive, complete, and solid final answer addressing the user's question directly:"""

    messages = [
        {"role": "system", "content": chairman_system},
        {"role": "user", "content": chairman_user_prompt}
    ]

    accumulated = []
    has_tokens = False

    try:
        async for token in query_model_stream(active_chairman, messages):
            has_tokens = True
            accumulated.append(token)
            yield {"type": "token", "token": token}
    except Exception as e:
        print(f"Error streaming chairman {active_chairman}: {e}")

    final_content = "".join(accumulated).strip()
    if has_tokens and final_content:
        # Sanity check: If model echoed peer critique instead of answering
        if "FINAL RANKING:" in final_content and final_content.startswith("Response ") and stage1_results:
            final_content = stage1_results[0].get('response', final_content)

        yield {
            "type": "complete",
            "data": {
                "model": active_chairman,
                "response": final_content
            }
        }
        return

    # Fallback to non-streaming or alternate model if stream was empty
    for result in stage1_results:
        fallback_model = result.get('model')
        if fallback_model and fallback_model != active_chairman:
            print(f"Chairman streaming failed, falling back to {fallback_model}...")
            try:
                async for token in query_model_stream(fallback_model, messages):
                    accumulated.append(token)
                    yield {"type": "token", "token": token}
                fallback_content = "".join(accumulated).strip()
                if fallback_content:
                    yield {
                        "type": "complete",
                        "data": {
                            "model": f"{fallback_model} (fallback chairman)",
                            "response": fallback_content
                        }
                    }
                    return
            except Exception as fb_err:
                print(f"Fallback stream failed for {fallback_model}: {fb_err}")

    yield {
        "type": "complete",
        "data": {
            "model": active_chairman,
            "response": "Error: Unable to generate final synthesis."
        }
    }



def parse_ranking_from_text(ranking_text: Optional[str]) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    if not ranking_text or not isinstance(ranking_text, str):
        return []

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking.get('ranking', '')

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


def calculate_consensus_metrics(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str],
    aggregate_rankings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate inter-model consensus, agreement percentage, and confidence metrics.

    Uses Kendall's Coefficient of Concordance (W) alongside top-pick agreement
    to produce a calibrated 0-100% consensus score and confidence tier.
    """
    if not stage2_results or not label_to_model:
        return {
            "score": 100,
            "tier": "unanimous",
            "tier_label": "Unanimous Consensus",
            "badge_icon": "🌟",
            "kendall_w": 1.0,
            "top_pick_agreement_pct": 100,
            "total_voters": 0,
            "winner_model": None,
            "winner_first_places": 0,
            "summary": "Single model / default unanimous consensus.",
            "vote_matrix": []
        }

    candidates = list(label_to_model.values())
    num_candidates = len(candidates)
    vote_matrix = []
    first_place_counts = {c: 0 for c in candidates}
    candidate_rank_sums = {c: 0 for c in candidates}
    valid_evaluators_count = 0

    for item in stage2_results:
        evaluator_model = item.get('model', 'Unknown')
        ranking_text = item.get('ranking', '')
        parsed = parse_ranking_from_text(ranking_text)

        model_rank_map = {}
        for pos, label in enumerate(parsed, start=1):
            if label in label_to_model:
                target_model = label_to_model[label]
                model_rank_map[target_model] = pos
                if pos == 1:
                    first_place_counts[target_model] = first_place_counts.get(target_model, 0) + 1

        for c in candidates:
            if c not in model_rank_map:
                model_rank_map[c] = num_candidates

        if model_rank_map:
            valid_evaluators_count += 1
            for c, pos in model_rank_map.items():
                candidate_rank_sums[c] += pos

            vote_matrix.append({
                "evaluator": evaluator_model,
                "ranks": {c: model_rank_map.get(c, num_candidates) for c in candidates}
            })

    winner_model = aggregate_rankings[0]['model'] if aggregate_rankings else (candidates[0] if candidates else None)
    winner_first_places = first_place_counts.get(winner_model, 0) if winner_model else 0
    top_pick_agreement_pct = round((winner_first_places / max(1, valid_evaluators_count)) * 100)

    M = valid_evaluators_count
    N = num_candidates

    if N <= 1 or M <= 1:
        kendall_w = 1.0
        consensus_score = 100
    elif N == 2:
        kendall_w = top_pick_agreement_pct / 100.0
        consensus_score = top_pick_agreement_pct
    else:
        R_bar = (M * (N + 1)) / 2.0
        S = sum((candidate_rank_sums[c] - R_bar) ** 2 for c in candidates)
        max_S = (M ** 2 * (N ** 3 - N)) / 12.0
        kendall_w = min(1.0, max(0.0, S / max_S)) if max_S > 0 else 1.0

        raw_score = (0.60 * kendall_w * 100.0) + (0.40 * top_pick_agreement_pct)
        consensus_score = int(round(min(100, max(0, raw_score))))

    if consensus_score >= 90:
        tier = "unanimous"
        tier_label = "Supermajority Consensus"
        badge_icon = "🌟"
    elif consensus_score >= 75:
        tier = "strong"
        tier_label = "Strong Consensus"
        badge_icon = "🟢"
    elif consensus_score >= 55:
        tier = "moderate"
        tier_label = "Moderate Agreement"
        badge_icon = "🟡"
    else:
        tier = "contested"
        tier_label = "Divided / Contested"
        badge_icon = "🔴"

    winner_short = winner_model.split('/')[1] if (winner_model and '/' in winner_model) else (winner_model or "Top Candidate")
    if tier == "unanimous":
        summary = f"Supermajority alignment: {winner_first_places} of {valid_evaluators_count} models selected {winner_short} as #1."
    elif tier == "strong":
        summary = f"Strong consensus: {winner_first_places} of {valid_evaluators_count} models ranked {winner_short} in 1st place with high concordance."
    elif tier == "moderate":
        summary = f"Moderate agreement: {winner_short} leads with {winner_first_places} of {valid_evaluators_count} first-place votes, with minor variation."
    else:
        summary = f"Contested debate: The council is divided across candidates with differing evaluation criteria."

    return {
        "score": consensus_score,
        "tier": tier,
        "tier_label": tier_label,
        "badge_icon": badge_icon,
        "kendall_w": round(kendall_w, 2),
        "top_pick_agreement_pct": top_pick_agreement_pct,
        "total_voters": valid_evaluators_count,
        "winner_model": winner_model,
        "winner_first_places": winner_first_places,
        "summary": summary,
        "vote_matrix": vote_matrix
    }


async def generate_conversation_title(
    user_query: str,
    chairman_model: Optional[str] = None
) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message
        chairman_model: Optional model to use for title generation

    Returns:
        A short title (3-5 words)
    """
    active_model = chairman_model if chairman_model else CHAIRMAN_MODEL
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    try:
        response = await query_model(active_model, messages, timeout=30.0)

        if response and response.get('content'):
            title = response['content'].strip()
            title = title.strip('"\'`').replace('\n', ' ')
            if len(title.split()) > 7:
                title = ' '.join(title.split()[:5])
            return title or "New Conversation"
    except Exception as e:
        print(f"Error generating title with {active_model}: {e}")

    # Fallback to simple truncation
    words = user_query.split()
    if len(words) <= 5:
        return user_query
    return ' '.join(words[:5]) + '...'


async def run_full_council(
    user_query: str,
    council_models: Optional[List[str]] = None,
    chairman_model: Optional[str] = None,
    persona: Optional[str] = "strict_truth"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question
        council_models: Optional custom list of models to form the council
        chairman_model: Optional custom chairman model for final synthesis
        persona: Optional specialized council persona ID

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(
        user_query,
        council_models=council_models,
        persona=persona
    )

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please check your model configuration or OpenRouter credits."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query,
        stage1_results,
        council_models=council_models,
        persona=persona
    )

    # Calculate aggregate rankings & consensus
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
    consensus = calculate_consensus_metrics(stage2_results, label_to_model, aggregate_rankings)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        chairman_model=chairman_model,
        persona=persona
    )

    persona_data = get_persona(persona)

    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings,
        "consensus": consensus,
        "persona": {
            "id": persona_data["id"],
            "name": persona_data["name"],
            "icon": persona_data["icon"],
            "badge": persona_data["badge"]
        }
    }

    return stage1_results, stage2_results, stage3_result, metadata

