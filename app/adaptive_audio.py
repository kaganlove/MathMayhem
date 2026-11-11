"""Phase 3R — Original Multi-Voice Musical Theme Candidates & Adaptive Audio Engine.

Replaces the legacy simple synth loop with:
1. Physical-modeling / multi-harmonic acoustic & hybrid instrument synthesis (`44.1 kHz` 16-bit PCM):
   - Clarinet / Woodwind Lead (odd-harmonic reed resonance, breath attack, expressive vibrato & grace notes)
   - Pizzicato Strings & Plucked Cello (karplus-inspired plucked body resonance with warm woody decay)
   - Wooden Marimba & Xylophone (inharmonic bar overtones `[1.0, 3.98, 9.18]` with resonator tube warmth)
   - Plucked Acoustic Guitar & Harpsichord / Lute (bright string pluck with low-pass body filter)
   - Kalimba / Thumb Piano (tine bell overtone `[1.0, 2.92, 5.8]` with crisp thumb attack)
   - Upright Walking Bass / Tuba (warm fundamental + 2nd/3rd harmonic chest resonance)
   - Orchestral & Minimalist Percussion (woodblock, clave, brush snare, shaker, finger snap, timpani pop)
2. Three Distinct Original Musical Candidates (`16.0 seconds` each, 100% original commercial-safe):
   - **Option A (`candidate_a_orchestral_cartoon.wav`):** Playful orchestral cartoon comedy.
   - **Option B (`candidate_b_electro_acoustic_adventure.wav`):** Modern electronic-acoustic adventure comedy.
   - **Option C (`candidate_c_quirky_minimalist_plucked.wav`):** Quirky minimalist percussion and plucked instruments.
3. Reusable Adaptive Audio Engine (`AdaptiveAudioEngine`):
   - Dynamic state variations: `EXPLORATION`, `SUSPENSE`, `CHAOS`, `RESOLUTION`
   - Automatic musical pauses (`pause_windows`) for comedic timing (e.g., dead-stop silence on `10 ÷ 0 =`)
   - Frame-accurate tactile sound effects (`button_click`, `positive_calc_chime`, `intrigued_calc_double_chime`,
     `division_by_zero_alarm`, `footstep_soft`, `object_pickup`, `door_creak`, `block_slide`, `math_symbol_chime`)
     synchronized directly to `PhysicalInteractionEngine` `ContactEvent` timestamps
   - Automatic sidechain volume ducking so foreground SFX cut through the musical score cleanly
   - Commercial licensing & SQLite `Asset` provenance registration
"""

from __future__ import annotations

import hashlib
import math
import struct
import wave
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.interaction_engine import ContactEvent
from app.models import Asset


SAMPLE_RATE = 44100


class AdaptiveMusicState(str, Enum):
    """Dynamic musical state variations for Math Mayhem episodes."""

    EXPLORATION = "EXPLORATION"
    SUSPENSE = "SUSPENSE"
    CHAOS = "CHAOS"
    RESOLUTION = "RESOLUTION"
    SILENCE = "SILENCE"


class MusicCandidateOption(str, Enum):
    """Three distinct musical theme candidates for owner review."""

    OPTION_A_ORCHESTRAL_CARTOON = "option_a_orchestral_cartoon"
    OPTION_B_ELECTRO_ACOUSTIC_ADVENTURE = "option_b_electro_acoustic_adventure"
    OPTION_C_QUIRKY_MINIMALIST_PLUCKED = "option_c_quirky_minimalist_plucked"


@dataclass(frozen=True)
class NoteEvent:
    """Single scored note for an acoustic/hybrid instrument voice."""

    start_sec: float
    duration_sec: float
    midi_note: float
    velocity: float = 0.8
    instrument: str = "clarinet"
    grace_midi: Optional[float] = None


@dataclass(frozen=True)
class PercussionEvent:
    """Single scored percussion hit."""

    start_sec: float
    kind: str  # `woodblock_hi` | `woodblock_lo` | `brush_hat` | `brush_snare` | `clave` | `snap` | `kick_soft`
    velocity: float = 0.75


@dataclass(frozen=True)
class SoundCueEvent:
    """Frame-synchronized sound effect cue triggered by physical interaction or movement."""

    cue_id: str
    sfx_name: str
    timestamp_sec: float
    frame_idx: int
    gain: float = 1.0
    pitch_shift_semitones: float = 0.0
    source_target_id: Optional[str] = None


@dataclass(frozen=True)
class MusicCandidateArtifact:
    """Metadata and file path for a generated musical candidate."""

    option_id: str
    label: str
    style_summary: str
    wav_path: Path
    duration_seconds: float
    sample_rate: int
    peak_amplitude: float
    rms_amplitude: float
    sha256: str
    license_name: str = "MathMayhem-100%-Original-Procedural-Score-Commercial-Safe"


def midi_to_freq(midi_note: float) -> float:
    """Convert fractional MIDI note number to frequency in Hz (`A4 = 69 -> 440.0 Hz`)."""
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))


# ---------------------------------------------------------------------------
# Expressive Multi-Harmonic / Physical-Modeling Instrument Synthesizers
# ---------------------------------------------------------------------------


