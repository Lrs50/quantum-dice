"""
animations.py
─────────────
Plotly-based Bloch sphere animations, quantum wave collapse, and probability
visualisations.

Bloch sphere physics:
  |0⟩  →  north pole  (0, 0, +1)
  |1⟩  →  south pole  (0, 0, -1)
  |+⟩  →  equator     (+1, 0, 0)   (after Hadamard)

Wave collapse physics:
  Phase 1: ψ(x) = Σ sin(kx + φk) / k  — interference pattern (superposition)
  Phase 2: ψ(x) → Gaussian spike at result_x  — wavefunction collapse
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


# ─── Colour palette ───────────────────────────────────────────────────────────
_BG        = "rgba(10, 10, 26, 0.0)"          # transparent (inherits dark theme)
_SPHERE    = "rgba(123, 47, 255, 0.12)"
_WIRE_DIM  = "rgba(123, 47, 255, 0.22)"
_WIRE_AXIS = "rgba(255, 255, 255, 0.12)"
_CYAN      = "#00e5ff"
_PURPLE    = "#7b2fff"
_GREEN     = "#00ff88"


# ─── Sphere geometry helpers ─────────────────────────────────────────────────

def _wireframe_traces() -> list[go.BaseTraceType]:
    """Latitude + longitude wire circles forming the Bloch sphere skeleton."""
    traces: list[go.BaseTraceType] = []
    phi = np.linspace(0, 2 * np.pi, 80)

    # Latitude circles (constant θ)
    for lat_deg in range(-75, 90, 30):
        lat = np.deg2rad(lat_deg)
        r = np.cos(lat)
        z = np.sin(lat)
        traces.append(go.Scatter3d(
            x=r * np.cos(phi), y=r * np.sin(phi), z=np.full_like(phi, z),
            mode="lines", line=dict(color=_WIRE_DIM, width=1),
            hoverinfo="skip", showlegend=False,
        ))

    # Longitude circles (meridians)
    theta = np.linspace(0, 2 * np.pi, 80)
    for lon_deg in range(0, 180, 45):
        lon = np.deg2rad(lon_deg)
        traces.append(go.Scatter3d(
            x=np.sin(theta) * np.cos(lon),
            y=np.sin(theta) * np.sin(lon),
            z=np.cos(theta),
            mode="lines", line=dict(color=_WIRE_DIM, width=1),
            hoverinfo="skip", showlegend=False,
        ))

    # Z-axis
    traces.append(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[-1.15, 1.15],
        mode="lines", line=dict(color=_WIRE_AXIS, width=2),
        hoverinfo="skip", showlegend=False,
    ))

    # Pole labels  |0⟩ / |1⟩
    traces.append(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[1.35, -1.35],
        mode="text", text=["|0⟩", "|1⟩"],
        textfont=dict(color="#aaaacc", size=12, family="monospace"),
        showlegend=False,
    ))

    return traces


def _state_vector_traces(
    x: float, y: float, z: float, color: str = _CYAN
) -> list[go.BaseTraceType]:
    """Arrow (line + tip sphere) representing the quantum state vector."""
    return [
        go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, z],
            mode="lines",
            line=dict(color=color, width=5),
            hoverinfo="skip", showlegend=False,
        ),
        go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode="markers+text",
            marker=dict(size=9, color=color, symbol="circle",
                        line=dict(color="white", width=1)),
            text=["ψ"], textposition="top center",
            textfont=dict(color=color, size=13, family="monospace"),
            showlegend=False,
        ),
    ]


def _fig_layout(title: str = "", height: int = 340) -> dict:
    return dict(
        title=dict(text=title, font=dict(color=_CYAN, size=13, family="monospace"), x=0.5),
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        scene=dict(
            bgcolor="rgba(10,10,30,0.85)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False, range=[-1.5, 1.5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False, range=[-1.5, 1.5]),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False, range=[-1.6, 1.6]),
            camera=dict(eye=dict(x=1.5, y=1.3, z=0.7)),
            aspectmode="cube",
        ),
        margin=dict(l=0, r=0, t=35, b=0),
        height=height,
    )


# ─── Public: static Bloch sphere ─────────────────────────────────────────────

def bloch_sphere_static(
    state: tuple[float, float, float] = (0.0, 0.0, 1.0),
    title: str = "",
    vector_color: str = _CYAN,
    height: int = 340,
) -> go.Figure:
    """Static Bloch sphere with a given state vector (x, y, z)."""
    x, y, z = state
    data = _wireframe_traces() + _state_vector_traces(x, y, z, vector_color)
    fig = go.Figure(data=data)
    fig.update_layout(**_fig_layout(title, height))
    return fig


# ─── Animation path computation ───────────────────────────────────────────────

def _animation_path(outcome: int, n_frames: int = 24) -> list[tuple[float, float, float]]:
    """
    Compute state-vector trajectory for the Bloch sphere animation.

    Phase 1 (first half):   |0⟩ = (0,0,1)  →  equator (superposition, spinning φ)
    Phase 2 (second half):  equator  →  |0⟩ = (0,0,1) or |1⟩ = (0,0,-1)
    """
    vectors: list[tuple[float, float, float]] = []
    half = n_frames // 2
    final_z = 1.0 if outcome == 0 else -1.0

    # Phase 1: rotate toward equator while spinning in φ
    for i in range(half):
        t = i / max(half - 1, 1)
        theta = (np.pi / 2) * t           # polar: 0 → π/2
        phi   = 2.5 * np.pi * t           # azimuthal spin
        x = float(np.sin(theta) * np.cos(phi))
        y = float(np.sin(theta) * np.sin(phi))
        z = float(np.cos(theta))
        vectors.append((x, y, z))

    # Phase 2: collapse from equator to measurement outcome
    eq_x, eq_y, eq_z = vectors[-1]
    for i in range(half):
        t = i / max(half - 1, 1)
        # Smooth-step easing
        t_ease = t * t * (3 - 2 * t)
        x = float(eq_x * (1 - t_ease))
        y = float(eq_y * (1 - t_ease))
        z = float(eq_z * (1 - t_ease) + final_z * t_ease)
        vectors.append((x, y, z))

    return vectors


# ─── Public: animated Bloch sphere ────────────────────────────────────────────

def bloch_sphere_animated(
    outcome: int,
    n_frames: int = 24,
    height: int = 360,
) -> go.Figure:
    """
    Plotly animated Bloch sphere figure (uses Plotly frames + play button).

    outcome: 0 → collapses to |0⟩ (north pole)
             1 → collapses to |1⟩ (south pole)
    """
    path = _animation_path(outcome, n_frames)
    wireframe = _wireframe_traces()
    half = n_frames // 2

    def _vec_color(i: int) -> str:
        if i < half:
            return _CYAN        # superposition phase
        # Collapse phase: interpolate cyan → green/purple
        t = (i - half) / max(half - 1, 1)
        if outcome == 0:
            r = int(0   * (1 - t) + 0    * t)
            g = int(229 * (1 - t) + 255  * t)
            b = int(255 * (1 - t) + 136  * t)
        else:
            r = int(0   * (1 - t) + 123  * t)
            g = int(229 * (1 - t) + 47   * t)
            b = int(255 * (1 - t) + 255  * t)
        return f"rgb({r},{g},{b})"

    x0, y0, z0 = path[0]
    initial_data = wireframe + _state_vector_traces(x0, y0, z0, _CYAN)

    frames = [
        go.Frame(
            data=wireframe + _state_vector_traces(x, y, z, _vec_color(i)),
            name=str(i),
        )
        for i, (x, y, z) in enumerate(path)
    ]

    fig = go.Figure(data=initial_data, frames=frames)
    fig.update_layout(
        **_fig_layout("Quantum State Evolution", height),
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "x": 0.5, "y": -0.02,
            "xanchor": "center", "yanchor": "top",
            "buttons": [
                {
                    "label": "▶  Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 80, "redraw": True},
                        "fromcurrent": False,
                        "transition": {"duration": 40, "easing": "linear"},
                        "mode": "immediate",
                    }],
                },
                {
                    "label": "⏸  Pause",
                    "method": "animate",
                    "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                },
            ],
        }],
        sliders=[{
            "active": 0,
            "currentvalue": {"visible": False},
            "pad": {"t": 50},
            "steps": [
                {
                    "args": [[str(i)], {"frame": {"duration": 80, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                    "label": "",
                    "method": "animate",
                }
                for i in range(len(frames))
            ],
            "x": 0.05, "len": 0.9, "y": 0,
            "bgcolor": "rgba(123,47,255,0.3)",
            "bordercolor": "rgba(123,47,255,0.6)",
        }],
    )
    return fig


# ─── Loop-based Bloch sphere animation (st.empty approach) ───────────────────

def bloch_sphere_frames(
    outcome: int,
    n_frames: int = 20,
) -> list[go.Figure]:
    """
    Pre-compute a list of static Bloch sphere figures for frame-by-frame
    animation via st.empty() in Streamlit.
    """
    path = _animation_path(outcome, n_frames)
    half = n_frames // 2
    figs = []
    for i, sv in enumerate(path):
        if i < half:
            color = _CYAN
            title = f"Superposition  |frame {i + 1}|"
        else:
            color = _GREEN if outcome == 0 else _PURPLE
            title = "⚡ Collapsing…"
        figs.append(bloch_sphere_static(sv, title=title, vector_color=color))
    return figs


# ─── Probability histogram ────────────────────────────────────────────────────

def probability_histogram(
    n_outcomes: int,
    result: int | None = None,
    labels: list[str] | None = None,
    title: str = "Quantum Probability Distribution",
) -> go.Figure:
    """
    Uniform probability bar chart with the measured outcome highlighted.

    n_outcomes: total number of equally-likely outcomes
    result:     1-indexed result to highlight (None → no highlight)
    labels:     custom x-axis labels (defaults to 1..n_outcomes)
    """
    p = 1.0 / n_outcomes
    xs = labels or [str(i + 1) for i in range(n_outcomes)]
    ys = [p] * n_outcomes
    colors = [
        _CYAN if (result is not None and i + 1 == result) else "rgba(123, 47, 255, 0.45)"
        for i in range(n_outcomes)
    ]

    fig = go.Figure(go.Bar(
        x=xs,
        y=ys,
        marker_color=colors,
        marker_line=dict(color="rgba(0,229,255,0.3)", width=1),
        text=[f"{p * 100:.1f}%" for _ in ys],
        textposition="outside",
        textfont=dict(color="#aaaacc", size=11),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=_CYAN, size=13, family="monospace"), x=0.5),
        paper_bgcolor=_BG,
        plot_bgcolor="rgba(10,10,30,0.85)",
        font=dict(color="#ccccee", family="monospace"),
        xaxis=dict(
            title="Outcome",
            gridcolor="rgba(123,47,255,0.15)",
            linecolor="rgba(123,47,255,0.3)",
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            title="Probability",
            tickformat=".0%",
            gridcolor="rgba(123,47,255,0.15)",
            linecolor="rgba(123,47,255,0.3)",
            range=[0, p * 1.6],
        ),
        margin=dict(l=10, r=10, t=45, b=30),
        height=260,
        bargap=0.25,
    )
    return fig


# ─── Quantum wave helpers ─────────────────────────────────────────────────────

def _make_interference(
    x: np.ndarray, lo: float, span: float, phase: float
) -> np.ndarray:
    """Sum-of-sines interference pattern for the given animation phase."""
    f = 4.0  # base frequency (cycles across x span)
    y = np.zeros_like(x)
    for k in range(1, 8):
        y += np.sin(k * (x - lo) / span * 2 * np.pi * f + phase * k * 1.8) / k
    mx = float(np.max(np.abs(y))) or 1.0
    return y / mx * 0.85


def _make_gaussian(
    x: np.ndarray, result_x: float, sigma: float, span: float
) -> np.ndarray:
    """Normalised Gaussian centred at result_x with width sigma * span."""
    g = np.exp(-0.5 * ((x - result_x) / (sigma * span)) ** 2)
    mx = float(g.max()) or 1.0
    return g / mx


def _smooth_lerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Smooth-step interpolation between two waveforms."""
    t_ease = t * t * (3 - 2 * t)
    return a * (1 - t_ease) + b * t_ease


