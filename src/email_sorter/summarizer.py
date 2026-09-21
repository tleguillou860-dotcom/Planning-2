"""Turn today's important emails into a short French summary for WhatsApp."""
from __future__ import annotations

from anthropic import Anthropic

from .gmail_client import EmailMessage

SUMMARY_SYSTEM_PROMPT = (
    "Tu rédiges un résumé matinal des emails importants pour un utilisateur "
    "pressé, en français. Pour chaque email, une ligne courte avec l'essentiel "
    "(expéditeur et ce qu'il faut retenir ou l'action à faire s'il y en a une). "
    "Style direct, sans blabla, format liste à puces. Pas d'introduction ni de "
    "conclusion superflue."
)


def build_summary(client: Anthropic, messages: list[EmailMessage]) -> str:
    if not messages:
        return "Aucun mail important ce matin."

    emails_block = "\n\n".join(
        f"- Expéditeur: {m.sender_name} <{m.sender_email}>\n"
        f"  Sujet: {m.subject}\n"
        f"  Extrait: {m.snippet}"
        for m in messages
    )
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": emails_block}],
    )
    bullets = response.content[0].text.strip()
    count = len(messages)
    header = f"📬 {count} mail{'s' if count > 1 else ''} important{'s' if count > 1 else ''} ce matin :\n\n"
    return header + bullets