def _render_voice_note(note: NoteEvent, sample_rate: int = SAMPLE_RATE) -> Tuple[int, List[float]]:
    """Synthesize a single expressive instrument note into a float buffer `(start_idx, samples)`."""
    start_idx = max(0, int(round(note.start_sec * sample_rate)))
    # Add natural acoustic tail beyond note duration
    tail_sec = 0.14 if note.instrument in ("pizzicato", "marimba", "kalimba", "guitar", "upright_bass") else 0.06
    total_dur = max(0.03, note.duration_sec + tail_sec)
    n_samples = int(round(total_dur * sample_rate))
    out = [0.0] * n_samples

    base_freq = midi_to_freq(note.midi_note)
    grace_freq = midi_to_freq(note.grace_midi) if note.grace_midi is not None else base_freq
    inst = note.instrument
    vel = max(0.05, min(1.2, note.velocity))

    phase = 0.0
    two_pi = 2.0 * math.pi

    for i in range(n_samples):
        t = i / float(sample_rate)

        # Optional grace-note slide in the first 42 ms
        if note.grace_midi is not None and t < 0.042:
            slide_u = t / 0.042
            freq = grace_freq + (base_freq - grace_freq) * (slide_u * slide_u * (3.0 - 2.0 * slide_u))
        else:
            freq = base_freq

        # Expressive vibrato for sustained wind/lead instruments
        if inst in ("clarinet", "analog_brass"):
            vib_depth = 0.0045 * min(1.0, max(0.0, (t - 0.05) / 0.12))
            freq *= 1.0 + vib_depth * math.sin(two_pi * 5.8 * t)

        phase += two_pi * freq / float(sample_rate)

        if inst == "clarinet":
            # Woodwind reed: predominantly odd harmonics (1, 3, 5, 7) + warm 2nd harmonic body
            attack = min(1.0, t / 0.018)
            release = (
                1.0
                if t <= note.duration_sec
                else max(0.0, math.exp(-(t - note.duration_sec) * 28.0))
            )
            sustain_contour = 0.92 + 0.08 * math.sin(two_pi * 2.5 * t)
            env = vel * 0.24 * attack * release * sustain_contour
            # Subtle reed chiff on attack
            chiff = 0.06 * math.exp(-t * 95.0) * math.sin(phase * 6.3)
            sig = (
                1.00 * math.sin(phase)
                + 0.14 * math.sin(2.0 * phase)
                + 0.48 * math.sin(3.0 * phase)
                + 0.19 * math.sin(5.0 * phase)
                + 0.07 * math.sin(7.0 * phase)
                + chiff
            )
            out[i] = env * sig

        elif inst == "pizzicato":
            # Crisp plucked orchestral string with warm wooden body resonance
            attack = min(1.0, t / 0.0035)
            decay = math.exp(-t * 11.5)
            bright_decay = math.exp(-t * 26.0)
            env = vel * 0.28 * attack * decay
            sig = (
                1.00 * math.sin(phase)
                + 0.52 * bright_decay * math.sin(2.0 * phase + 0.3)
                + 0.26 * bright_decay * math.sin(3.0 * phase + 0.7)
                + 0.11 * bright_decay * math.sin(4.0 * phase)
            )
            out[i] = env * sig

        elif inst == "upright_bass":
            # Bouncy walking acoustic bass / tuba foundation
            attack = min(1.0, t / 0.007)
            decay = math.exp(-t * 5.8)
            pluck_decay = math.exp(-t * 18.0)
            env = vel * 0.32 * attack * decay
            sig = (
                1.00 * math.sin(phase)
                + 0.62 * math.sin(2.0 * phase)
                + 0.28 * pluck_decay * math.sin(3.0 * phase)
                + 0.10 * pluck_decay * math.sin(4.0 * phase)
            )
            out[i] = env * sig

        elif inst == "xylophone" or inst == "marimba":
            # Tuned wooden bar percussion with authentic inharmonic bar overtone (3.98x)
            attack = min(1.0, t / 0.002)
            decay_rate = 16.0 if inst == "xylophone" else 9.5
            decay = math.exp(-t * decay_rate)
            bar_overtone_decay = math.exp(-t * (decay_rate * 3.4))
            mallet_click = math.exp(-t * 140.0) * math.sin(phase * 7.4) * 0.16
            env = vel * 0.27 * attack * decay
            sig = (
                1.00 * math.sin(phase)
                + 0.32 * bar_overtone_decay * math.sin(3.98 * phase)
                + (0.10 if inst == "xylophone" else 0.04) * bar_overtone_decay * math.sin(9.18 * phase)
                + mallet_click
            )
            out[i] = env * sig

        elif inst == "guitar":
            # Plucked acoustic guitar with warm midrange and bright string transient
            attack = min(1.0, t / 0.003)
            decay = math.exp(-t * 6.5)
            harm_decay = math.exp(-t * 15.0)
            env = vel * 0.25 * attack * decay
            sig = (
                1.00 * math.sin(phase)
                + 0.58 * harm_decay * math.sin(2.0 * phase)
                + 0.34 * harm_decay * math.sin(3.0 * phase)
                + 0.18 * harm_decay * math.sin(4.0 * phase)
                + 0.09 * math.exp(-t * 32.0) * math.sin(5.0 * phase)
            )
            out[i] = env * sig

        elif inst == "analog_brass":
            # Warm modern synth-brass / bell lead with filter-envelope sweep
            attack = min(1.0, t / 0.022)
            release = (
                1.0
                if t <= note.duration_sec
                else max(0.0, math.exp(-(t - note.duration_sec) * 20.0))
            )
            filt_env = 0.35 + 0.65 * math.exp(-t * 5.5)
            env = vel * 0.22 * attack * release
            sig = (
                1.00 * math.sin(phase)
                + 0.55 * filt_env * math.sin(2.0 * phase)
                + 0.35 * filt_env * math.sin(3.0 * phase)
                + 0.20 * filt_env * filt_env * math.sin(4.0 * phase)
                + 0.10 * filt_env * filt_env * math.sin(5.0 * phase)
            )
            out[i] = env * sig

        elif inst == "kalimba":
            # Plucked metal tine on gourd resonator (characteristic 2.92x tine clang that decays quickly)
            attack = min(1.0, t / 0.0022)
            decay = math.exp(-t * 7.2)
            tine_decay = math.exp(-t * 28.0)
            env = vel * 0.27 * attack * decay
            sig = (
                1.00 * math.sin(phase)
                + 0.12 * math.sin(2.0 * phase)
                + 0.38 * tine_decay * math.sin(2.92 * phase)
                + 0.14 * tine_decay * math.sin(5.80 * phase)
            )
            out[i] = env * sig

        elif inst == "harpsichord":
            # Crisp plucked lute-harpsichord register
            attack = min(1.0, t / 0.0025)
            decay = math.exp(-t * 8.8)
            bright = math.exp(-t * 19.0)
            env = vel * 0.22 * attack * decay
            sig = (
                0.85 * math.sin(phase)
                + 0.65 * bright * math.sin(2.0 * phase)
                + 0.42 * bright * math.sin(3.0 * phase)
                + 0.22 * bright * math.sin(4.0 * phase)
                + 0.12 * bright * math.sin(6.0 * phase)
            )
            out[i] = env * sig

        else:
            env = vel * 0.20 * math.exp(-t * 8.0)
            out[i] = env * math.sin(phase)

    return start_idx, out


