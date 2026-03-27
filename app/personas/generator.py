"""Persona generation — LLM-based creation with quality judge."""

from __future__ import annotations

import logging
import random
import uuid

from app.llm.json_utils import extract_json, strip_thinking
from app.llm.queue import Priority, get_queue
from app.personas.models import Persona
from app.profiles.registry import PopulationProfile, load_sources_content

logger = logging.getLogger(__name__)

PERSONA_TEMPERATURE = 0.8
MAX_RETRIES = 2
def _sample_attributes(profile: PopulationProfile, count: int) -> list[dict[str, str]]:
    """Sample N attribute combinations from a profile."""

    results: list[dict[str, str]] = []
    for _ in range(count):
        attrs: dict[str, str] = {}
        for dim in profile.dimensions:
            values = profile.get_values(dim)
            w = [profile.get_weight(dim, v) for v in values]
            attrs[dim] = random.choices(values, weights=w, k=1)[0]  # nosec B311
        results.append(attrs)
    return results
def _format_attrs_text(attributes: dict[str, str], profile: PopulationProfile) -> str:
    lines = []
    for dim, val in attributes.items():
        desc = profile.get_description(dim, val)
        if desc:
            lines.append(f"- {dim}: {val} ({desc})")
        else:
            lines.append(f"- {dim}: {val}")
    return "\n".join(lines)
def _build_persona_prompt(
    attributes: dict[str, str],
    profile: PopulationProfile,
    sources_content: str = "",
    generated_name: str = "",
) -> str:
    attrs_text = _format_attrs_text(attributes, profile)

    context_block = ""
    if profile.context:
        context_block = f"""
Cadre de reference : {profile.context}
Tu connais cet univers/cette epoque/cette culture : utilise TOUTES
 tes connaissances pour incarner ce persona de maniere credible.
"""

    sources_block = ""
    if sources_content:
        sources_block = f"""
Documents de reference :
{sources_content}
"""

    name_block = ""
    if generated_name:
        name_block = (
            f"\nIMPORTANT : Le persona s'appelle {generated_name}. "
            "Utilise ce prenom et ce nom de famille tels quels.\n"
        )
        name_instruction = (
            f'"name": "DOIT commencer par {generated_name}, ' "suivi de l'age et du role\""
        )
    else:
        name_instruction = '"name": "Identite avec age et role"'

    return f"""Tu es un generateur de personas fictifs pour une simulation.

IMPORTANT : Chaque persona doit etre AUTHENTIQUE et FIDELE a ses attributs.
Ses opinions, valeurs et comportements decoulent naturellement de son profil.
Un personnage mauvais pense et agit en mauvais. Un personnage modere a des
positions moderees mais affirmees. Un radical est radical. Un conservateur
est conservateur. Un progressiste est progressiste.
Ne force pas l'extremisme : respecte le positionnement assigne.
Chaque persona doit etre UNIQUE et MEMORABLE.

Profil de population : {profile.description}
{context_block}{sources_block}{name_block}
Voici les attributs de ce persona :
{attrs_text}

Genere un persona fictif coherent avec ces attributs.

Reponds UNIQUEMENT avec un objet JSON (pas de markdown, pas de commentaire) \
contenant exactement ces 5 cles :
{{
  {name_instruction},
  "background": "4-5 phrases : origines, parcours, evenements marquants",
  "valeurs": "Croyances profondes, coherentes avec les attributs",
  "vision": "Comment il/elle voit la societe et les autres",
  "traits": "3-4 traits dominants avec exemples concrets"
}}

Exemple pour un Nain Guerrier Loyal Bon :
{{
  "name": "Thorin Marteau-de-Fer, 180 ans, forgeron et veteran",
  "background": "Ne dans les forges du Mont Kazad, Thorin a combattu \
dans trois guerres claniques avant de raccrocher sa hache. Il porte \
une cicatrice au front, souvenir d'un duel d'honneur qu'il a refuse \
de fuir. Aujourd'hui forgeron respecte, il forme les apprentis avec \
la meme rigueur que ses anciens maitres.",
  "valeurs": "L'honneur du clan passe avant tout. Un serment est \
sacre, meme s'il coute la vie. La loi existe pour proteger les \
faibles, pas pour servir les puissants.",
  "vision": "Le monde est divise entre ceux qui tiennent parole et \
les autres. Il meprise la ruse et la manipulation, preferant une \
verite brutale a un mensonge poli.",
  "traits": "Obstine jusqu'a l'entetement : refuse de negocier quand \
il estime avoir raison. Loyal : a pris des coups pour defendre des \
inconnus. Bourru mais juste : ses critiques sont dures mais toujours \
meritees."
}}

Remplis chaque champ avec du contenu riche et detaille."""
def _assemble_system_prompt(persona_data: dict, attributes: dict[str, str]) -> str:
    name = persona_data.get("name", "Inconnu")
    background = persona_data.get("background", "")
    valeurs = persona_data.get("valeurs", "")
    vision = persona_data.get("vision", "")
    traits = persona_data.get("traits", "")

    return f"""Tu es {name}.

Ton histoire : {background}

Tes valeurs : {valeurs}
Ta vision du monde : {vision}
Personnalite : {traits}

Tes opinions sont authentiques, assumees et coherentes avec ton vecu \
et tes valeurs. Tu ne cherches pas a plaire ni a etre \
politiquement correct, mais tu restes fidele a ce que tu es."""
def _validate_persona_json(data: dict) -> bool:
    required = ("name", "background", "valeurs", "vision", "traits")
    for key in required:
        val = data.get(key)
        if not isinstance(val, str) or not val.strip():
            return False
    return True