def _wave_layout(label: str, height: int) -> dict:
    """Shared Plotly layout for all wave figures."""
    return dict(
        title=dict(text=label, font=dict(color=_CYAN, size=13, family="monospace"), x=0.5),
        paper_bgcolor=_BG,
        plot_bgcolor="rgba(10,10,30,0.85)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(
            showgrid=False, zeroline=True, zerolinecolor="rgba(123,47,255,0.2)",
            showticklabels=False, visible=False, range=[-1.3, 1.3],
        ),
        margin=dict(l=10, r=10, t=35, b=10),
        height=height,
    )


# ─── Public: idle wave ────────────────────────────────────────────────────────

def quantum_wave_idle(
    x_range: tuple[float, float] = (0.0, 1.0),
    label: str = "Quantum State",
    height: int = 280,
) -> go.Figure:
    """
    Static low-amplitude sine wave shown before the user clicks — the
    'ready' state of the quantum system.
    """
    x = np.linspace(x_range[0], x_range[1], 400)
    span = (x_range[1] - x_range[0]) or 1.0
    y = 0.15 * np.sin(4 * np.pi * (x - x_range[0]) / span)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(123,47,255,0.08)",
        line=dict(color=_PURPLE, width=2),
        hoverinfo="skip",
        showlegend=False,
    ))
    mid = (x_range[0] + x_range[1]) / 2
    fig.add_annotation(
        x=mid, y=0.5,
        text="|ψ⟩  awaiting measurement…",
        showarrow=False,
        font=dict(color=_WIRE_DIM, size=12, family="monospace"),
        xref="x", yref="paper",
    )
    fig.update_layout(**_wave_layout(label, height))
    return fig


