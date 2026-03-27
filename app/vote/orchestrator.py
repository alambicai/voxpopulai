"""Orchestrateur de vote synthetique — population simulee.

Genere des personas synthetiques a partir d'un profil de population,
les fait voter independamment sur une question, puis analyse les resultats.
Chaque persona vote sans voir les reponses des autres (pattern wisdom).
"""

from __future__ import annotations

import logging

from app.events.event_log import emit_event, generate_collaboration_id
from app.llm.json_utils import extract_json, strip_thinking
from app.llm.queue import Priority, get_queue
from app.personas.generator import generate_personas, generate_personas_iter
from app.personas.models import Persona
from app.personas.store import PersonaStore
from app.profiles.registry import PopulationProfile, get_profile, load_sources_content
from app.vote.models import (
    SyntheticVoteResult,
    Vote,
    VoteAnalysis,
    VoteTally,
)

logger = logging.getLogger(__name__)

SIMULATION_DISCLAIMER = (
    "SIMULATION - Ces resultats proviennent de personas generes par IA "
    "et ne representent pas de vraies opinions humaines. A utiliser comme "
    "outil d'exploration, pas comme base de decision."
)

DEFAULT_MODEL = "qwen3:14b"
DEFAULT_NUM_VOTERS = 20
DEFAULT_TEMPERATURE = 0.8
ANALYSIS_TEMPERATURE = 0.3
OPINION_TEMPERATURE = 0.6
POSITION_TEMPERATURE = 0.5
MIN_VOTERS = 3
MAX_RETRIES_VOTE = 2
def _resolve_profile(population_profile: str | PopulationProfile) -> PopulationProfile:
    """Resout un profil depuis un nom ou un objet PopulationProfile."""
    if isinstance(population_profile, str):
        return get_profile(population_profile)
    return population_profile
async def _get_or_generate_personas(
    profile: PopulationProfile,
    count: int,
    models: list[str],
    reuse: bool,
    generation_model: str | None = None,
    temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
) -> list[Persona]:
    """Obtient des personas en les reutilisant depuis la base ou en generant."""
    store = PersonaStore()

    if reuse:
        available = store.count_by_profile(profile.name)
        if available >= count:
            logger.info(
                "Reutilisation de %d personas existants pour '%s'",
                count,
                profile.name,
            )
            return store.sample(profile.name, count)
        logger.info(
            "Pas assez de personas en base (%d/%d) pour '%s', generation",
            available,
            count,
            profile.name,
        )

    gen_models = generation_model if generation_model else models
    personas = await generate_personas(
        profile,
        count,
        gen_models,
        assigned_models=models,
        temperature=temperature,
        judge_model=judge_model,
        judge_temperature=judge_temperature,
        judge_max_retries=judge_max_retries,
    )
    store.save_batch_multi(personas, profile.name)
    return personas
def _build_vote_context(profile: PopulationProfile) -> str:
    """Construit le contexte de vote depuis le profil (context + sources)."""
    parts: list[str] = []
    if profile.context:
        parts.append(profile.context)
    sources = load_sources_content(profile)
    if sources:
        parts.append(sources)
    return "\n\n".join(parts)
def _build_opinion_prompt(question: str, context: str = "") -> str:
    """Construit le prompt d'opinion libre (appel 1/2)."""
    context_block = ""
    if context:
        context_block = (
            f"\nCadre de reference : {context}\n"
            "IMPORTANT : reponds en coherence avec ton personnage, son univers, "
            "son epoque et ses biais. Une reponse sincere et coherente avec "
            "ton personnage est attendue, pas une reponse consensuelle.\n"
        )

    return (
        f"On te demande ton avis sur la question suivante :\n\n"
        f'"{question}"\n'
        f"{context_block}\n"
        "Raconte en 2-3 phrases ce que tu penses de cette question, "
        "en t'appuyant sur ton vecu, ta situation et tes convictions. "
        "Sois sincere et direct."
    )
def _build_vote_prompt(question: str) -> str:
    """Construit le prompt de vote (appel 2/2)."""
    return (
        f"Au vu de ce que tu viens d'exprimer, "
        f'"{question}" — '
        "reponds en un seul mot : oui, non, ou abstention."
    )
_VALID_POSITIONS = {"oui", "non", "abstention"}
def _extract_position(text: str) -> str | None:
    """Extrait la position (oui/non/abstention) depuis la reponse texte du LLM."""
    normalized = text.strip().lower()

    if normalized in _VALID_POSITIONS:
        return normalized

    found = [pos for pos in _VALID_POSITIONS if pos in normalized]

    if len(found) == 1:
        return found[0]

    return None