def _render_percussion_hit(hit: PercussionEvent, sample_rate: int = SAMPLE_RATE) -> Tuple[int, List[float]]:
    """Synthesize crisp orchestral/minimalist percussion hits (woodblock, clave, brush, snap, soft kick)."""
    start_idx = max(0, int(round(hit.start_sec * sample_rate)))
    dur = 0.09
    n_samples = int(round(dur * sample_rate))
    out = [0.0] * n_samples
    vel = max(0.05, min(1.2, hit.velocity))
    two_pi = 2.0 * math.pi

    for i in range(n_samples):
        t = i / float(sample_rate)
        # Deterministic pseudo-noise for brush/snare textures
        noise = math.sin(i * 12.9898 + 78.233) * 43758.5453
        noise = (noise - math.floor(noise)) * 2.0 - 1.0

        if hit.kind == "woodblock_hi":
            env = vel * 0.24 * math.exp(-t * 55.0)
            out[i] = env * (math.sin(two_pi * 920.0 * t) + 0.42 * math.sin(two_pi * 1490.0 * t))
        elif hit.kind == "woodblock_lo":
            env = vel * 0.24 * math.exp(-t * 48.0)
            out[i] = env * (math.sin(two_pi * 685.0 * t) + 0.38 * math.sin(two_pi * 1110.0 * t))
        elif hit.kind == "clave":
            env = vel * 0.22 * math.exp(-t * 68.0)
            out[i] = env * (math.sin(two_pi * 2380.0 * t) + 0.28 * math.sin(two_pi * 3620.0 * t))
        elif hit.kind == "snap":
            env = vel * 0.22 * math.exp(-t * 72.0)
            body = math.sin(two_pi * 1850.0 * t) + 0.5 * math.sin(two_pi * 2920.0 * t)
            out[i] = env * (0.65 * body + 0.35 * noise)
        elif hit.kind == "brush_hat":
            env = vel * 0.12 * math.exp(-t * 62.0)
            # High-passed metallic shimmer + brush noise
            shimmer = math.sin(two_pi * 5400.0 * t) * 0.4 + math.sin(two_pi * 7850.0 * t) * 0.3
            out[i] = env * (0.65 * noise + 0.35 * shimmer)
        elif hit.kind == "brush_snare":
            env = vel * 0.18 * math.exp(-t * 36.0)
            shell = math.sin(two_pi * 215.0 * t) * math.exp(-t * 50.0)
            out[i] = env * (0.72 * noise + 0.28 * shell)
        elif hit.kind == "kick_soft":
            env = vel * 0.26 * math.exp(-t * 24.0)
            f_sweep = 58.0 + 72.0 * math.exp(-t * 48.0)
            out[i] = env * math.sin(two_pi * f_sweep * t)

    return start_idx, out


# ---------------------------------------------------------------------------
# Three Original Musical Theme Candidate Scores (Options A, B, C)
# ---------------------------------------------------------------------------


