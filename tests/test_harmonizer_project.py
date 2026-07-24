from harmonizer.solver import build_harmonizer_model, harmonize


def test_first_harmonizer_returns_legal_weighted_satb_solutions() -> None:
    model = build_harmonizer_model()
    solutions = harmonize(max_solutions=1)

    assert tuple(len(domain) for domain in model.candidates) == (15, 9)
    assert len(solutions) == 1
    solution = solutions[0]
    assert solution.decisions == 2
    assert solution.log_weight < 0
    assert tuple(voicing[0] for voicing in solution.voicings) == (67, 72)
    for voicing in solution.voicings:
        soprano, alto, tenor, bass = voicing
        assert soprano >= alto >= tenor >= bass
        assert soprano - alto <= 12
        assert alto - tenor <= 12
        assert tenor - bass <= 19
