"""
quantum_engine.py
─────────────────
PennyLane quantum circuits for all randomness tools.

All circuits use the default.qubit simulator with Hadamard gates to
create uniform superposition states, then sample via quantum measurement.
Rejection sampling ensures perfect uniformity when 2^n > target range.
"""

from __future__ import annotations

import math
import string
from typing import List, Tuple

import numpy as np
import pennylane as qml

# ─── Low-level primitives ─────────────────────────────────────────────────────


def _n_qubits(max_val: int) -> int:
    """Minimum qubits needed to represent integers 0 … max_val."""
    if max_val <= 0:
        return 1
    return max(1, math.ceil(math.log2(max_val + 1)))


def _bits_to_int(bits: List[int]) -> int:
    """Convert bit list (MSB first) to integer."""
    value = 0
    for b in bits:
        value = (value << 1) | int(b)
    return value


def _sample_bits(n_qubits: int) -> List[int]:
    """
    Sample n_qubits bits from an equal-superposition quantum circuit.

    Circuit: |0⟩⊗n  ──  H⊗n  ──  ⟨M⟩
    Each wire has independent 50/50 probability.
    """
    dev = qml.device("default.qubit", wires=n_qubits, shots=1)

    @qml.qnode(dev)
    def circuit():
        for i in range(n_qubits):
            qml.Hadamard(wires=i)
        return qml.sample(wires=list(range(n_qubits)))

    result = np.array(circuit()).flatten().astype(int)
    return result.tolist()


def _sample_batch(n_qubits: int, n_shots: int) -> List[List[int]]:
    """
    Sample n_shots independent measurements from the same H⊗n circuit.
    Returns a list of n_shots bit-lists, each of length n_qubits.
    More efficient than calling _sample_bits repeatedly.
    """
    dev = qml.device("default.qubit", wires=n_qubits, shots=n_shots)

    @qml.qnode(dev)
    def circuit():
        for i in range(n_qubits):
            qml.Hadamard(wires=i)
        return qml.sample(wires=list(range(n_qubits)))

    result = np.array(circuit())

    # Normalise shape to (n_shots, n_qubits)
    if result.ndim == 1:
        if n_qubits == 1:
            result = result.reshape(-1, 1)
        else:
            result = result.reshape(1, -1)

    return result.astype(int).tolist()


def _uniform_int(n: int, max_attempts: int = 200) -> int:
    """
    Uniformly distributed integer in [0, n] using rejection sampling.
    Fallback to numpy if exhausted (astronomically unlikely).
    """
    if n <= 0:
        return 0
    n_qubits = _n_qubits(n)
    for _ in range(max_attempts):
        bits = _sample_bits(n_qubits)
        value = _bits_to_int(bits)
        if value <= n:
            return value
    return int(np.random.randint(0, n + 1))


# ─── Public quantum tools ──────────────────────────────────────────────────────


def quantum_coin_flip() -> int:
    """
    1-qubit Hadamard circuit.

    Circuit: |0⟩ ──── H ──── ⟨M⟩

    Returns 0 (Heads) or 1 (Tails), each with P = 0.5.
    """
    return _sample_bits(1)[0]


def quantum_dice_roll() -> Tuple[int, List[int]]:
    """
    3-qubit Hadamard circuit → standard six-sided die.

    Circuit:
        |0⟩ ── H ── ⟨M⟩
        |0⟩ ── H ── ⟨M⟩
        |0⟩ ── H ── ⟨M⟩

    3 bits encode 8 states (0–7).  Rejection sampling maps to 1–6 uniformly.
    Returns (face 1-6, raw bits [b2, b1, b0]).
    """
    for _ in range(50):
        bits = _sample_bits(3)
        value = _bits_to_int(bits)  # 0–7
        if value < 6:
            return value + 1, bits
    # Fallback (P(fallback) < 2^-50 per attempt)
    val = int(np.random.randint(1, 7))
    return val, [int(b) for b in f"{val - 1:03b}"]


def quantum_random_int(n: int) -> Tuple[int, int, List[int]]:
    """
    Random integer in [0, n] using ⌈log₂(n+1)⌉ qubits.

    Returns (value, n_qubits_used, raw_bits).
    """
    n_qubits = _n_qubits(n)
    value = _uniform_int(n)
    bits = [int(b) for b in f"{value:0{n_qubits}b}"]
    return value, n_qubits, bits


def quantum_shuffle(items: List) -> List:
    """
    Quantum Fisher-Yates shuffle — O(n) circuit calls via batch sampling.

    For each position i from n-1 down to 1, picks j ∈ [0, i] uniformly.
    """
    items = list(items)
    n = len(items)
    if n <= 1:
        return items

    # Batch sample enough bits (3× buffer for rejection)
    max_val = n - 1
    n_qubits = _n_qubits(max_val)
    batch = _sample_batch(n_qubits, (n - 1) * 4)
    batch_iter = iter(batch)

    for i in range(n - 1, 0, -1):
        j = None
        # Try to find a valid j from the batch
        for bits in batch_iter:
            val = _bits_to_int(bits)
            if val <= i:
                j = val
                break
        if j is None:
            j = _uniform_int(i)  # fallback (rare)
        items[i], items[j] = items[j], items[i]

    return items