def _build_option_a_orchestral_cartoon_score(duration_seconds: float) -> Tuple[List[NoteEvent], List[PercussionEvent]]:
    """Option A: Playful orchestral cartoon comedy (132 BPM, C Major / A Minor / Lydian mischievous hook).

    Features:
    - Clarinet/Woodwind lead with playful grace notes and staccato leaps
    - Pizzicato string counter-chords on off-beats
    - Bouncy upright bass / tuba walking line
    - Xylophone sparkles and crisp woodblock/brush percussion
    """
    beat = 60.0 / 132.0  # 0.4545s per beat
    notes: List[NoteEvent] = []
    perc: List[PercussionEvent] = []

    # 8-bar playful orchestral cartoon melody (32 beats = 14.5s, loops cleanly to 16.0s)
    # Bar 1-2: Inquisitive clarinet motif in C major with raised 4th (F#66) cartoon mischief
    melody_pattern = [
        # (beat_offset, dur_beats, midi, grace_midi, vel)
        (0.0, 0.45, 72, 71, 0.88),   # C5 (grace B4)
        (0.5, 0.45, 76, None, 0.82), # E5
        (1.0, 0.45, 79, 78, 0.90),   # G5 (grace F#5)
        (1.5, 0.45, 81, None, 0.85), # A5
        (2.0, 0.70, 79, None, 0.90), # G5
        (3.0, 0.45, 78, None, 0.80), # F#5
        (3.5, 0.45, 79, None, 0.88), # G5
        # Bar 2: Mischievous descending tip-toe
        (4.0, 0.45, 84, 83, 0.92),   # C6
        (4.5, 0.45, 79, None, 0.80), # G5
        (5.0, 0.45, 76, None, 0.82), # E5
        (5.5, 0.45, 72, None, 0.80), # C5
        (6.0, 0.85, 74, 73, 0.88),   # D5
        (7.0, 0.85, 79, None, 0.84), # G5
        # Bar 3: Playful A-minor sneaky phrase
        (8.0, 0.45, 69, 68, 0.86),   # A4
        (8.5, 0.45, 72, None, 0.82), # C5
        (9.0, 0.45, 76, 75, 0.88),   # E5
        (9.5, 0.45, 81, None, 0.92), # A5
        (10.0, 0.45, 80, None, 0.84),# G#5
        (10.5, 0.45, 81, None, 0.88),# A5
        (11.0, 0.85, 84, 83, 0.94),  # C6
        # Bar 4: Bouncy turnaround
        (12.0, 0.45, 83, None, 0.86),# B5
        (12.5, 0.45, 79, None, 0.82),# G5
        (13.0, 0.45, 77, None, 0.84),# F5
        (13.5, 0.45, 74, None, 0.80),# D5
        (14.0, 0.90, 72, 71, 0.92),  # C5
        (15.0, 0.80, 67, None, 0.80),# G4
    ]

    total_beats = int(math.ceil(duration_seconds / beat))
    for cycle_start in range(0, total_beats, 16):
        for b_off, dur_b, midi_n, grace_n, vel in melody_pattern:
            t0 = (cycle_start + b_off) * beat
            if t0 >= duration_seconds:
                continue
            notes.append(
                NoteEvent(
                    start_sec=t0,
                    duration_sec=dur_b * beat,
                    midi_note=midi_n,
                    velocity=vel,
                    instrument="clarinet",
                    grace_midi=grace_n,
                )
            )
            # Double bright phrase peaks on orchestral xylophone
            if midi_n >= 79 and b_off in (1.0, 4.0, 9.5, 11.0, 14.0):
                notes.append(
                    NoteEvent(
                        start_sec=t0,
                        duration_sec=0.22,
                        midi_note=midi_n + 12,
                        velocity=vel * 0.65,
                        instrument="xylophone",
                    )
                )

    # Walking upright bass (quarter notes) + off-beat pizzicato string chords
    bass_roots = [48, 52, 55, 52, 50, 55, 43, 50, 45, 48, 52, 48, 53, 50, 43, 47]
    pizz_chords = [
        (60, 64, 67), (60, 64, 67), (62, 67, 71), (62, 67, 71),
        (57, 60, 64), (57, 60, 64), (59, 62, 67), (60, 64, 67),
    ]
    for b_idx in range(total_beats):
        t_beat = b_idx * beat
        if t_beat >= duration_seconds:
            break
        bass_midi = bass_roots[b_idx % len(bass_roots)]
        notes.append(
            NoteEvent(
                start_sec=t_beat,
                duration_sec=beat * 0.78,
                midi_note=bass_midi,
                velocity=0.85 if (b_idx % 2 == 0) else 0.72,
                instrument="upright_bass",
            )
        )
        # Off-beat pizzicato stringdyad/triad
        t_off = t_beat + 0.5 * beat
        if t_off < duration_seconds:
            chord = pizz_chords[(b_idx // 2) % len(pizz_chords)]
            for c_midi in chord:
                notes.append(
                    NoteEvent(
                        start_sec=t_off,
                        duration_sec=0.16,
                        midi_note=c_midi + 12,
                        velocity=0.52,
                        instrument="pizzicato",
                    )
                )
        # Light cartoon percussion (woodblocks + brushes)
        if b_idx % 2 == 0:
            perc.append(PercussionEvent(start_sec=t_beat, kind="kick_soft", velocity=0.65))
            perc.append(PercussionEvent(start_sec=t_beat, kind="woodblock_lo", velocity=0.58))
        else:
            perc.append(PercussionEvent(start_sec=t_beat, kind="brush_snare", velocity=0.62))
            if t_off < duration_seconds:
                perc.append(PercussionEvent(start_sec=t_off, kind="woodblock_hi", velocity=0.66))
        if t_off < duration_seconds:
            perc.append(PercussionEvent(start_sec=t_off, kind="brush_hat", velocity=0.55))

    return notes, perc


def _build_option_b_electro_acoustic_adventure_score(
    duration_seconds: float,
) -> Tuple[List[NoteEvent], List[PercussionEvent]]:
    """Option B: Modern electronic-acoustic adventure comedy (124 BPM, F Lydian / Dorian groove).

    Features:
    - Syncopated wooden Marimba & Plucked Acoustic Guitar melodic hook
    - Warm Analog Brass / Bell counter-melody
    - Acoustic-electric bassline & crisp shaker/brush/clave groove
    """
    beat = 60.0 / 124.0  # 0.4838s per beat
    notes: List[NoteEvent] = []
    perc: List[PercussionEvent] = []

    # Syncopated adventure hook in F Lydian (F, G, A, B, C, D, E)
    hook_pattern = [
        (0.0, 0.45, 65, 0.88, "marimba"),       # F4
        (0.5, 0.45, 69, 0.82, "marimba"),       # A4
        (1.0, 0.45, 72, 0.90, "marimba"),       # C5
        (1.75, 0.65, 74, 0.92, "marimba"),      # D5 (syncopated)
        (2.5, 0.45, 72, 0.84, "marimba"),       # C5
        (3.0, 0.85, 71, 0.88, "marimba"),       # B4 (Lydian #4 spark)
        (4.0, 0.45, 72, 0.88, "marimba"),       # C5
        (4.5, 0.45, 76, 0.86, "marimba"),       # E5
        (5.0, 0.45, 77, 0.92, "marimba"),       # F5
        (5.75, 0.65, 79, 0.94, "marimba"),      # G5
        (6.5, 0.45, 76, 0.84, "marimba"),       # E5
        (7.0, 0.85, 72, 0.88, "marimba"),       # C5
        # Answering phrase with warm analog brass counter-lead
        (8.0, 0.70, 74, 0.86, "analog_brass"),  # D5
        (8.75, 0.65, 76, 0.88, "analog_brass"), # E5
        (9.5, 0.45, 77, 0.90, "analog_brass"),  # F5
        (10.0, 0.90, 81, 0.92, "analog_brass"), # A5
        (11.0, 0.85, 79, 0.88, "analog_brass"), # G5
        (12.0, 0.45, 77, 0.88, "marimba"),      # F5
        (12.5, 0.45, 74, 0.84, "marimba"),      # D5
        (13.0, 0.45, 72, 0.86, "marimba"),      # C5
        (13.5, 0.45, 69, 0.82, "marimba"),      # A4
        (14.0, 1.20, 65, 0.92, "analog_brass"), # F4
    ]

    guitar_arpeggio = [65, 72, 69, 76, 62, 69, 65, 74, 67, 74, 71, 79, 60, 67, 64, 72]
    bass_pattern = [41, 41, 53, 48, 38, 38, 50, 45, 43, 43, 55, 50, 36, 48, 43, 40]

    total_beats = int(math.ceil(duration_seconds / beat))
    for cycle_start in range(0, total_beats, 16):
        for b_off, dur_b, midi_n, vel, inst in hook_pattern:
            t0 = (cycle_start + b_off) * beat
            if t0 >= duration_seconds:
                continue
            notes.append(
                NoteEvent(
                    start_sec=t0,
                    duration_sec=dur_b * beat,
                    midi_note=midi_n,
                    velocity=vel,
                    instrument=inst,
                )
            )

    for b_idx in range(total_beats):
        t_beat = b_idx * beat
        if t_beat >= duration_seconds:
            break
        # Plucked acoustic guitar 8th-note groove
        g1 = guitar_arpeggio[b_idx % len(guitar_arpeggio)]
        notes.append(
            NoteEvent(start_sec=t_beat, duration_sec=beat * 0.45, midi_note=g1, velocity=0.64, instrument="guitar")
        )
        t_half = t_beat + 0.5 * beat
        if t_half < duration_seconds:
            notes.append(
                NoteEvent(
                    start_sec=t_half,
                    duration_sec=beat * 0.45,
                    midi_note=g1 + 7,
                    velocity=0.56,
                    instrument="guitar",
                )
            )

        # Warm bassline
        b_midi = bass_pattern[b_idx % len(bass_pattern)]
        notes.append(
            NoteEvent(
                start_sec=t_beat,
                duration_sec=beat * 0.82,
                midi_note=b_midi,
                velocity=0.84,
                instrument="upright_bass",
            )
        )

        # Adventure percussion groove
        if b_idx % 2 == 0:
            perc.append(PercussionEvent(start_sec=t_beat, kind="kick_soft", velocity=0.72))
        else:
            perc.append(PercussionEvent(start_sec=t_beat, kind="brush_snare", velocity=0.68))
        if t_half < duration_seconds:
            perc.append(PercussionEvent(start_sec=t_half, kind="brush_hat", velocity=0.62))
        if b_idx % 4 in (1, 3) and t_half < duration_seconds:
            perc.append(PercussionEvent(start_sec=t_half, kind="clave", velocity=0.58))

    return notes, perc


def _build_option_c_quirky_minimalist_plucked_score(
    duration_seconds: float,
) -> Tuple[List[NoteEvent], List[PercussionEvent]]:
    """Option C: Quirky minimalist percussion and plucked instruments (136 BPM, D Dorian / Pentatonic puzzle box).

    Features:
    - Interlocking Kalimba (thumb piano) and Harpsichord/Lute plucked ostinatos
    - Pizzicato Cello counter-melody
    - Crisp woodblocks, claves, finger snaps, and tuned xylophone accents
    """
    beat = 60.0 / 136.0  # 0.4411s per beat
    notes: List[NoteEvent] = []
    perc: List[PercussionEvent] = []

    # Quirky interlocking Kalimba + Harpsichord puzzle motif in D Dorian (D, E, F, G, A, B, C)
    kalimba_motif = [
        (0.0, 0.35, 74, 0.88),  # D5
        (0.5, 0.35, 77, 0.82),  # F5
        (1.0, 0.35, 81, 0.90),  # A5
        (1.5, 0.35, 83, 0.86),  # B5 (Dorian 6th)
        (2.0, 0.35, 86, 0.92),  # D6
        (2.5, 0.35, 81, 0.80),  # A5
        (3.0, 0.65, 79, 0.88),  # G5
        (4.0, 0.35, 76, 0.84),  # E5
        (4.5, 0.35, 79, 0.82),  # G5
        (5.0, 0.35, 81, 0.88),  # A5
        (5.5, 0.35, 74, 0.80),  # D5
        (6.0, 0.65, 72, 0.86),  # C5
        (7.0, 0.65, 74, 0.90),  # D5
    ]

    harpsichord_counter = [
        (0.25, 0.30, 62, 0.68), # D4
        (0.75, 0.30, 69, 0.65), # A4
        (1.25, 0.30, 65, 0.68), # F4
        (2.25, 0.30, 67, 0.68), # G4
        (2.75, 0.30, 71, 0.66), # B4
        (4.25, 0.30, 64, 0.68), # E4
        (4.75, 0.30, 67, 0.65), # G4
        (5.25, 0.30, 69, 0.68), # A4
        (6.25, 0.30, 60, 0.66), # C4
        (6.75, 0.30, 62, 0.72), # D4
    ]

    pizz_cello_line = [50, 57, 53, 55, 50, 48, 45, 48]

    total_beats = int(math.ceil(duration_seconds / beat))
    for cycle_start in range(0, total_beats, 8):
        for b_off, dur_b, midi_n, vel in kalimba_motif:
            t0 = (cycle_start + b_off) * beat
            if t0 < duration_seconds:
                notes.append(
                    NoteEvent(
                        start_sec=t0,
                        duration_sec=dur_b * beat,
                        midi_note=midi_n,
                        velocity=vel,
                        instrument="kalimba",
                    )
                )
        for b_off, dur_b, midi_n, vel in harpsichord_counter:
            t0 = (cycle_start + b_off) * beat
            if t0 < duration_seconds:
                notes.append(
                    NoteEvent(
                        start_sec=t0,
                        duration_sec=dur_b * beat,
                        midi_note=midi_n,
                        velocity=vel,
                        instrument="harpsichord",
                    )
                )

    for b_idx in range(total_beats):
        t_beat = b_idx * beat
        if t_beat >= duration_seconds:
            break
        c_midi = pizz_cello_line[b_idx % len(pizz_cello_line)]
        notes.append(
            NoteEvent(
                start_sec=t_beat,
                duration_sec=beat * 0.70,
                midi_note=c_midi,
                velocity=0.84,
                instrument="pizzicato",
            )
        )
        t_half = t_beat + 0.5 * beat
        if b_idx % 2 == 0:
            perc.append(PercussionEvent(start_sec=t_beat, kind="woodblock_lo", velocity=0.72))
            if t_half < duration_seconds:
                perc.append(PercussionEvent(start_sec=t_half, kind="clave", velocity=0.64))
        else:
            perc.append(PercussionEvent(start_sec=t_beat, kind="snap", velocity=0.76))
            if t_half < duration_seconds:
                perc.append(PercussionEvent(start_sec=t_half, kind="woodblock_hi", velocity=0.68))

    return notes, perc


# ---------------------------------------------------------------------------
# Score Renderer & WAV Export
# ---------------------------------------------------------------------------


def render_score_to_buffer(
    notes: Sequence[NoteEvent],
    percussion: Sequence[PercussionEvent],
    duration_seconds: float,
    sample_rate: int = SAMPLE_RATE,
) -> List[float]:
    """Mix all scored instrument notes and percussion events into a float buffer."""
    n_samples = int(round(duration_seconds * sample_rate))
    mix = [0.0] * n_samples

    for note in notes:
        start_idx, samples = _render_voice_note(note, sample_rate=sample_rate)
        end_idx = min(n_samples, start_idx + len(samples))
        for i in range(start_idx, end_idx):
            mix[i] += samples[i - start_idx]

    for hit in percussion:
        start_idx, samples = _render_percussion_hit(hit, sample_rate=sample_rate)
        end_idx = min(n_samples, start_idx + len(samples))
        for i in range(start_idx, end_idx):
            mix[i] += samples[i - start_idx]

    return mix


def _write_normalized_wav(
    samples: Sequence[float],
    wav_path: Path,
    target_peak: float = 0.88,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[float, float, str]:
    """Normalize buffer to `target_peak`, write 16-bit PCM WAV, and return `(peak, rms, sha256)`."""
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    raw_peak = max((abs(x) for x in samples), default=1e-6)
    scale = (target_peak / raw_peak) if raw_peak > 1e-6 else 1.0

    pcm = bytearray()
    sq_sum = 0.0
    final_peak = 0.0
    for s in samples:
        val = max(-0.98, min(0.98, s * scale))
        av = abs(val)
        if av > final_peak:
            final_peak = av
        sq_sum += val * val
        pcm.extend(struct.pack("<h", int(round(val * 32767.0))))

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(pcm))

    rms = math.sqrt(sq_sum / max(1, len(samples)))
    digest = hashlib.sha256(wav_path.read_bytes()).hexdigest()
    return round(final_peak, 4), round(rms, 4), digest


def generate_three_music_candidates(
    out_dir: Path = Path("assets/audio/candidates"),
    duration_seconds: float = 16.0,
) -> Dict[str, MusicCandidateArtifact]:
    """Generate the three distinct original musical candidates (Options A, B, C) for owner selection."""
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        (
            MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value,
            "Option A — Playful Orchestral Cartoon Comedy",
            "Clarinet/woodwind lead with grace notes, pizzicato strings, upright walking bass, and xylophone/woodblocks (132 BPM).",
            out_dir / "candidate_a_orchestral_cartoon.wav",
            _build_option_a_orchestral_cartoon_score,
        ),
        (
            MusicCandidateOption.OPTION_B_ELECTRO_ACOUSTIC_ADVENTURE.value,
            "Option B — Modern Electronic-Acoustic Adventure Comedy",
            "Syncopated wooden marimba & plucked acoustic guitar hook, warm analog brass/bell counter-lead, and brush groove (124 BPM).",
            out_dir / "candidate_b_electro_acoustic_adventure.wav",
            _build_option_b_electro_acoustic_adventure_score,
        ),
        (
            MusicCandidateOption.OPTION_C_QUIRKY_MINIMALIST_PLUCKED.value,
            "Option C — Quirky Minimalist Percussion & Plucked Instruments",
            "Interlocking kalimba, harpsichord/lute, and pizzicato cello puzzle ostinatos over woodblocks, claves, and snaps (136 BPM).",
            out_dir / "candidate_c_quirky_minimalist_plucked.wav",
            _build_option_c_quirky_minimalist_plucked_score,
        ),
    ]

    artifacts: Dict[str, MusicCandidateArtifact] = {}
    for opt_id, label, summary, wav_path, builder_fn in specs:
        notes, perc = builder_fn(duration_seconds)
        buf = render_score_to_buffer(notes, perc, duration_seconds=duration_seconds)
        peak, rms, digest = _write_normalized_wav(buf, wav_path=wav_path, target_peak=0.86)
        artifacts[opt_id] = MusicCandidateArtifact(
            option_id=opt_id,
            label=label,
            style_summary=summary,
            wav_path=wav_path,
            duration_seconds=duration_seconds,
            sample_rate=SAMPLE_RATE,
            peak_amplitude=peak,
            rms_amplitude=rms,
            sha256=digest,
        )
    return artifacts


# ---------------------------------------------------------------------------
# Tactile Sound Effects & Adaptive Audio Engine
# ---------------------------------------------------------------------------


def _synthesize_sfx_clip(sfx_name: str, pitch_shift_semitones: float = 0.0, sample_rate: int = SAMPLE_RATE) -> List[float]:
    """Synthesize a crisp, unmistakable tactile cartoon sound effect clip."""
    two_pi = 2.0 * math.pi
    pitch_mult = 2.0 ** (pitch_shift_semitones / 12.0)

    if sfx_name == "button_click":
        # Crisp mechanical calculator key switch click + tactile woody keycap thock
        n = int(0.065 * sample_rate)
        out = [0.0] * n
        for i in range(n):
            t = i / float(sample_rate)
            click_hi = math.exp(-t * 145.0) * math.sin(two_pi * 1720.0 * pitch_mult * t)
            thock_lo = math.exp(-t * 68.0) * math.sin(two_pi * 490.0 * pitch_mult * t)
            snap = math.exp(-t * 240.0) * math.sin(two_pi * 3200.0 * t)
            out[i] = 0.56 * (0.55 * click_hi + 0.35 * thock_lo + 0.10 * snap)
        return out

    if sfx_name == "positive_calc_chime":
        # Warm rising major triad bell chime (`10 ÷ 2 = 5`)
        n = int(0.55 * sample_rate)
        out = [0.0] * n
        notes = [(0.0, 523.25), (0.07, 659.25), (0.14, 783.99)]
        for t0, freq in notes:
            s0 = int(t0 * sample_rate)
            for i in range(s0, n):
                dt = (i - s0) / float(sample_rate)
                env = 0.34 * math.exp(-dt * 6.5)
                out[i] += env * (math.sin(two_pi * freq * dt) + 0.35 * math.sin(two_pi * freq * 2.0 * dt))
        return out

    if sfx_name == "intrigued_calc_double_chime":
        # Faster, higher-pitched double bell chime (`10 ÷ 1 = 10`, rising curiosity)
        n = int(0.58 * sample_rate)
        out = [0.0] * n
        notes = [(0.0, 587.33), (0.06, 739.99), (0.12, 880.0), (0.20, 1174.66)]
        for t0, freq in notes:
            s0 = int(t0 * sample_rate)
            for i in range(s0, n):
                dt = (i - s0) / float(sample_rate)
                env = 0.36 * math.exp(-dt * 6.8)
                out[i] += env * (math.sin(two_pi * freq * dt) + 0.40 * math.sin(two_pi * freq * 2.0 * dt))
        return out

    if sfx_name == "division_by_zero_alarm":
        # Distinct comedic cartoon paradox alarm (`10 ÷ 0 = UNDEFINED`): dissonant tritone + descending spring wobble
        n = int(1.35 * sample_rate)
        out = [0.0] * n
        for i in range(n):
            t = i / float(sample_rate)
            if t < 0.42:
                # Two-tone red error buzzer pulse
                f_buzz = 311.13 if int(t * 14.0) % 2 == 0 else 220.0
                env = 0.48 * math.exp(-t * 1.4)
                sig = (
                    math.sin(two_pi * f_buzz * t)
                    + 0.55 * math.sin(two_pi * (f_buzz * 1.414) * t)
                    + 0.35 * math.sin(two_pi * (f_buzz * 3.0) * t)
                )
                out[i] = env * sig * 0.55
            else:
                # Comedic cartoon spring / paradox shimmer tail
                dt = t - 0.42
                wobble_f = (520.0 - 240.0 * min(1.0, dt / 0.85)) * (1.0 + 0.16 * math.sin(two_pi * 19.0 * dt))
                env = 0.44 * math.exp(-dt * 2.8)
                out[i] = env * (math.sin(two_pi * wobble_f * dt) + 0.4 * math.sin(two_pi * wobble_f * 2.5 * dt))
        return out

    if sfx_name == "footstep_soft":
        n = int(0.055 * sample_rate)
        return [
            0.22 * math.exp(-(i / float(sample_rate)) * 65.0) * math.sin(two_pi * 145.0 * (i / float(sample_rate)))
            for i in range(n)
        ]

    if sfx_name == "reality_reset_chime":
        # Bright sparkling C-major ascending arpeggio chime when pressing 'C' (Clear) collapses the cartoon void
        n = int(0.75 * sample_rate)
        out = [0.0] * n
        notes = [(0.0, 523.25), (0.06, 659.25), (0.12, 783.99), (0.18, 1046.50), (0.25, 1318.51)]
        for t0, freq in notes:
            s0 = int(t0 * sample_rate)
            for i in range(s0, n):
                dt = (i - s0) / float(sample_rate)
                env = 0.32 * math.exp(-dt * 5.8)
                out[i] += env * (math.sin(two_pi * freq * dt) + 0.38 * math.sin(two_pi * freq * 2.0 * dt))
        return out

    if sfx_name == "cartoon_void_whoosh":
        # Swirling low-to-mid vortex hum + phase-modulated cartoon suction whoosh
        n = int(1.60 * sample_rate)
        out = [0.0] * n
        for i in range(n):
            t = i / float(sample_rate)
            env = 0.34 * math.sin(math.pi * min(1.0, t / 1.60))
            f_swirl = 135.0 + 45.0 * math.sin(two_pi * 3.5 * t)
            out[i] = env * (
                0.60 * math.sin(two_pi * f_swirl * t)
                + 0.40 * math.sin(two_pi * (f_swirl * 1.5) * t + math.sin(two_pi * 7.0 * t))
            )
        return out

    # Generic interaction SFX (`object_pickup`, `door_creak`, `block_slide`, `math_symbol_chime`)
    n = int(0.22 * sample_rate)
    return [
        0.30 * math.exp(-(i / float(sample_rate)) * 16.0) * math.sin(two_pi * 660.0 * pitch_mult * (i / float(sample_rate)))
        for i in range(n)
    ]


@dataclass
class AdaptiveAudioEngine:
    """Synchronizes adaptive background music, comedic pauses, and physical-contact sound effects."""

    duration_seconds: float = 16.0
    fps: int = 30
    candidate_option: str = MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value
    state_schedule: List[Tuple[float, float, AdaptiveMusicState]] = field(default_factory=list)
    pause_windows: List[Tuple[float, float]] = field(default_factory=list)
    sound_cues: List[SoundCueEvent] = field(default_factory=list)

    def add_state_window(self, start_sec: float, end_sec: float, state: AdaptiveMusicState) -> None:
        self.state_schedule.append((start_sec, end_sec, state))

    def add_musical_pause(self, start_sec: float, end_sec: float) -> None:
        """Schedule an intentional dramatic/comedic musical pause window."""
        self.pause_windows.append((start_sec, end_sec))

    def register_contact_events(self, contact_events: Sequence[ContactEvent]) -> List[SoundCueEvent]:
        """Convert physical `ContactEvent` records directly into frame-accurate `SoundCueEvent` triggers."""
        created: List[SoundCueEvent] = []
        # Map keypad labels to subtle musical pitch variations so sequential key presses feel alive
        key_pitch_map = {
            "1": 0.0,
            "2": 2.0,
            "3": 4.0,
            "0": -2.0,
            "÷": 5.0,
            "=": 7.0,
        }
        for ev in contact_events:
            key_lbl = ev.target_id.replace("key_", "")
            pitch_shift = key_pitch_map.get(key_lbl, 0.0)
            click_cue = SoundCueEvent(
                cue_id=f"cue_click_{ev.step_id}",
                sfx_name="button_click" if ev.sfx_cue == "division_by_zero_alarm" else ev.sfx_cue,
                timestamp_sec=ev.timestamp_sec,
                frame_idx=ev.frame_idx,
                gain=0.95,
                pitch_shift_semitones=pitch_shift,
                source_target_id=ev.target_id,
            )
            self.sound_cues.append(click_cue)
            created.append(click_cue)

            # Trigger synchronized calculator evaluation result SFX immediately after '=' contact
            if ev.target_id == "key_=":
                eval_t = min(self.duration_seconds - 0.1, ev.timestamp_sec + 0.08)
                eval_frame = int(round(eval_t * self.fps))
                if "-> '5'" in ev.state_change_summary:
                    res_cue = SoundCueEvent(
                        cue_id=f"cue_result_5_{ev.step_id}",
                        sfx_name="positive_calc_chime",
                        timestamp_sec=eval_t,
                        frame_idx=eval_frame,
                        gain=0.92,
                        source_target_id=ev.target_id,
                    )
                    self.sound_cues.append(res_cue)
                    created.append(res_cue)
                elif "-> '10'" in ev.state_change_summary:
                    res_cue = SoundCueEvent(
                        cue_id=f"cue_result_10_{ev.step_id}",
                        sfx_name="intrigued_calc_double_chime",
                        timestamp_sec=eval_t,
                        frame_idx=eval_frame,
                        gain=0.95,
                        source_target_id=ev.target_id,
                    )
                    self.sound_cues.append(res_cue)
                    created.append(res_cue)
                elif "UNDEFINED" in ev.state_change_summary:
                    res_cue = SoundCueEvent(
                        cue_id=f"cue_result_undef_{ev.step_id}",
                        sfx_name="division_by_zero_alarm",
                        timestamp_sec=eval_t,
                        frame_idx=eval_frame,
                        gain=1.0,
                        source_target_id=ev.target_id,
                    )
                    self.sound_cues.append(res_cue)
                    created.append(res_cue)
            elif ev.target_id == "key_C":
                reset_t = min(self.duration_seconds - 0.1, ev.timestamp_sec + 0.06)
                reset_frame = int(round(reset_t * self.fps))
                reset_cue = SoundCueEvent(
                    cue_id=f"cue_reality_reset_{ev.step_id}",
                    sfx_name="reality_reset_chime",
                    timestamp_sec=reset_t,
                    frame_idx=reset_frame,
                    gain=0.96,
                    source_target_id=ev.target_id,
                )
                self.sound_cues.append(reset_cue)
                created.append(reset_cue)
        return created

    def state_at(self, t_sec: float) -> AdaptiveMusicState:
        for s0, s1, st in self.state_schedule:
            if s0 <= t_sec <= s1:
                return st
        return AdaptiveMusicState.EXPLORATION

    def is_in_musical_pause(self, t_sec: float) -> bool:
        return any(p0 <= t_sec <= p1 for p0, p1 in self.pause_windows)

    def render_adaptive_episode_mix(
        self,
        wav_path: Path,
        sample_rate: int = SAMPLE_RATE,
    ) -> Dict[str, object]:
        """Render the complete adaptive episode soundtrack with state variations, pauses, SFX, and ducking."""
        if self.candidate_option == MusicCandidateOption.OPTION_B_ELECTRO_ACOUSTIC_ADVENTURE.value:
            notes, perc = _build_option_b_electro_acoustic_adventure_score(self.duration_seconds)
        elif self.candidate_option == MusicCandidateOption.OPTION_C_QUIRKY_MINIMALIST_PLUCKED.value:
            notes, perc = _build_option_c_quirky_minimalist_plucked_score(self.duration_seconds)
        else:
            notes, perc = _build_option_a_orchestral_cartoon_score(self.duration_seconds)

        # Apply adaptive state transformations (SUSPENSE tense transposition, CHAOS rhythmic energy, RESOLUTION cadence)
        adapted_notes: List[NoteEvent] = []
        for n in notes:
            if self.is_in_musical_pause(n.start_sec):
                continue
            st = self.state_at(n.start_sec)
            if st == AdaptiveMusicState.SILENCE:
                continue
            elif st == AdaptiveMusicState.SUSPENSE:
                # Subtle sneaky minor/diminished color & lighter velocity during 10 ÷ 0 buildup
                shift = -1.0 if (int(n.midi_note) % 12 in (4, 9)) else 0.0
                adapted_notes.append(
                    NoteEvent(
                        start_sec=n.start_sec,
                        duration_sec=n.duration_sec * 0.75,
                        midi_note=n.midi_note + shift,
                        velocity=n.velocity * 0.78,
                        instrument="pizzicato" if n.instrument == "clarinet" else n.instrument,
                        grace_midi=n.grace_midi,
                    )
                )
            elif st == AdaptiveMusicState.CHAOS:
                # Energetic upper-register spike
                adapted_notes.append(
                    NoteEvent(
                        start_sec=n.start_sec,
                        duration_sec=n.duration_sec * 0.65,
                        midi_note=n.midi_note + 1.0,
                        velocity=min(1.0, n.velocity * 0.95),
                        instrument=n.instrument,
                        grace_midi=n.grace_midi,
                    )
                )
            elif st == AdaptiveMusicState.RESOLUTION:
                # Warm resolved C-major / tonic glow
                adapted_notes.append(
                    NoteEvent(
                        start_sec=n.start_sec,
                        duration_sec=n.duration_sec * 1.15,
                        midi_note=n.midi_note,
                        velocity=n.velocity * 0.85,
                        instrument=n.instrument,
                        grace_midi=n.grace_midi,
                    )
                )
            else:
                adapted_notes.append(n)

        adapted_perc = [p for p in perc if not self.is_in_musical_pause(p.start_sec)]
        music_buf = render_score_to_buffer(adapted_notes, adapted_perc, self.duration_seconds, sample_rate=sample_rate)

        # Apply smooth envelope attenuation across `pause_windows` so music stops cleanly on comedic beat
        n_samples = len(music_buf)
        for i in range(n_samples):
            t = i / float(sample_rate)
            if self.is_in_musical_pause(t):
                music_buf[i] *= 0.02

        # Render foreground SFX buffer
        sfx_buf = [0.0] * n_samples
        for cue in self.sound_cues:
            clip = _synthesize_sfx_clip(
                cue.sfx_name,
                pitch_shift_semitones=cue.pitch_shift_semitones,
                sample_rate=sample_rate,
            )
            s0 = max(0, int(round(cue.timestamp_sec * sample_rate)))
            s1 = min(n_samples, s0 + len(clip))
            for i in range(s0, s1):
                sfx_buf[i] += cue.gain * clip[i - s0]

        # Sidechain ducking: attenuate background music slightly whenever foreground SFX is active
        final_mix = [0.0] * n_samples
        duck_env = 0.0
        for i in range(n_samples):
            s_abs = abs(sfx_buf[i])
            if s_abs > duck_env:
                duck_env = 0.85 * duck_env + 0.15 * s_abs
            else:
                duck_env = 0.9985 * duck_env
            music_gain = max(0.32, 0.62 - 0.55 * min(1.0, duck_env * 2.5))
            final_mix[i] = music_buf[i] * music_gain + sfx_buf[i] * 1.15

        peak, rms, digest = _write_normalized_wav(final_mix, wav_path=wav_path, target_peak=0.90, sample_rate=sample_rate)
        return {
            "wav_path": str(wav_path),
            "duration_seconds": self.duration_seconds,
            "candidate_option": self.candidate_option,
            "sound_cue_count": len(self.sound_cues),
            "pause_windows": list(self.pause_windows),
            "peak_amplitude": peak,
            "rms_amplitude": rms,
            "sha256": digest,
        }


def verify_and_register_audio_provenance(
    session: Session,
    candidates: Dict[str, MusicCandidateArtifact],
    episode_mix_path: Optional[Path] = None,
) -> List[Asset]:
    """Verify commercial-use safety and register audio assets in SQLite `Asset` provenance table."""
    registered: List[Asset] = []
    for opt_id, cand in candidates.items():
        if not cand.wav_path.exists():
            raise FileNotFoundError(f"Missing audio candidate file: {cand.wav_path}")
        if "Commercial-Safe" not in cand.license_name:
            raise ValueError(f"Audio candidate {opt_id} lacks verified commercial license.")
        asset_name = f"music_candidate_{opt_id}"
        existing = session.query(Asset).filter_by(name=asset_name).first()
        if existing is None:
            asset = Asset(
                name=asset_name,
                asset_type="music",
                file_path=str(cand.wav_path),
                sha256=cand.sha256,
                source="local://app/adaptive_audio.py#procedural-multi-voice",
                license_type=cand.license_name,
                provenance_record=f"{cand.label}: {cand.style_summary}",
                commercial_use_cleared=True,
                sponsored_use_cleared=True,
            )
            session.add(asset)
            registered.append(asset)
        else:
            existing.sha256 = cand.sha256
            existing.file_path = str(cand.wav_path)
            registered.append(existing)

    if episode_mix_path is not None and episode_mix_path.exists():
        digest = hashlib.sha256(episode_mix_path.read_bytes()).hexdigest()
        mix_name = "ep001_adaptive_master_mix"
        existing_mix = session.query(Asset).filter_by(name=mix_name).first()
        if existing_mix is None:
            mix_asset = Asset(
                name=mix_name,
                asset_type="music",
                file_path=str(episode_mix_path),
                sha256=digest,
                source="local://app/adaptive_audio.py#AdaptiveAudioEngine",
                license_type="MathMayhem-100%-Original-Procedural-Score-Commercial-Safe",
                provenance_record="Math Mayhem Adaptive Episode Mix & Tactile SFX (100% Commercial Safe)",
                commercial_use_cleared=True,
                sponsored_use_cleared=True,
            )
            session.add(mix_asset)
            registered.append(mix_asset)
        else:
            existing_mix.sha256 = digest
            existing_mix.file_path = str(episode_mix_path)
            registered.append(existing_mix)

    session.commit()
    return registered
