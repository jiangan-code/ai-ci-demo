from shop import flags


def test_same_user_always_gets_same_bucket():
    assert flags.bucket("full_reduction", "u42") == flags.bucket("full_reduction", "u42")


def test_unknown_flag_is_off():
    assert flags.is_enabled("no_such_flag", "u42") is False


def test_zero_percent_means_nobody(monkeypatch):
    monkeypatch.setitem(flags.ROLLOUT_PERCENT, "full_reduction", 0)
    assert not any(flags.is_enabled("full_reduction", f"u{i}") for i in range(1000))