def _generate_persona_id() -> str:
    return f"per_{uuid.uuid4().hex[:12]}"
def _generate_name(profile: PopulationProfile, attributes: dict[str, str]) -> str:
    if not profile.name_generator:
        return ""
    try:
        from app.personas.name_generators import get_name_generator

        gen_fn = get_name_generator(profile.name_generator["type"])
        gen_attrs = {
            k: attributes[k]
            for k in profile.name_generator.get("depends_on", [])
            if k in attributes
        }
        return gen_fn(gen_attrs)
    except Exception:
        logger.warning("Name generator failed, falling back to LLM naming")
        return ""
def _build_fallback_persona(
    persona_id: str,
    attributes: dict[str, str],
    profile: PopulationProfile,
    model: str,
) -> Persona:
    name = _generate_name(profile, attributes)
    if not name:
        attr_parts = [f"{v}" for v in attributes.values()]
        name = ", ".join(attr_parts[:3])
    attrs_str = ", ".join(f"{k}={v}" for k, v in attributes.items())
    context_hint = f" ({profile.context})" if profile.context else ""
    fallback_data = {
        "name": name,
        "background": f"Persona du profil '{profile.name}'{context_hint} "
        f"avec les attributs : {attrs_str}.",
        "valeurs": "Non determine.",
        "vision": "Non determine.",
        "traits": "Non determine.",
    }
    return Persona(
        id=persona_id,
        name=name,
        attributes=attributes,
        system_prompt=_assemble_system_prompt(fallback_data, attributes),
        background=fallback_data["background"],
        model=model,
    )
