"""Classify an email as "important" or "pub" (advertising/newsletter).

Cheap, deterministic rules handle the obvious cases (unsubscribe headers,
known ad/newsletter senders, promo keywords). Anything the rules aren't
confident about is sent to Claude for a judgement call.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from anthropic import Anthropic

from .gmail_client import EmailMessage

Category = Literal["important", "pub"]

PUB_KEYWORDS = [
    "promo", "promotion", "soldes", "solde", "réduction", "reduction",
    "offre spéciale", "offre speciale", "code promo", "% de réduction",
    "newsletter", "unsubscribe", "se désinscrire", "se desinscrire",
    "livraison offerte", "vente flash", "black friday", "cyber monday",
    "coupon", "deal du jour",
]

PUB_SENDER_HINTS = [
    "newsletter", "no-reply", "noreply", "no_reply", "notifications",
    "marketing", "promo", "offers", "news@", "info@",
]


@dataclass
class Classification:
    category: Category
    reason: str


def _rule_based(message: EmailMessage) -> Classification | None:
    subject_lower = message.subject.lower()
    sender_lower = message.sender_email.lower()

    if message.has_list_unsubscribe:
        return Classification("pub", "en-tête List-Unsubscribe présent")

    if any(keyword in subject_lower for keyword in PUB_KEYWORDS):
        return Classification("pub", "mot-clé publicitaire dans le sujet")

    if any(hint in sender_lower for hint in PUB_SENDER_HINTS):
        return Classification("pub", "expéditeur automatisé/marketing")

    return None


CLASSIFY_SYSTEM_PROMPT = (
    "Tu classes des emails en deux catégories uniquement : \"important\" ou "
    "\"pub\". \"pub\" couvre les publicités, newsletters, promotions et "
    "notifications automatiques sans valeur pour l'utilisateur. \"important\" "
    "couvre tout le reste (messages personnels, professionnels, factures, "
    "rendez-vous, sécurité de compte, etc.). Réponds uniquement avec un JSON "
    "de la forme {\"category\": \"important\"|\"pub\", \"reason\": \"...\"}."
)


def _llm_classify(client: Anthropic, message: EmailMessage) -> Classification:
    user_content = (
        f"Expéditeur: {message.sender_name} <{message.sender_email}>\n"
        f"Sujet: {message.subject}\n"
        f"Extrait: {message.snippet}"
    )
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=200,
        system=CLASSIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = response.content[0].text
    try:
        data = json.loads(text)
        category = data["category"]
        if category not in ("important", "pub"):
            raise ValueError(category)
        return Classification(category, data.get("reason", "classification IA"))
    except (json.JSONDecodeError, KeyError, ValueError):
        return Classification("important", "échec de classification IA, classé important par défaut")


def classify(client: Anthropic, message: EmailMessage) -> Classification:
    rule_result = _rule_based(message)
    if rule_result is not None:
        return rule_result
    return _llm_classify(client, message)