def _build_position_retry_prompt(raw_response: str) -> str:
    """Construit le feedback de retry quand la position n'est pas parseable."""
    return (
        f'Tu as repondu "{raw_response[:100]}". '
        "Ce n'est pas une reponse valide. "
        "Reponds UNIQUEMENT par un seul mot : oui, non, ou abstention."
    )
async def _cast_vote(
    persona: Persona,
    question: str,
    model: str,
    temperature: float,
    context: str = "",
) -> Vote:
    """Fait voter un persona via une conversation multi-tours."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": persona.system_prompt},
        {
            "role": "user",
            "content": _build_opinion_prompt(question, context),
        },
    ]

    reasoning = ""
    try:
        queue = get_queue()
        response = await queue.chat_queued(
            Priority.MEDIUM,
            model,
            messages,
            OPINION_TEMPERATURE,
        )
        reasoning = strip_thinking(response["message"]["content"]).strip()
        if reasoning:
            messages.append({"role": "assistant", "content": reasoning})
    except Exception:
        logger.exception(
            "Erreur LLM pour opinion de %s",
            persona.name,
        )

    if not reasoning:
        logger.warning("Fallback vote abstention pour persona %s (pas d'opinion)", persona.id)
        return Vote(
            persona=persona,
            position="abstention",
            reasoning="[Vote non exprime - erreur de traitement]",
        )

    messages.append(
        {
            "role": "user",
            "content": _build_vote_prompt(question),
        }
    )

    position = None
    raw_content = ""

    for attempt in range(MAX_RETRIES_VOTE + 1):
        try:
            queue = get_queue()
            response = await queue.chat_queued(
                Priority.MEDIUM,
                model,
                messages,
                POSITION_TEMPERATURE,
            )
            raw_content = strip_thinking(response["message"]["content"])
            position = _extract_position(raw_content)

            if position:
                messages.append({"role": "assistant", "content": raw_content})
                break

            logger.warning(
                "Position non parseable pour %s (tentative %d/%d): %s",
                persona.name,
                attempt + 1,
                MAX_RETRIES_VOTE + 1,
                raw_content[:200],
            )

            messages.append({"role": "assistant", "content": raw_content})
            messages.append(
                {
                    "role": "user",
                    "content": _build_position_retry_prompt(raw_content),
                }
            )
        except Exception:
            logger.exception(
                "Erreur LLM pour vote de %s (tentative %d/%d)",
                persona.name,
                attempt + 1,
                MAX_RETRIES_VOTE + 1,
            )

    if not position:
        logger.warning("Fallback vote abstention pour persona %s", persona.id)
        return Vote(
            persona=persona,
            position="abstention",
            reasoning=reasoning,
        )

    return Vote(
        persona=persona,
        position=position,
        reasoning=reasoning,
    )
def _compute_tally(votes: list[Vote]) -> VoteTally:
    """Calcule le decompte des votes par position."""
    total = len(votes)
    if total == 0:
        return VoteTally()

    oui = sum(1 for v in votes if v.position == "oui")
    non_count = sum(1 for v in votes if v.position == "non")
    abstention = sum(1 for v in votes if v.position == "abstention")

    return VoteTally(
        oui=oui,
        non=non_count,
        abstention=abstention,
        oui_pct=round(oui / total * 100, 1),
        non_pct=round(non_count / total * 100, 1),
        abstention_pct=round(abstention / total * 100, 1),
    )
def _build_analysis_prompt(votes: list[Vote], question: str, profile: PopulationProfile) -> str:
    """Construit le prompt d'analyse envoye au LLM."""
    votes_text = ""
    for i, vote in enumerate(votes, 1):
        attrs_str = ", ".join(f"{k}: {v}" for k, v in vote.persona.attributes.items())
        votes_text += (
            f"Votant {i} ({vote.persona.name}, {attrs_str}): "
            f"position={vote.position}\n"
            f"  Raisonnement: {vote.reasoning}\n\n"
        )

    total = len(votes)
    oui = sum(1 for v in votes if v.position == "oui")
    non_count = sum(1 for v in votes if v.position == "non")
    abstention = sum(1 for v in votes if v.position == "abstention")

    context_line = ""
    if profile.context:
        context_line = f"\nCadre de reference : {profile.context}"

    return f"""Analyse les resultats de ce vote synthetique.

Question posee : "{question}"
Profil de population : {profile.description}{context_line}
Nombre de votants : {total}

Resultats bruts :
- Oui : {oui} ({oui / total * 100:.1f}%)
- Non : {non_count} ({non_count / total * 100:.1f}%)
- Abstention : {abstention} ({abstention / total * 100:.1f}%)

Detail des votes :
{votes_text}

Produis une analyse structuree en repondant UNIQUEMENT avec un objet JSON au format suivant :
{{
  "key_arguments": {{
    "oui": ["argument 1", "argument 2"],
    "non": ["argument 1", "argument 2"]
  }},
  "demographic_patterns": [
    "Observation 1 sur les correlations demographiques",
    "Observation 2"
  ]
}}

IMPORTANT : Ne calcule PAS la position dominante ni le consensus, concentre-toi sur l'analyse qualitative des arguments et des correlations demographiques."""
def _parse_analysis_data(data: dict) -> dict | None:
    """Extrait les champs qualitatifs du JSON LLM."""
    key_arguments = data.get("key_arguments", {})
    if not isinstance(key_arguments, dict):
        return None
    key_arguments.setdefault("oui", [])
    key_arguments.setdefault("non", [])

    demographic_patterns = data.get("demographic_patterns", [])
    if not isinstance(demographic_patterns, list):
        demographic_patterns = []

    return {
        "key_arguments": key_arguments,
        "demographic_patterns": demographic_patterns,
    }