def _build_judge_prompt(
    attributes: dict[str, str],
    persona_data: dict,
    profile: PopulationProfile,
) -> str:
    attrs_text = _format_attrs_text(attributes, profile)

    context_line = ""
    if profile.context:
        context_line = f"\nCadre de reference : {profile.context}"

    return f"""Tu es un controleur qualite pour des personas synthetiques.

Profil de population : {profile.description}{context_line}

Attributs bruts assignes :
{attrs_text}

Persona genere :
- Nom : {persona_data.get('name', '')}
- Background : {persona_data.get('background', '')}
- Valeurs : {persona_data.get('valeurs', '')}
- Vision : {persona_data.get('vision', '')}
- Traits : {persona_data.get('traits', '')}

Evalue la coherence de ce persona selon ces criteres :
1. Les attributs bruts sont-ils refletes dans le narratif ?
2. Le background, les valeurs, la vision et les traits sont-ils coherents entre eux ?
3. Le contenu est-il suffisamment riche et specifique ?

Reponds UNIQUEMENT avec un objet JSON :
{{"verdict": "accepted" ou "rejected", "justification": "Explication en 1-2 phrases"}}"""
async def _judge_persona(
    attributes: dict[str, str],
    persona_data: dict,
    profile: PopulationProfile,
    judge_model: str,
    judge_temperature: float = 0.1,
) -> tuple[bool, str]:
    attrs_summary = ", ".join(f"{k}={v}" for k, v in attributes.items())
    persona_name = persona_data.get("name", "?")
    logger.info("[JUDGE] Evaluation persona=%s model=%s attrs=[%s]", persona_name, judge_model, attrs_summary)

    prompt = _build_judge_prompt(attributes, persona_data, profile)
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un evaluateur rigoureux de personas synthetiques. "
                "Sois exigeant sur la coherence entre attributs et narratif."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    try:
        queue = get_queue()
        response = await queue.chat_queued(Priority.MEDIUM, judge_model, messages, judge_temperature)
        content = strip_thinking(response["message"]["content"])
        data = extract_json(content)

        if data and "verdict" in data:
            verdict = data["verdict"].strip().lower()
            justification = data.get("justification", "Pas de justification")
            accepted = verdict == "accepted"
            log_fn = logger.info if accepted else logger.warning
            log_fn("[JUDGE] verdict=%s persona=%s justification=%s", "ACCEPTED" if accepted else "REJECTED", persona_name, justification)
            return accepted, justification

        logger.warning("[JUDGE] verdict=PARSE_FAILURE persona=%s", persona_name)
        return True, "Judge parse failure — accepted by default"

    except Exception:
        logger.exception("[JUDGE] verdict=ERROR persona=%s", persona_name)
        return True, "Judge error — accepted by default"
