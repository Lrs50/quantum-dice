"""
app.py
──────
Quantum Dice — Streamlit frontend.

Run:  uv run streamlit run app.py
"""

from __future__ import annotations

# ── stdlib ────────────────────────────────────────────────────────────────────
import math
import string
import time
from pathlib import Path

# ── third-party ───────────────────────────────────────────────────────────────
import streamlit as st

# ── Page config (must be the very first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="⚛️ Quantum Dice",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── local ─────────────────────────────────────────────────────────────────────
from animations import (
    bloch_sphere_frames,
    bloch_sphere_static,
    probability_histogram,
    quantum_wave_frames,
    quantum_wave_idle,
)
from quantum_engine import (
    circuit_info,
    quantum_coin_flip,
    quantum_colors,
    quantum_dice_roll,
    quantum_group_divide,
    quantum_lottery,
    quantum_password,
    quantum_random_int,
    quantum_shuffle,
)
from utils import (
    COIN_LABELS,
    DICE_UNICODE,
    bits_display,
    color_name_approx,
    contrast_text,
    group_size_summary,
    password_entropy,
    password_strength_label,
    render_circuit_html,
    rgb_to_hex,
)

# ─── CSS injection ────────────────────────────────────────────────────────────


def _load_css() -> None:
    css_path = Path("static/styles.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_load_css()


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="quantum-header">
      <h1 class="quantum-title">⚛ QUANTUM DICE</h1>
      <p class="quantum-subtitle">
        True randomness via quantum superposition &amp; wavefunction collapse
      </p>
      <span class="quantum-badge">⚛ Powered by PennyLane · default.qubit simulator</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _circuit_expander(tool: str, n: int = 0) -> None:
    """Show a collapsible quantum circuit diagram."""
    info = circuit_info(tool, n)
    if not info:
        return
    n_q = info.get("n_qubits", 1)
    n_q_display = n_q if isinstance(n_q, int) else 1
    with st.expander("🔬 Quantum Circuit", expanded=False):
        st.markdown(render_circuit_html(n_q_display), unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-family:monospace;font-size:0.8rem;'
            f'color:#8888aa;margin-top:0.4rem">{info.get("description","")}</p>',
            unsafe_allow_html=True,
        )


def _result_card(
    label: str,
    value_html: str,
    prob_html: str = "",
    bits: list[int] | None = None,
) -> None:
    """Render a styled result card."""
    bits_row = (
        f'<div style="margin-top:0.5rem;font-family:monospace;font-size:0.8rem;'
        f'color:#666688">Measured bits: {bits_display(bits)}</div>'
        if bits
        else ""
    )
    st.markdown(
        f"""
        <div class="result-card">
          <div class="result-label">{label}</div>
          {value_html}
          {f'<div class="result-prob">{prob_html}</div>' if prob_html else ""}
          {bits_row}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _bloch_animation_loop(
    outcome_bit: int,
    n_frames: int = 20,
    key_prefix: str = "bloch",
) -> None:
    """Server-side frame-by-frame Bloch sphere animation via st.empty()."""
    placeholder = st.empty()
    for i, fig in enumerate(bloch_sphere_frames(outcome_bit, n_frames)):
        placeholder.plotly_chart(
            fig, width="stretch", key=f"{key_prefix}_frame_{i}_{time.time_ns()}"
        )
        time.sleep(0.09)
    placeholder.empty()


def _wave_setup(
    col,
    x_range: tuple[float, float],
    idle_label: str,
    idle_key: str,
    height: int = 280,
) -> st.empty:
    """
    Render the idle wave chart inside `col` and return its placeholder.
    The placeholder is reused by _wave_animation_loop to swap frames in-place.
    """
    with col:
        st.markdown("##### 〰 Quantum Wave")
        ph = st.empty()
        ph.plotly_chart(
            quantum_wave_idle(x_range, idle_label, height),
            width="stretch",
            key=idle_key,
        )
    return ph


def _wave_animation_loop(
    placeholder: st.empty,
    result_x: float,
    x_range: tuple[float, float],
    label: str,
    key_prefix: str,
    n_frames: int = 28,
    frame_delay: float = 0.07,
) -> None:
    """
    Server-side frame-by-frame wave animation.  Blocks until all frames are
    rendered so that result display only happens after this function returns.
    """
    for i, fig in enumerate(quantum_wave_frames(result_x, x_range, n_frames, label)):
        placeholder.plotly_chart(
            fig, width="stretch", key=f"{key_prefix}_{i}_{time.time_ns()}"
        )
        time.sleep(frame_delay)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# ─── 🎲 Dice Roll ─────────────────────────────────────────────────────────────


def tab_dice() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "3-qubit Hadamard circuit generates 8 equally-likely states → "
        "rejection-sampled to a perfect uniform 1–6 distribution."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        _circuit_expander("dice")
        st.markdown("##### ⚙ Options")
        n_dice = st.slider("Number of dice", 1, 6, 1, key="dice_n")
        animate = st.checkbox(
            "Show Bloch sphere animation", value=True, key="dice_anim"
        )
        roll_btn = st.button(
            "🎲  Roll Quantum Dice", key="btn_dice", use_container_width=True
        )

    with col_anim:
        st.markdown("##### 🌐 Bloch Sphere")
        sphere_ph = st.empty()
        sphere_ph.plotly_chart(
            bloch_sphere_static((0, 0, 1), title="|0⟩ — ready"),
            width="stretch",
            key="dice_sphere_idle",
        )

    if roll_btn:
        results: list[int] = []
        raw_bits_all: list[list[int]] = []

        with st.spinner("⚛  Entering quantum superposition…"):
            for _ in range(n_dice):
                val, bits = quantum_dice_roll()
                results.append(val)
                raw_bits_all.append(bits)

        if animate:
            outcome_bit = results[0] % 2
            with col_anim:
                _bloch_animation_loop(outcome_bit, n_frames=20, key_prefix="dice")
                sphere_ph.plotly_chart(
                    bloch_sphere_static(
                        (0, 0, 1) if outcome_bit == 0 else (0, 0, -1),
                        title="⚡ Collapsed!",
                        vector_color="#00ff88" if outcome_bit == 0 else "#7b2fff",
                    ),
                    width="stretch",
                    key="dice_sphere_collapsed",
                )

        st.markdown("---")
        if n_dice == 1:
            _result_card(
                "QUANTUM MEASUREMENT",
                f'<div class="dice-unicode">{DICE_UNICODE[results[0]]}</div>'
                f'<div class="result-value-large">{results[0]}</div>',
                prob_html="P = 1/6 ≈ 16.67%",
                bits=raw_bits_all[0],
            )
        else:
            dice_html = "".join(
                f'<span style="font-size:3rem;margin:0 0.3rem;'
                f'filter:drop-shadow(0 0 12px #00e5ff)">{DICE_UNICODE[v]}</span>'
                for v in results
            )
            st.markdown(
                f'<div class="result-card">'
                f'<div class="result-label">QUANTUM MEASUREMENTS</div>'
                f'<div style="margin:0.5rem 0">{dice_html}</div>'
                f'<div class="result-prob">Sum: {sum(results)} &nbsp;|&nbsp; '
                f'Values: {", ".join(map(str, results))}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        with st.expander("📊 Probability Distribution", expanded=True):
            st.plotly_chart(
                probability_histogram(6, results[0], title="Six-Sided Quantum Die"),
                width="stretch",
                key="dice_histogram",
            )


# ─── 🪙 Coin Flip ─────────────────────────────────────────────────────────────


def tab_coin() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "A single Hadamard gate puts one qubit into |+⟩ = (|0⟩+|1⟩)/√2. "
        "Measurement collapses it to 0 or 1 with equal probability."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        _circuit_expander("coin")
        n_flips = st.slider("Number of flips", 1, 100, 1, key="coin_n")
        animate = st.checkbox(
            "Show Bloch sphere animation", value=True, key="coin_anim"
        )
        flip_btn = st.button(
            "🪙  Flip Quantum Coin", key="btn_coin", use_container_width=True
        )

    with col_anim:
        st.markdown("##### 🌐 Bloch Sphere")
        sphere_ph = st.empty()
        sphere_ph.plotly_chart(
            bloch_sphere_static((0, 0, 1), title="|0⟩ — ready"),
            width="stretch",
            key="coin_sphere_idle",
        )

    if flip_btn:
        with st.spinner("⚛  Superposition in progress…"):
            outcomes = [quantum_coin_flip() for _ in range(n_flips)]

        if animate and n_flips <= 5:
            outcome_bit = outcomes[0]
            with col_anim:
                _bloch_animation_loop(outcome_bit, n_frames=20, key_prefix="coin")
                label_str, _ = COIN_LABELS[outcome_bit]
                sphere_ph.plotly_chart(
                    bloch_sphere_static(
                        (0, 0, 1) if outcome_bit == 0 else (0, 0, -1),
                        title=f"⚡ {label_str}",
                        vector_color="#00e5ff" if outcome_bit == 0 else "#7b2fff",
                    ),
                    width="stretch",
                    key="coin_sphere_collapsed",
                )

        st.markdown("---")
        if n_flips == 1:
            res = outcomes[0]
            label, emoji = COIN_LABELS[res]
            _result_card(
                "QUANTUM MEASUREMENT",
                f'<div style="font-size:5rem;line-height:1;'
                f'filter:drop-shadow(0 0 20px #00e5ff)">{emoji}</div>'
                f'<div class="result-value-large">{label}</div>',
                prob_html="P(Heads) = P(Tails) = 50.00%",
                bits=[res],
            )
        else:
            heads = outcomes.count(0)
            tails = outcomes.count(1)
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("🌕 Heads", heads, f"{heads / n_flips * 100:.1f}%")
            col_m2.metric("🌑 Tails", tails, f"{tails / n_flips * 100:.1f}%")
            col_m3.metric("Total Flips", n_flips)

            with st.expander("📊 Distribution", expanded=True):
                fig = probability_histogram(
                    2,
                    1 if outcomes[-1] == 0 else 2,
                    labels=["Heads (0)", "Tails (1)"],
                    title="Coin Flip Probability",
                )
                st.plotly_chart(fig, width="stretch", key="coin_histogram")

            recent = outcomes[-20:]
            chips = "".join(
                f'<span style="font-size:1.1rem;margin:0.1rem;'
                f'{"color:#00e5ff" if v == 0 else "color:#7b2fff"}">'
                f'{"🌕" if v == 0 else "🌑"}</span>'
                for v in recent
            )
            st.markdown(
                f'<div class="result-card"><div class="result-label">'
                f"LAST {len(recent)} FLIPS</div>"
                f'<div style="margin:0.5rem 0">{chips}</div></div>',
                unsafe_allow_html=True,
            )


# ─── 🔢 Random Number ─────────────────────────────────────────────────────────


def tab_random_number() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "⌈log₂(N+1)⌉ qubits encode every integer from 0 to N. "
        "Rejection sampling ensures perfect uniformity — no modulo bias."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        max_val = st.number_input(
            "Maximum value (N)",
            min_value=1,
            max_value=100_000,
            value=100,
            step=1,
            key="rng_n",
        )
        min_val = st.number_input(
            "Minimum value",
            min_value=0,
            max_value=int(max_val) - 1,
            value=0,
            step=1,
            key="rng_min",
        )
        animate = st.checkbox("Show Bloch sphere animation", value=True, key="rng_anim")
        _circuit_expander("random", int(max_val))
        gen_btn = st.button(
            "🔢  Generate Quantum Number", key="btn_rng", use_container_width=True
        )

    with col_anim:
        st.markdown("##### 🌐 Bloch Sphere")
        sphere_ph = st.empty()
        sphere_ph.plotly_chart(
            bloch_sphere_static((0, 0, 1), title="|0⟩ — ready"),
            width="stretch",
            key="rng_sphere_idle",
        )

    if gen_btn:
        span = int(max_val) - int(min_val)
        with st.spinner("⚛  Collapsing quantum state…"):
            raw_val, n_q, bits = quantum_random_int(span)
        result = int(min_val) + raw_val

        if animate:
            outcome_bit = result % 2
            with col_anim:
                _bloch_animation_loop(outcome_bit, n_frames=20, key_prefix="rng")
                sphere_ph.plotly_chart(
                    bloch_sphere_static(
                        (0, 0, 1) if outcome_bit == 0 else (0, 0, -1),
                        title="⚡ Collapsed!",
                        vector_color="#00ff88" if outcome_bit == 0 else "#7b2fff",
                    ),
                    width="stretch",
                    key="rng_sphere_collapsed",
                )

        st.markdown("---")
        _result_card(
            "QUANTUM MEASUREMENT",
            f'<div class="result-value-large">{result}</div>',
            prob_html=(
                f"Range [{int(min_val)}, {int(max_val)}] · "
                f"{n_q} qubits · "
                f"P ≈ {1 / (span + 1) * 100:.4f}%"
            ),
            bits=bits,
        )

        with st.expander("📊 Probability Distribution", expanded=True):
            display_n = min(span + 1, 20)
            st.plotly_chart(
                probability_histogram(
                    display_n,
                    min(result - int(min_val) + 1, display_n),
                    title=f"Uniform Distribution [0, {min(span, 19)}{'…' if span >= 20 else ''}]",
                ),
                width="stretch",
                key="rng_histogram",
            )


# ─── 👥 Group Divider ─────────────────────────────────────────────────────────


def tab_group_divider() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "Quantum Fisher-Yates shuffle produces perfectly uniform permutations. "
        "Groups are then balanced: larger groups get one extra member."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        names_raw = st.text_area(
            "Names (one per line)",
            value="Alice\nBob\nCarol\nDave\nEve\nFrank\nGrace\nHank\nIvy\nJack",
            height=160,
            key="grp_names",
        )
        names = [n.strip() for n in names_raw.strip().splitlines() if n.strip()]

        col_a, col_b = st.columns(2)
        with col_a:
            n_groups = st.number_input(
                "Number of groups",
                min_value=2,
                max_value=max(2, len(names)),
                value=min(3, len(names) // 2 or 2),
                step=1,
                key="grp_n",
            )
        with col_b:
            if names and int(n_groups) >= 2:
                st.markdown(
                    f'<div style="font-family:monospace;font-size:0.82rem;'
                    f'color:#8888aa;margin-top:1.6rem">'
                    f"📐 {group_size_summary(len(names), int(n_groups))}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        _circuit_expander("shuffle")
        divide_btn = st.button(
            "🔀  Quantum Divide", key="btn_grp", use_container_width=True
        )

    wave_ph = _wave_setup(
        col_anim, (0, max(len(names), 1)), "Superposition Selector", "grp_wave_idle"
    )

    if divide_btn:
        if len(names) < 2:
            st.warning("Enter at least 2 names.")
            return
        if int(n_groups) > len(names):
            st.warning("More groups than names.")
            return

        with st.spinner("⚛  Quantum shuffling…"):
            groups, shuffled = quantum_group_divide(names, int(n_groups))

        # Collapse to the original slot of the member that landed first after shuffle
        result_slot = float(names.index(shuffled[0]))
        with col_anim:
            _wave_animation_loop(
                wave_ph, result_slot, (0, len(names)), "Quantum Shuffle", "grp_wave"
            )

        st.markdown("---")
        st.markdown(
            '<p style="font-family:monospace;font-size:0.78rem;'
            "letter-spacing:0.1em;color:#00e5ff;text-transform:uppercase;"
            'margin-bottom:0.8rem">⚛ Entangled Groups</p>',
            unsafe_allow_html=True,
        )

        cols_per_row = min(int(n_groups), 3)
        for row_start in range(0, int(n_groups), cols_per_row):
            row_groups = groups[row_start : row_start + cols_per_row]
            row_cols = st.columns(len(row_groups))
            for col, grp in zip(row_cols, row_groups):
                with col:
                    idx = groups.index(grp) + 1
                    chips = "".join(
                        f'<span class="member-chip">{m}</span>' for m in grp
                    )
                    st.markdown(
                        f'<div class="group-card">'
                        f'<div class="group-title">Group {idx} · {len(grp)} members</div>'
                        f"<div>{chips}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )


# ─── 🎰 Quantum Lottery ───────────────────────────────────────────────────────


def tab_lottery() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "Quantum shuffle selects K winners from M participants with "
        "perfect uniformity — every combination of K from M is equally likely."
        "</p>",
        unsafe_allow_html=True,
    )

    _DEFAULT_PARTICIPANTS = (
        "Alice Chen\nBob Martinez\nCarol Singh\nDave Kim\n"
        "Eve Johnson\nFrank Lee\nGrace Patel\nHank Torres\n"
        "Ivy Nguyen\nJack Robinson"
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        participants_raw = st.text_area(
            "Participants (one per line)",
            value=_DEFAULT_PARTICIPANTS,
            height=160,
            key="lot_participants",
        )
        participants = [
            p.strip() for p in participants_raw.strip().splitlines() if p.strip()
        ]

        n_winners = st.number_input(
            "Number of winners to draw",
            min_value=1,
            max_value=max(1, len(participants) - 1),
            value=min(3, len(participants) - 1),
            step=1,
            key="lot_n",
        )
        draw_btn = st.button(
            "🎰  Draw Quantum Winners", key="btn_lot", use_container_width=True
        )

    wave_ph = _wave_setup(
        col_anim,
        (0, max(len(participants), 1)),
        "Lottery Superposition",
        "lot_wave_idle",
    )

    if draw_btn:
        if len(participants) < 2:
            st.warning("Enter at least 2 participants.")
            return

        with st.spinner("⚛  Drawing quantum lottery…"):
            winners, non_winners = quantum_lottery(participants, int(n_winners))

        # Collapse to the original slot of the first winner
        first_winner_slot = float(
            participants.index(winners[0]) if winners[0] in participants else 0
        )
        with col_anim:
            _wave_animation_loop(
                wave_ph,
                first_winner_slot,
                (0, len(participants)),
                "Lottery Draw",
                "lot_wave",
            )

        st.markdown("---")
        st.markdown(
            '<p style="font-family:monospace;font-size:0.78rem;'
            "letter-spacing:0.1em;color:#00ff88;text-transform:uppercase;"
            'margin-bottom:0.6rem">🏆 Winners</p>',
            unsafe_allow_html=True,
        )
        winner_chips = "".join(
            f'<span class="winner-chip">🏆 {w}</span>' for w in winners
        )
        st.markdown(
            f'<div class="result-card" style="text-align:left">{winner_chips}</div>',
            unsafe_allow_html=True,
        )

        if non_winners:
            with st.expander(f"📋 Non-winners ({len(non_winners)})", expanded=False):
                chips = "".join(
                    f'<span class="member-chip">{p}</span>' for p in non_winners
                )
                st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entries", len(participants))
        col2.metric("Winners Drawn", len(winners))
        col3.metric("Win Probability", f"{len(winners) / len(participants) * 100:.1f}%")


# ─── 🔐 Password Generator ────────────────────────────────────────────────────


def tab_password() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "Each character is selected from the charset using quantum-random index sampling. "
        "All characters are drawn in a single batch circuit call."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        length = st.slider("Password length", 8, 64, 16, key="pw_len")
        use_upper = st.checkbox("Uppercase (A–Z)", value=True, key="pw_upper")
        use_digits = st.checkbox("Digits (0–9)", value=True, key="pw_digits")
        use_symbols = st.checkbox("Symbols (!@#…)", value=True, key="pw_sym")

        pool = (
            26
            + (26 if use_upper else 0)
            + (10 if use_digits else 0)
            + (32 if use_symbols else 0)
        )
        est_entropy = length * math.log2(pool)
        st.markdown(
            f'<div style="background:rgba(13,13,43,0.7);border:1px solid rgba(123,47,255,0.3);'
            f'border-radius:10px;padding:0.8rem 1rem;font-family:monospace;font-size:0.8rem;margin-top:0.8rem">'
            f'<span style="color:#8888aa">Charset: </span><span style="color:#00e5ff">{pool} chars</span>'
            f"&nbsp;·&nbsp;"
            f'<span style="color:#8888aa">Entropy: </span><span style="color:#00e5ff">{est_entropy:.0f} bits</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

        gen_btn = st.button(
            "🔐  Generate Quantum Password", key="btn_pw", use_container_width=True
        )

    wave_ph = _wave_setup(col_anim, (0, pool), "Charset Superposition", "pw_wave_idle")

    if gen_btn:
        with st.spinner("⚛  Sampling quantum character indices…"):
            pw = quantum_password(
                length=int(length),
                use_upper=use_upper,
                use_digits=use_digits,
                use_symbols=use_symbols,
            )

        # Build charset in the same order used by quantum_password so the
        # collapse point accurately reflects the first character's position.
        charset = string.ascii_lowercase
        if use_upper:
            charset += string.ascii_uppercase
        if use_digits:
            charset += string.digits
        if use_symbols:
            charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        first_char_idx = float(charset.index(pw[0])) if pw[0] in charset else 0.0

        with col_anim:
            _wave_animation_loop(
                wave_ph,
                first_char_idx,
                (0, len(charset)),
                "Charset Sampling",
                "pw_wave",
            )

        st.markdown("---")
        st.markdown(f'<div class="password-box">{pw}</div>', unsafe_allow_html=True)

        strength_label, css_cls = password_strength_label(pw)
        entropy_val = password_entropy(pw)
        st.markdown(
            f'<div style="text-align:center;font-family:monospace;font-size:0.9rem;margin:0.3rem 0">'
            f'<span class="{css_cls}">{strength_label}</span>'
            f'<span style="color:#666688;margin-left:1rem">{entropy_val:.0f} bits entropy</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.info("💡 Click the password above to select it, then copy with Ctrl+C / ⌘C")


# ─── 🎵 Playlist Shuffle ──────────────────────────────────────────────────────

_DEFAULT_SONGS = (
    "Bohemian Rhapsody — Queen\n"
    "Stairway to Heaven — Led Zeppelin\n"
    "Hotel California — Eagles\n"
    "Smells Like Teen Spirit — Nirvana\n"
    "Imagine — John Lennon\n"
    "Billie Jean — Michael Jackson\n"
    "Like a Rolling Stone — Bob Dylan\n"
    "Hey Jude — The Beatles\n"
    "Purple Rain — Prince\n"
    "Born to Run — Bruce Springsteen"
)


def tab_playlist() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "Quantum Fisher-Yates produces a truly uniform permutation of your playlist — "
        "every order is equally likely, unlike most media player shuffle algorithms."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        songs_raw = st.text_area(
            "Songs / items (one per line)",
            value=_DEFAULT_SONGS,
            height=220,
            key="pl_songs",
        )
        songs = [s.strip() for s in songs_raw.strip().splitlines() if s.strip()]
        shuffle_btn = st.button(
            "🎵  Quantum Shuffle", key="btn_pl", use_container_width=True
        )

    wave_ph = _wave_setup(
        col_anim, (0, max(len(songs), 1)), "Playlist Superposition", "pl_wave_idle"
    )

    if shuffle_btn:
        if len(songs) < 2:
            st.warning("Enter at least 2 songs.")
            return

        with st.spinner("⚛  Quantum shuffling playlist…"):
            shuffled = quantum_shuffle(songs)

        # Collapse to the original index of the song that ended up first
        original_idx = float(songs.index(shuffled[0])) if shuffled[0] in songs else 0.0
        with col_anim:
            _wave_animation_loop(
                wave_ph, original_idx, (0, len(songs)), "Playlist Shuffle", "pl_wave"
            )

        st.markdown("---")
        items_html = "".join(
            f'<div class="playlist-item">'
            f'<span class="playlist-idx">{i + 1:02d}</span>'
            f"<span>🎵 {song}</span>"
            f"</div>"
            for i, song in enumerate(shuffled)
        )
        st.markdown(items_html, unsafe_allow_html=True)


# ─── 🎨 Color Palette ─────────────────────────────────────────────────────────


def tab_colors() -> None:
    st.markdown(
        '<p style="font-family:monospace;color:#8888aa;margin-bottom:1rem">'
        "Three 8-qubit Hadamard circuits sample independent R, G, B channels (0–255) "
        "for each colour. Results are quantum-random with perfect uniformity."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_anim = st.columns([1, 1], gap="large")

    with col_ctrl:
        n_colors = st.slider("Number of colors", 1, 10, 5, key="col_n")
        gen_btn = st.button(
            "🎨  Generate Quantum Palette", key="btn_col", use_container_width=True
        )

    wave_ph = _wave_setup(col_anim, (0, 255), "RGB Superposition", "col_wave_idle")

    if gen_btn:
        with st.spinner("⚛  Measuring quantum colour states…"):
            colors = quantum_colors(int(n_colors))

        # Collapse to the R channel value of the first colour
        with col_anim:
            _wave_animation_loop(
                wave_ph, float(colors[0][0]), (0, 255), "RGB Sampling", "col_wave"
            )

        st.markdown("---")
        swatches_html = '<div class="color-swatch-row">'
        for r, g, b in colors:
            hex_val = rgb_to_hex(r, g, b)
            name = color_name_approx(r, g, b)
            swatches_html += (
                f'<div class="color-swatch">'
                f'<div class="color-block" style="background:{hex_val};'
                f'box-shadow:0 4px 20px {hex_val}66"></div>'
                f'<div class="color-hex">{hex_val.upper()}</div>'
                f'<div class="color-name">{name}</div>'
                f"</div>"
            )
        swatches_html += "</div>"
        st.markdown(swatches_html, unsafe_allow_html=True)

        with st.expander("📋 Export CSS Variables", expanded=False):
            css_vars = "\n".join(
                f"  --color-{i + 1}: {rgb_to_hex(r, g, b).upper()};"
                for i, (r, g, b) in enumerate(colors)
            )
            st.code(f":root {{\n{css_vars}\n}}", language="css")


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="font-family:monospace">
            <div style="color:#00e5ff;font-size:1rem;letter-spacing:0.1em;
            text-transform:uppercase;margin-bottom:0.8rem">⚛ Quantum Dice</div>
            <div style="color:#8888aa;font-size:0.78rem;line-height:1.7">
            All randomness is generated via <b style="color:#7b2fff">PennyLane</b>
            quantum circuits using Hadamard gates and projective measurement.<br><br>
            <b style="color:#00e5ff">Why quantum?</b><br>
            Classical PRNGs are deterministic — given the seed they're fully predictable.
            Quantum measurement is fundamentally non-deterministic by the laws of physics.
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown(
            """
            <div style="font-family:monospace;font-size:0.78rem;color:#8888aa">
            <div style="color:#00e5ff;margin-bottom:0.5rem">⚛ Quantum Facts</div>
            • A qubit in superposition has no definite value until measured<br><br>
            • The Hadamard gate creates equal probability for 0 and 1<br><br>
            • Measurement collapses the wavefunction irreversibly<br><br>
            • 3 qubits encode 2³ = 8 states simultaneously<br><br>
            • Rejection sampling preserves uniformity when 2ⁿ ≠ N
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown(
            """
            <div style="background:rgba(13,13,43,0.7);border:1px solid rgba(123,47,255,0.3);
            border-radius:10px;padding:0.9rem 1rem;font-family:monospace">
              <div style="color:#00e5ff;font-size:0.72rem;letter-spacing:0.12em;
              text-transform:uppercase;margin-bottom:0.55rem">Creator</div>
              <div style="color:#e0e0ff;font-size:0.92rem;font-weight:600">Lucas Reis</div>
              <div style="color:#8888aa;font-size:0.75rem;margin-top:0.2rem;
              margin-bottom:0.65rem">Machine Learning Engineer</div>
              <div style="display:flex;gap:0.6rem;flex-wrap:wrap">
                <a href="https://www.linkedin.com/in/lucas-dos-reis-lrs/"
                   target="_blank" rel="noopener"
                   style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:rgba(0,119,181,0.18);border:1px solid rgba(0,119,181,0.45);
                   border-radius:6px;padding:0.25rem 0.6rem;color:#5bb8ff;
                   font-size:0.75rem;text-decoration:none">
                  🔗 LinkedIn
                </a>
                <a href="https://github.com/Lrs50"
                   target="_blank" rel="noopener"
                   style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:rgba(123,47,255,0.15);border:1px solid rgba(123,47,255,0.4);
                   border-radius:6px;padding:0.25rem 0.6rem;color:#b88fff;
                   font-size:0.75rem;text-decoration:none">
                  🐙 GitHub
                </a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style="font-family:monospace;font-size:0.72rem;color:#444466;
            text-align:center;margin-top:0.6rem">
            Built with PennyLane · Streamlit · Plotly<br>
            Quantum randomness · No classical PRNGs
            </div>
            """,
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    _sidebar()

    tab_labels = [
        "🎲 Dice Roll",
        "🪙 Coin Flip",
        "🔢 Random Number",
        "👥 Group Divider",
        "🎰 Lottery",
        "🔐 Password",
        "🎵 Playlist",
        "🎨 Colors",
    ]
    tab_fns = [
        tab_dice,
        tab_coin,
        tab_random_number,
        tab_group_divider,
        tab_lottery,
        tab_password,
        tab_playlist,
        tab_colors,
    ]

    for tab, fn in zip(st.tabs(tab_labels), tab_fns):
        with tab:
            fn()

    st.markdown(
        """
        <div style="text-align:center;font-family:monospace;font-size:0.72rem;
        color:#333355;margin-top:2rem;padding:1rem;
        border-top:1px solid rgba(123,47,255,0.15)">
        ⚛ Quantum Dice · Created by
        <a href="https://github.com/Lrs50" target="_blank" rel="noopener"
           style="color:#7b2fff;text-decoration:none">Lucas Reis</a>
        · Powered by PennyLane default.qubit · All measurements are quantum-mechanically random
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