def _compute_analysis_stats(votes: list[Vote]) -> dict:
    """Calcule dominant_position, margin et consensus_level de maniere deterministe."""
    total = len(votes)
    counts = {"oui": 0, "non": 0, "abstention": 0}
    for v in votes:
        counts[v.position] += 1

    sorted_positions = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    first_pct = sorted_positions[0][1] / total if total > 0 else 0
    second_pct = sorted_positions[1][1] / total if total > 0 else 0
    margin = round(first_pct - second_pct, 2)

    if margin > 0.3:
        consensus = "fort"
    elif margin > 0.15:
        consensus = "modere"
    elif margin > 0.05:
        consensus = "faible"
    else:
        consensus = "aucun"

    dominant = sorted_positions[0][0] if margin > 0.05 else "indecis"

    return {
        "dominant_position": dominant,
        "margin": margin,
        "consensus_level": consensus,
    }
def _build_fallback_analysis(votes: list[Vote]) -> VoteAnalysis:
    """Construit une analyse deterministe en cas d'echec LLM."""
    stats = _compute_analysis_stats(votes)
    return VoteAnalysis(
        dominant_position=stats["dominant_position"],
        margin=stats["margin"],
        key_arguments={"oui": [], "non": []},
        demographic_patterns=["[Analyse automatique - LLM indisponible]"],
        consensus_level=stats["consensus_level"],
    )