# ─── Public: wave collapse frame list (server-side loop) ─────────────────────

def quantum_wave_frames(
    result_x: float,
    x_range: tuple[float, float] = (0.0, 1.0),
    n_frames: int = 28,
    label: str = "Wavefunction Collapse",
    height: int = 280,
) -> list[go.Figure]:
    """
    Pre-compute a list of static wave figures for frame-by-frame animation
    via st.empty() in Streamlit.  Results are only shown after the loop ends.

    Phase 1 (first half): ψ(x) = Σ sin(kx + φk)/k — interference (superposition)
    Phase 2 (second half): lerp toward narrow Gaussian at result_x (collapse)
    """
    lo, hi = float(x_range[0]), float(x_range[1])
    span = (hi - lo) or 1.0
    x = np.linspace(lo, hi, 500)
    half = n_frames // 2

    # Pre-compute the frozen interference wave used as the collapse start-point
    frozen_interference = _make_interference(x, lo, span, phase=2 * np.pi)

    figs: list[go.Figure] = []

    for i in range(n_frames):
        is_last = i == n_frames - 1

        if i < half:
            phase = (i / max(half - 1, 1)) * 2 * np.pi
            y = _make_interference(x, lo, span, phase)
            color = _PURPLE
            fill_alpha = 0.08 + 0.06 * (i / half)
            step_label = f"{label}  ·  |ψ⟩ superposition"
        else:
            t = (i - half) / max(half - 1, 1)          # 0 → 1
            sigma = 0.40 * (1 - t) + 0.025 * t         # wide → narrow Gaussian
            gauss = _make_gaussian(x, result_x, sigma, span)
            y = _smooth_lerp(frozen_interference, gauss, t)
            # Colour shifts purple → cyan as it collapses
            r_ch = int(123 * (1 - t))
            g_ch = int(47 * (1 - t) + 229 * t)
            color = f"rgb({r_ch},{g_ch},{255})"
            fill_alpha = 0.14 + 0.08 * t
            step_label = f"{label}  ·  collapsing…"

        # Final frame: sharp collapsed Gaussian in cyan
        if is_last:
            y = _make_gaussian(x, result_x, 0.025, span)
            color = _CYAN
            fill_alpha = 0.15
            step_label = f"{label}  ·  ⚡ collapsed"

        trace = go.Scatter(
            x=x, y=y,
            mode="lines",
            fill="tozeroy",
            fillcolor=f"rgba(123,47,255,{fill_alpha:.2f})",
            line=dict(color=color, width=2.5),
            hoverinfo="skip",
            showlegend=False,
        )
        fig = go.Figure(data=[trace])
        fig.update_layout(**_wave_layout(step_label, height))
        figs.append(fig)

    return figs