def quantum_group_divide(
    names: List[str], n_groups: int
) -> Tuple[List[List[str]], List[str]]:
    """
    Quantum shuffle then balanced partition.

    For M names into K groups:
      base_size = M // K
      first (M % K) groups get base_size + 1 members, rest get base_size.

    Example: 15 names, 4 groups  →  sizes [4, 4, 4, 3]

    Returns (groups, shuffled_order).
    """
    shuffled = quantum_shuffle(names)
    n = len(shuffled)
    base_size = n // n_groups
    remainder = n % n_groups

    groups: List[List[str]] = []
    idx = 0
    for i in range(n_groups):
        size = base_size + (1 if i < remainder else 0)
        groups.append(shuffled[idx : idx + size])
        idx += size

    return groups, shuffled


def quantum_lottery(
    participants: List[str], n_winners: int
) -> Tuple[List[str], List[str]]:
    """
    Select n_winners from participants via quantum shuffle.

    Returns (winners, non_winners).
    """
    shuffled = quantum_shuffle(participants)
    return shuffled[:n_winners], shuffled[n_winners:]


def quantum_password(
    length: int = 16,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Quantum-random password.

    One batch circuit call samples all character indices at once.
    Rejection sampling ensures uniform distribution over the charset.
    """
    charset = string.ascii_lowercase
    if use_upper:
        charset += string.ascii_uppercase
    if use_digits:
        charset += string.digits
    if use_symbols:
        charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    if not charset:
        charset = string.ascii_lowercase

    max_idx = len(charset) - 1
    n_qubits = _n_qubits(max_idx)
    # Sample with 3× buffer to account for rejection
    batch = _sample_batch(n_qubits, length * 4)

    chars: List[str] = []
    for bits in batch:
        idx = _bits_to_int(bits)
        if idx <= max_idx:
            chars.append(charset[idx])
        if len(chars) == length:
            break

    # Rare fallback
    while len(chars) < length:
        chars.append(charset[_uniform_int(max_idx)])

    return "".join(chars)


def quantum_colors(n_colors: int = 5) -> List[Tuple[int, int, int]]:
    """
    Generate n_colors random RGB tuples (each channel 0–255).

    Uses a single 8-qubit batch circuit for efficiency.
    """
    # 8 qubits → 0–255; need 3 channels per color
    n_samples = n_colors * 3 * 2  # 2× buffer (rejection rate ≈ 0 for 8-qubits/256)
    batch = _sample_batch(8, n_samples)

    channels: List[int] = []
    for bits in batch:
        val = _bits_to_int(bits)  # 0–255, always valid
        channels.append(val)
        if len(channels) == n_colors * 3:
            break

    # Pack into RGB tuples
    colors = []
    for i in range(0, len(channels) - 2, 3):
        colors.append((channels[i], channels[i + 1], channels[i + 2]))
        if len(colors) == n_colors:
            break

    return colors


# ─── Metadata helpers ─────────────────────────────────────────────────────────


def circuit_info(tool: str, n: int = 0) -> dict:
    """Return circuit metadata for the given tool (used in UI diagrams)."""
    info = {
        "coin": {
            "n_qubits": 1,
            "diagram": "|0⟩ ──── H ──── ⟨M⟩",
            "description": "Hadamard gate puts qubit in |+⟩ = (|0⟩+|1⟩)/√2 → equal 50/50",
        },
        "dice": {
            "n_qubits": 3,
            "diagram": ("|0⟩ ── H ── ⟨M⟩\n" "|0⟩ ── H ── ⟨M⟩\n" "|0⟩ ── H ── ⟨M⟩"),
            "description": "3 qubits encode 8 outcomes → rejection-sample to 1–6 (uniform)",
        },
        "random": {
            "n_qubits": _n_qubits(n) if n > 0 else "⌈log₂(N+1)⌉",
            "diagram": ("|0⟩ ── H ── ⟨M⟩\n" "  ⋮    ⋮     ⋮  \n" "|0⟩ ── H ── ⟨M⟩"),
            "description": (
                f"⌈log₂({n}+1)⌉ qubits → rejection-sample to [0,{n}]"
                if n > 0
                else "⌈log₂(N+1)⌉ qubits → rejection-sample to [0,N]"
            ),
        },
        "shuffle": {
            "n_qubits": "variable",
            "diagram": "Quantum Fisher-Yates:\nfor i = n-1 … 1:\n  j ~ Uniform(0, i)\n  swap(i, j)",
            "description": "Quantum Fisher-Yates produces perfectly uniform permutations",
        },
    }
    return info.get(tool, {})