async def _create_persona(
    attributes: dict[str, str],
    profile: PopulationProfile,
    model: str,
    sources_content: str = "",
    assigned_model: str = "",
    temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
) -> Persona:
    stored_model = assigned_model or model
    persona_id = _generate_persona_id()
    attrs_summary = ", ".join(f"{k}={v}" for k, v in attributes.items())
    logger.info("[PERSONA] START id=%s model=%s attrs=[%s]", persona_id, model, attrs_summary)

    generated_name = _generate_name(profile, attributes)

    prompt = _build_persona_prompt(attributes, profile, sources_content, generated_name)
    messages = [{"role": "user", "content": prompt}]

    judge_retries_left = judge_max_retries if judge_model else 0
    last_valid_data: dict | None = None

    for _judge_round in range(judge_max_retries + 1 if judge_model else 1):
        extracted = False
        for attempt in range(MAX_RETRIES + 1):
            try:
                queue = get_queue()
                response = await queue.chat_queued(Priority.MEDIUM, model, messages, temperature)
                content = response["message"]["content"]
                content = strip_thinking(content)

                data = extract_json(content)
                if data and _validate_persona_json(data):
                    last_valid_data = data
                    extracted = True
                    logger.info("[PERSONA] JSON_OK id=%s attempt=%d/%d", persona_id, attempt + 1, MAX_RETRIES + 1)
                    break

                if data is None:
                    reason = "extraction JSON echouee"
                else:
                    required = ("name", "background", "valeurs", "vision", "traits")
                    missing = [k for k in required if not isinstance(data.get(k), str) or not data.get(k, "").strip()]
                    reason = f"champs manquants ou vides : {', '.join(missing)}"

                logger.warning("[PERSONA] JSON_FAIL id=%s attempt=%d/%d — %s", persona_id, attempt + 1, MAX_RETRIES + 1, reason)

                correction = (
                    f"ERREUR : ta reponse est invalide. {reason}. "
                    "Renvoie UNIQUEMENT un objet JSON avec exactement ces 5 cles : "
                    '"name", "background", "valeurs", "vision", "traits". '
                    "Pas de commentaire, pas de markdown."
                )
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": correction})

            except Exception:
                logger.exception("[PERSONA] LLM_ERROR id=%s attempt=%d/%d", persona_id, attempt + 1, MAX_RETRIES + 1)

        if not extracted:
            logger.warning("[PERSONA] ALL_JSON_FAILED id=%s", persona_id)
            break

        if judge_model:
            accepted, justification = await _judge_persona(
                attributes, last_valid_data, profile, judge_model, judge_temperature
            )
            if not accepted and judge_retries_left > 0:
                judge_retries_left -= 1
                logger.warning("[PERSONA] JUDGE_RETRY id=%s — %s", persona_id, justification)
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"REJET DU CONTROLE QUALITE : {justification}. "
                            "Corrige le persona pour le rendre plus coherent avec "
                            "les attributs assignes. Renvoie UNIQUEMENT le JSON corrige."
                        ),
                    }
                )
                continue

        system_prompt = _assemble_system_prompt(last_valid_data, attributes)
        persona_name = last_valid_data["name"].strip()
        logger.info("[PERSONA] DONE id=%s name=%s model=%s", persona_id, persona_name[:60], stored_model)
        return Persona(
            id=persona_id,
            name=persona_name,
            attributes=attributes,
            system_prompt=system_prompt,
            background=last_valid_data["background"].strip(),
            model=stored_model,
        )

    if last_valid_data:
        persona_name = last_valid_data["name"].strip()
        logger.warning("[PERSONA] JUDGE_EXHAUSTED id=%s name=%s", persona_id, persona_name[:60])
        system_prompt = _assemble_system_prompt(last_valid_data, attributes)
        return Persona(
            id=persona_id,
            name=persona_name,
            attributes=attributes,
            system_prompt=system_prompt,
            background=last_valid_data["background"].strip(),
            model=stored_model,
        )

    logger.warning("[PERSONA] FALLBACK id=%s", persona_id)
    return _build_fallback_persona(persona_id, attributes, profile, stored_model)
async def generate_personas(
    profile: PopulationProfile,
    count: int,
    models: str | list[str],
    assigned_models: list[str] | None = None,
    temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
) -> list[Persona]:
    if count < 1:
        raise ValueError(f"count must be >= 1, got: {count}")

    if isinstance(models, str):
        models = [models]

    vote_models = assigned_models or models
    sampled = _sample_attributes(profile, count)
    sources_content = load_sources_content(profile)
    personas: list[Persona] = []

    for attrs in sampled:
        model = random.choice(models)  # nosec B311
        assigned = random.choice(vote_models)  # nosec B311
        persona = await _create_persona(
            attrs, profile, model, sources_content,
            assigned_model=assigned, temperature=temperature,
            judge_model=judge_model, judge_temperature=judge_temperature,
            judge_max_retries=judge_max_retries,
        )
        personas.append(persona)

    return personas
async def generate_personas_iter(
    profile: PopulationProfile,
    count: int,
    models: str | list[str],
    assigned_models: list[str] | None = None,
    temperature: float = 0.8,
    judge_model: str = "",
    judge_temperature: float = 0.1,
    judge_max_retries: int = 2,
):
    if count < 1:
        raise ValueError(f"count must be >= 1, got: {count}")

    if isinstance(models, str):
        models = [models]

    vote_models = assigned_models or models
    sampled = _sample_attributes(profile, count)
    sources_content = load_sources_content(profile)

    for i, attrs in enumerate(sampled):
        model = random.choice(models)  # nosec B311
        assigned = random.choice(vote_models)  # nosec B311
        persona = await _create_persona(
            attrs, profile, model, sources_content,
            assigned_model=assigned, temperature=temperature,
            judge_model=judge_model, judge_temperature=judge_temperature,
            judge_max_retries=judge_max_retries,
        )
        yield (i + 1, count, persona)
