"""Extraction et reparation de JSON depuis des reponses LLM."""

from __future__ import annotations

import json
import re
def strip_thinking(text: str) -> str:
    """Supprime les blocs <think>...</think> des reponses LLM."""

    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
def _strip_markdown_from_json(text: str) -> str:
    """Nettoie le formatage markdown que les LLM injectent dans du JSON."""
    text = re.sub(r'//[^\n"]*$', "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text
def _fix_unescaped_quotes(text: str) -> str:
    """Repare les guillemets doubles non-echappees dans les valeurs JSON."""
    result = []
    i = 0
    n = len(text)
    in_string = False

    while i < n:
        ch = text[i]

        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
            i += 1
        else:
            if ch == "\\" and i + 1 < n:
                result.append(ch)
                result.append(text[i + 1])
                i += 2
            elif ch == '"':
                rest = text[i + 1 :].lstrip()
                if not rest or rest[0] in (",", "}", "]", ":"):
                    result.append(ch)
                    in_string = False
                    i += 1
                else:
                    result.append('\\"')
                    i += 1
            else:
                result.append(ch)
                i += 1

    return "".join(result)
def try_parse_json(text: str) -> dict | list | None:
    """Tente json.loads avec reparations progressives si echec."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    cleaned = _strip_markdown_from_json(text)
    if cleaned != text:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    fixed = _fix_unescaped_quotes(text)
    if fixed != text:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    if cleaned != text:
        fixed_cleaned = _fix_unescaped_quotes(cleaned)
        if fixed_cleaned != cleaned:
            try:
                return json.loads(fixed_cleaned)
            except json.JSONDecodeError:
                pass

    return None
def extract_json(text: str) -> dict | None:
    """Extrait un objet JSON d'une reponse LLM."""
    text = strip_thinking(text)

    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        result = try_parse_json(match.group(1))
        if isinstance(result, dict):
            return result

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        result = try_parse_json(match.group())
        if isinstance(result, dict):
            return result

    result = try_parse_json(text)
    return result if isinstance(result, dict) else None
def extract_json_array(text: str) -> list | None:
    """Extrait un tableau JSON d'une reponse LLM."""
    text = strip_thinking(text)

    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        result = try_parse_json(match.group(1))
        if isinstance(result, list):
            return result

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        result = try_parse_json(match.group())
        if isinstance(result, list):
            return result

    result = try_parse_json(text)
    return result if isinstance(result, list) else None
