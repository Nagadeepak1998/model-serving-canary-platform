from model_serving_canary_platform.rollout import CanaryRouter


def test_rollout_is_stable_for_ticket() -> None:
    router = CanaryRouter("baseline", "canary")

    first = router.decide("INC-12345", 25)
    second = router.decide("INC-12345", 25)

    assert first == second


def test_full_rollout_selects_canary() -> None:
    router = CanaryRouter("baseline", "canary")

    decision = router.decide("INC-22222", 100)

    assert decision.selected_model == "canary"