async def _analyze_votes(
    votes: list[Vote],
    question: str,
    profile: PopulationProfile,
    model: str,
) -> VoteAnalysis:
    """Analyse des votes : stats deterministes + analyse qualitative LLM."""
    stats = _compute_analysis_stats(votes)

    prompt = _build_analysis_prompt(votes, question, profile)
    messages = [
        {
            "role": "system",
            "content": "Tu es un analyste de sondages. Tu produis des analyses objectives et nuancees.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        queue = get_queue()
        response = await queue.chat_queued(
            Priority.MEDIUM,
            model,
            messages,
            ANALYSIS_TEMPERATURE,
        )
        content = strip_thinking(response["message"]["content"])
        data = extract_json(content)
        if data:
            qualitative = _parse_analysis_data(data)
            if qualitative:
                return VoteAnalysis(
                    dominant_position=stats["dominant_position"],
                    margin=stats["margin"],
                    consensus_level=stats["consensus_level"],
                    key_arguments=qualitative["key_arguments"],
                    demographic_patterns=qualitative["demographic_patterns"],
                )
        logger.warning("Analyse JSON invalide: %s", content[:200])
    except Exception:
        logger.exception("Erreur LLM pour l'analyse des votes")

    return _build_fallback_analysis(votes)
async def synthetic_population_vote(
    question: str,
    population_profile: str | PopulationProfile,
    num_voters: int = DEFAULT_NUM_VOTERS,
    persona_models: str | list[str] = DEFAULT_MODEL,
    analysis_model: str | None = None,
    generation_model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    reuse_personas: bool = False,
    collaboration_id: str | None = None,
    generation_temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
) -> SyntheticVoteResult:
    """Orchestre un vote synthetique sur une question."""
    if not question or not question.strip():
        raise ValueError("La question ne peut pas etre vide.")
    if num_voters < MIN_VOTERS:
        raise ValueError(f"num_voters doit etre >= {MIN_VOTERS}, recu : {num_voters}")

    models_list = [persona_models] if isinstance(persona_models, str) else persona_models

    if not analysis_model:
        analysis_model = models_list[0]

    collab_id = collaboration_id or generate_collaboration_id()
    emit_event(
        "collaboration_start",
        collab_id,
        data={
            "mode": "synthetic_vote",
            "question": question,
            "topic": question,
            "population_profile": population_profile
            if isinstance(population_profile, str)
            else population_profile.name,
            "num_voters": num_voters,
            "models": models_list,
        },
    )

    profile = _resolve_profile(population_profile)
    personas = await _get_or_generate_personas(
        profile,
        num_voters,
        models_list,
        reuse_personas,
        generation_model,
        temperature=generation_temperature,
        judge_model=judge_model,
        judge_temperature=judge_temperature,
        judge_max_retries=judge_max_retries,
    )

    vote_context = _build_vote_context(profile)

    votes: list[Vote] = []
    for persona in personas:
        vote = await _cast_vote(
            persona,
            question,
            persona.model,
            temperature,
            vote_context,
        )
        votes.append(vote)

    tally = _compute_tally(votes)
    analysis = await _analyze_votes(votes, question, profile, analysis_model)

    result = SyntheticVoteResult(
        question=question,
        population_profile=profile.name,
        total_voters=len(votes),
        votes=votes,
        tally=tally,
        analysis=analysis,
        disclaimer=SIMULATION_DISCLAIMER,
    )

    emit_event(
        "collaboration_end",
        collab_id,
        data={
            "mode": "synthetic_vote",
            "total_voters": len(votes),
            "tally": tally.model_dump(),
            "consensus_level": analysis.consensus_level,
            "dominant_position": analysis.dominant_position,
            "result": result.model_dump(),
        },
    )

    return result
async def synthetic_vote_stream(
    question: str,
    population_profile: str | PopulationProfile,
    num_voters: int = DEFAULT_NUM_VOTERS,
    persona_models: str | list[str] = DEFAULT_MODEL,
    analysis_model: str | None = None,
    generation_model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    reuse_personas: bool = False,
    generation_temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
):
    """Orchestre un vote synthetique en yielding des evenements de progression."""
    if not question or not question.strip():
        raise ValueError("La question ne peut pas etre vide.")
    if num_voters < MIN_VOTERS:
        raise ValueError(f"num_voters doit etre >= {MIN_VOTERS}, recu : {num_voters}")

    models_list = [persona_models] if isinstance(persona_models, str) else persona_models

    if not analysis_model:
        analysis_model = models_list[0]

    collab_id = generate_collaboration_id()
    emit_event(
        "collaboration_start",
        collab_id,
        data={
            "mode": "synthetic_vote",
            "question": question,
            "topic": question,
            "population_profile": population_profile
            if isinstance(population_profile, str)
            else population_profile.name,
            "num_voters": num_voters,
            "models": models_list,
        },
    )

    profile = _resolve_profile(population_profile)

    store = PersonaStore()
    personas: list[Persona] = []

    if reuse_personas:
        available = store.count_by_profile(profile.name)
        if available >= num_voters:
            logger.info("Reutilisation de %d personas pour '%s'", num_voters, profile.name)
            personas = store.sample(profile.name, num_voters)
            for i, _p in enumerate(personas):
                yield {"phase": "personas", "current": i + 1, "total": num_voters}
        else:
            logger.info("Pas assez de personas (%d/%d), generation", available, num_voters)

    if not personas:
        gen_models = generation_model if generation_model else models_list
        async for current, total, persona in generate_personas_iter(
            profile,
            num_voters,
            gen_models,
            assigned_models=models_list,
            temperature=generation_temperature,
            judge_model=judge_model,
            judge_temperature=judge_temperature,
            judge_max_retries=judge_max_retries,
        ):
            personas.append(persona)
            yield {"phase": "personas", "current": current, "total": total}
        store.save_batch_multi(personas, profile.name)

    vote_context = _build_vote_context(profile)
    votes: list[Vote] = []
    for i, persona in enumerate(personas):
        vote = await _cast_vote(
            persona,
            question,
            persona.model,
            temperature,
            vote_context,
        )
        votes.append(vote)
        yield {"phase": "votes", "current": i + 1, "total": len(personas)}

    yield {"phase": "analysis"}
    tally = _compute_tally(votes)
    analysis = await _analyze_votes(votes, question, profile, analysis_model)

    result = SyntheticVoteResult(
        question=question,
        population_profile=profile.name,
        total_voters=len(votes),
        votes=votes,
        tally=tally,
        analysis=analysis,
        disclaimer=SIMULATION_DISCLAIMER,
    )

    emit_event(
        "collaboration_end",
        collab_id,
        data={
            "mode": "synthetic_vote",
            "total_voters": len(votes),
            "tally": tally.model_dump(),
            "consensus_level": analysis.consensus_level,
            "dominant_position": analysis.dominant_position,
            "result": result.model_dump(),
        },
    )

    yield {"phase": "done", "result": result}
