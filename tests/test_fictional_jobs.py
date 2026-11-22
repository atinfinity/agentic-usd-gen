"""agentic-usd-gen-fictional --jobs builds each product in its own process."""

import pytest

from agentic_usd_gen.fictional import main


def _files(root):  # vision.json holds absolute image paths: the cache folder's own path is left out
    return {p.relative_to(root): p.read_bytes().replace(str(root).encode(), b"<cache>")
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_jobs_write_the_same_cache(tmp_path):
    names = ["soda_pet_500ml", "potato_chips_bag", "stick_snack_box"]
    assert main([*names, "--no-build", "--cache", str(tmp_path / "serial")]) == 0
    assert main([*names, "--no-build", "--cache", str(tmp_path / "jobs"), "--jobs", "3"]) == 0
    serial, jobs = _files(tmp_path / "serial"), _files(tmp_path / "jobs")
    assert serial and serial.keys() == jobs.keys()
    assert [k for k in serial if serial[k] != jobs[k]] == []


def test_failed_product_sets_status(tmp_path, monkeypatch):
    from agentic_usd_gen import fictional

    monkeypatch.setattr(fictional.cli, "main", lambda argv: 1)  # serial path: the build's exit code is kept
    assert main(["soda_pet_500ml", "--cache", str(tmp_path)]) == 1


def test_failed_product_does_not_stop_the_others(tmp_path):
    """agentic-usd-gen exits on an unknown option (SystemExit in the worker): every product still runs and is reported."""
    names = ["soda_pet_500ml", "stick_snack_box"]
    for jobs in ("1", "2"):
        assert main([*names, "--cache", str(tmp_path / jobs), "--jobs", jobs, "--no-such-option"]) != 0
        assert all((tmp_path / jobs / d / "spec.json").exists() for d in {p.name for p in (tmp_path / jobs).iterdir()})
        assert len(list((tmp_path / jobs).iterdir())) == 2


def test_jobs_refuse_one_slug_for_all(tmp_path):
    with pytest.raises(SystemExit):
        main(["soda_pet_500ml", "stick_snack_box", "--cache", str(tmp_path), "--jobs", "2", "--slug", "x"])
