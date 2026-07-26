"""Four-part tonal harmonization case study."""

from .muses_harmonizer import (
    MusesFactories,
    MusesHarmonization,
    PieceLike,
    harmonize_temporal_collection,
)
from .note_solver import (
    Cadence,
    HarmonicPlanDegree,
    HarmonicPlanProfile,
    NoteHarmonization,
    NoteHarmonizerModel,
    SATBVoice,
    build_note_harmonizer_model,
    harmonize_notes,
    sample_harmonization,
    solve_note_harmonizer,
)
from .solver import (
    Harmonization,
    HarmonizerModel,
    build_harmonizer_model,
    harmonize,
)

__all__ = [
    "Harmonization",
    "HarmonizerModel",
    "Cadence",
    "HarmonicPlanDegree",
    "HarmonicPlanProfile",
    "MusesFactories",
    "MusesHarmonization",
    "NoteHarmonization",
    "NoteHarmonizerModel",
    "PieceLike",
    "SATBVoice",
    "build_harmonizer_model",
    "build_note_harmonizer_model",
    "harmonize",
    "harmonize_notes",
    "harmonize_temporal_collection",
    "sample_harmonization",
    "solve_note_harmonizer",
]
