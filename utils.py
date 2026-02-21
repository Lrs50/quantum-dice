"""
utils.py
────────
Helper utilities: group balancing, colour tools, password analysis,
circuit diagram rendering, and display formatting.
"""

from __future__ import annotations

import math
from typing import Any, List, Tuple


# ─── Group balancing ──────────────────────────────────────────────────────────

def balanced_groups(items: List[Any], n_groups: int) -> List[List[Any]]:
    """
    Divide *items* into *n_groups* balanced groups.

    Base size  = len(items) // n_groups
    Remainder groups (first remainder) get one extra member.

    Example: 15 items, 4 groups  →  [4, 4, 4, 3]
    """
    n = len(items)
    if n_groups <= 0:
        raise ValueError("n_groups must be > 0")
    if n_groups > n:
        raise ValueError("More groups than items")

    base = n // n_groups
    remainder = n % n_groups
    groups: List[List[Any]] = []
    idx = 0
    for i in range(n_groups):
        size = base + (1 if i < remainder else 0)
        groups.append(items[idx: idx + size])
        idx += size
    return groups


def group_size_summary(n_items: int, n_groups: int) -> str:
    """Human-readable summary of balanced group sizes."""
    base = n_items // n_groups
    remainder = n_items % n_groups
    if remainder == 0:
        return f"{n_groups} groups × {base} members"
    return (
        f"{remainder} group(s) of {base + 1}  +  "
        f"{n_groups - remainder} group(s) of {base}"
    )


# ─── Colour utilities ─────────────────────────────────────────────────────────

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) integers to '#rrggbb' hex string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def _srgb(c: int) -> float:
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance [0, 1]."""
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def contrast_text(r: int, g: int, b: int) -> str:
    """Return '#000000' or '#ffffff' for best contrast on the given background."""
    return "#000000" if luminance(r, g, b) > 0.179 else "#ffffff"


def color_name_approx(r: int, g: int, b: int) -> str:
    """Very rough colour name based on dominant channel."""
    mx = max(r, g, b)
    if mx < 60:
        return "Void Black"
    if r == mx and g < 100 and b < 100:
        return "Quantum Red"
    if g == mx and r < 100 and b < 100:
        return "Superposition Green"
    if b == mx and r < 100 and g < 100:
        return "Entangled Blue"
    if r == mx and g == mx and b < 100:
        return "Photon Yellow"
    if r == mx and b == mx and g < 100:
        return "Probability Magenta"
    if g == mx and b == mx and r < 100:
        return "Wavefunction Cyan"
    if mx > 200:
        return "Collapsed White"
    return "Quantum Grey"


# ─── Password utilities ───────────────────────────────────────────────────────

def password_entropy(password: str) -> float:
    """Approximate entropy in bits (based on charset size and length)."""
    import string as _s
    pool = 0
    if any(c in _s.ascii_lowercase for c in password):
        pool += 26
    if any(c in _s.ascii_uppercase for c in password):
        pool += 26
    if any(c in _s.digits for c in password):
        pool += 10
    if any(c not in _s.ascii_letters + _s.digits for c in password):
        pool += 32
    if pool == 0:
        pool = 26
    return len(password) * math.log2(pool)


def password_strength_label(password: str) -> Tuple[str, str]:
    """
    Returns (label, css_class) based on password entropy.
    """
    entropy = password_entropy(password)
    if entropy >= 100:
        return "⚛️  Quantum-Unbreakable", "strength-quantum"
    if entropy >= 72:
        return "🔐 Very Strong", "strength-very-strong"
    if entropy >= 50:
        return "🔒 Strong", "strength-strong"
    if entropy >= 36:
        return "⚠️  Moderate", "strength-moderate"
    return "❌ Weak", "strength-weak"


# ─── Circuit diagram rendering ────────────────────────────────────────────────

def render_circuit_html(n_qubits: int, gate: str = "H") -> str:
    """
    Render a simple quantum circuit as an HTML/CSS block.
    n_qubits wires, each with one gate and a measurement.
    """
    rows = ""
    for _ in range(n_qubits):
        rows += f"""
        <div class="circuit-row">
            <span class="qubit-ket">|0⟩</span>
            <span class="circuit-wire">───────</span>
            <span class="gate-box">{gate}</span>
            <span class="circuit-wire">───────</span>
            <span class="measure-box">⟨M⟩</span>
        </div>"""
    return f'<div class="circuit-diagram">{rows}</div>'


# ─── Misc display helpers ─────────────────────────────────────────────────────

DICE_UNICODE = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

COIN_LABELS = {0: ("HEADS", "🌕"), 1: ("TAILS", "🌑")}


def format_probability(p: float, outcomes: int = 0) -> str:
    """Format a probability as a percentage string."""
    pct = p * 100
    if outcomes:
        return f"{pct:.2f}% (1/{outcomes})"
    return f"{pct:.2f}%"


def bits_display(bits: List[int]) -> str:
    """Format a bit list as a colour-coded HTML string."""
    spans = "".join(
        f'<span class="bit-{"zero" if b == 0 else "one"}">{b}</span>'
        for b in bits
    )
    return f'<span class="bits-display">{spans}</span>'
