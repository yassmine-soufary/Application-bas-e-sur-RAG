"""Conservative document relationships, discovered from explicit wording and references.

No file number, old/new value or EIH-specific target is hardcoded here.
Relationships expand context, never silently establish legal precedence.
"""
import re
from .models import Chunk, SearchHit

REFERENCE = re.compile(r'\b[A-Z]{2,}(?:-[A-Z0-9]+){2,}\b')
MODIFICATION = re.compile(r'modifi(?:e|ent|cation)|remplac(?:e|ent)|au lieu de|désormais', re.I)


def relationships(chunks: list[Chunk]) -> dict[str, set[str]]:
    documents: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        documents.setdefault(chunk.reference, []).append(chunk)
    links = {}
    for reference, parts in documents.items():
        # Require an explicit modifying status AND replacement wording in the body.
        status = parts[0].status
        body = '\n'.join(c.text for c in parts)
        if MODIFICATION.search(status) and re.search(r'remplac\w* les dispositions|modifie\w*.*(?:article|section|règle)', body, re.I):
            targets = set(REFERENCE.findall(status + '\n' + body)) & documents.keys() - {reference}
            # A mere citation to another rule is not a target: prefer references in status.
            explicit = set(REFERENCE.findall(status)) & targets
            if explicit:
                links[reference] = {t for t in explicit if documents[t][0].date < parts[0].date}
    return links


def expand(hits: list[SearchHit], chunks: list[Chunk]) -> tuple[list[SearchHit], list[dict]]:
    links = relationships(chunks)
    relevant = {h.chunk.reference for h in hits}
    edges = [{'amending': modifier, 'target': target} for modifier, targets in links.items()
             for target in targets if modifier in relevant or target in relevant]
    # Include both documents in full for small university corpus: preserves scope,
    # unchanged rules and old provisions, even when semantic retrieval misses them.
    required = {e[key] for e in edges for key in ('amending', 'target')}
    result = list(hits)
    seen = {h.chunk.id for h in hits}
    for chunk in sorted(chunks, key=lambda c: (c.date, c.file, c.page, c.section, c.id)):
        if chunk.reference in required and chunk.id not in seen:
            result.append(SearchHit(chunk=chunk, score=-1.0))  # linked context, not a measured retrieval score
            seen.add(chunk.id)
    return result, edges
