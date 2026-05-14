"""
chat_export.py — Export chat history as PDF or TXT
"""

import io
from datetime import datetime


def export_chat_as_text(messages: list[dict], user_name: str = "User") -> str:
    """Export chat messages as plain text."""
    lines = [
        "═" * 60,
        f"  DataGuru — Chat Export",
        f"  User: {user_name}",
        f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "═" * 60,
        "",
    ]
    for msg in messages:
        role = user_name if msg["role"] == "user" else "DataGuru"
        lines.append(f"[{role}]")
        lines.append(msg["content"])
        if msg.get("sources"):
            lines.append(f"  Sources: {', '.join(msg['sources'])}")
        lines.append("")
        lines.append("─" * 40)
        lines.append("")

    lines.append(f"\n{'═' * 60}")
    lines.append(f"  End of export — {len(messages)} messages")
    lines.append(f"{'═' * 60}")
    return "\n".join(lines)


def export_chat_as_pdf(messages: list[dict], user_name: str = "User") -> bytes:
    """Export chat messages as a styled PDF. Returns PDF bytes."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header
    pdf.set_fill_color(10, 25, 41)
    pdf.rect(0, 0, 210, 297, "F")  # dark background

    # Title bar
    pdf.set_fill_color(8, 145, 178)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_y(8)
    pdf.cell(0, 12, "DataGuru - Chat Export", align="C")

    # Sub-header
    pdf.set_y(32)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, f"User: {user_name}  |  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Messages: {len(messages)}", align="C")
    pdf.ln(12)

    # Messages
    for msg in messages:
        is_user = msg["role"] == "user"
        role_label = user_name if is_user else "DataGuru"

        # Check if we need a new page
        if pdf.get_y() > 260:
            pdf.add_page()
            pdf.set_fill_color(10, 25, 41)
            pdf.rect(0, 0, 210, 297, "F")

        # Role label
        if is_user:
            pdf.set_text_color(6, 182, 212)
        else:
            pdf.set_text_color(20, 184, 166)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, role_label)
        pdf.ln(5)

        # Message content
        pdf.set_text_color(226, 232, 240)
        pdf.set_font("Helvetica", "", 9)

        content = msg["content"]
        # Clean up markdown formatting for PDF
        content = content.replace("**", "").replace("```", "").replace("`", "")

        # Write multi-line content
        pdf.multi_cell(0, 5, content)

        # Sources
        if msg.get("sources"):
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(100, 116, 139)
            sources_text = "Sources: " + ", ".join(msg["sources"])
            pdf.multi_cell(0, 4, sources_text)

        # Separator
        pdf.ln(3)
        pdf.set_draw_color(30, 64, 96)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

    return pdf.output()
