# ⚛ Quantum Dice

> True randomness via quantum superposition and wavefunction collapse.

A visually stunning web app that generates genuinely non-deterministic random
numbers using real quantum circuits — powered by **PennyLane** and **Streamlit**.

---

## Features

| Tab | What it does | Qubits |
|-----|-------------|--------|
| 🎲 **Dice Roll** | Roll 1–6 dice, Bloch sphere animation | 3 per die |
| 🪙 **Coin Flip** | Single or batch flips, live stats | 1 |
| 🔢 **Random Number** | Any range [min, max], no modulo bias | ⌈log₂(N+1)⌉ |
| 👥 **Group Divider** | Paste names → quantum-shuffled balanced groups | variable |
| 🎰 **Lottery** | Pick K winners from M participants | variable |
| 🔐 **Password** | Quantum-random characters, entropy meter | 7 per char |
| 🎵 **Playlist Shuffle** | Perfectly uniform Fisher-Yates shuffle | variable |
| 🎨 **Color Palette** | Random RGB palettes with CSS export | 8 per channel |

All randomness is generated from **Hadamard-gate quantum circuits** via
PennyLane's `default.qubit` simulator — no classical PRNGs involved.

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup & Run

```bash
# Clone / enter the project directory
cd quantum-dice

# Install dependencies via uv
uv sync

# Launch the app
uv run streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

---

## Project Structure

```
quantum-dice/
├── app.py               # Streamlit UI — 8 tabs, CSS injection, animations
├── quantum_engine.py    # PennyLane circuits (coin, dice, shuffle, password…)
├── animations.py        # Plotly 3D Bloch sphere + probability histograms
├── utils.py             # Group balancing, colour tools, password analysis
├── pyproject.toml       # uv / PEP 517 dependency manifest
├── .env                 # Runtime config (animation frames, defaults)
├── .streamlit/
│   └── config.toml      # Streamlit dark quantum theme
└── static/
    └── styles.css       # Quantum-void CSS (particles, glows, animations)
```

---

## Quantum Background

### Why quantum randomness?

Classical PRNGs are **deterministic**: given the seed they produce the same
sequence every time.  A quantum measurement of a qubit in superposition is
**fundamentally non-deterministic** — the outcome cannot be predicted even with
complete knowledge of the system.

### The circuit

Every tool uses the same core primitive:

```
|0⟩ ──── H ──── ⟨M⟩
```

The **Hadamard gate** (H) creates the equal superposition:

```
|+⟩ = (|0⟩ + |1⟩) / √2
```

Measuring |+⟩ yields 0 or 1 with P = 0.5 each.  Combining n qubits gives
2ⁿ equally-likely outcomes.  **Rejection sampling** discards values outside
the target range, preserving perfect uniformity with no modulo bias.

### Fisher-Yates quantum shuffle

For a list of n items, the algorithm picks a random swap partner for each
position from i = n−1 down to 1.  Each swap index is drawn from a fresh
quantum circuit, producing a **perfectly uniform permutation**.

---

## Configuration

Edit `.env` to change defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANIMATION_FRAMES` | 20 | Bloch sphere animation frames |
| `ANIMATION_SPEED_MS` | 80 | Frame delay in ms |
| `DEFAULT_PASSWORD_LENGTH` | 16 | Password tab default length |
| `DEFAULT_RANDOM_MAX` | 100 | Random number tab default N |
| `REJECTION_SAMPLE_LIMIT` | 200 | Max rejection-sampling attempts |

---

## Tech Stack

| Library | Version | Role |
|---------|---------|------|
| [Streamlit](https://streamlit.io) | ≥ 1.40 | Web UI framework |
| [PennyLane](https://pennylane.ai) | ≥ 0.39 | Quantum circuit simulation |
| [Plotly](https://plotly.com/python/) | ≥ 5.20 | 3D Bloch spheres, histograms |
| [NumPy](https://numpy.org) | ≥ 1.26 | Numerical operations |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ≥ 1.0 | `.env` config loading |
