from goalseek.core.artifact_store import ArtifactStore


def test_copy_file_recreates_missing_run_dir(tmp_path):
    store = ArtifactStore(tmp_path)
    source = tmp_path / "experiment.py"
    source.write_text("print('ok')\n", encoding="utf-8")
    run_dir = tmp_path / "runs" / "0001"

    target = store.copy_file(run_dir, source, "experiment.py")

    assert target.read_text(encoding="utf-8") == "print('ok')\n"


def test_write_helpers_recreate_missing_run_dir(tmp_path):
    store = ArtifactStore(tmp_path)
    run_dir = tmp_path / "runs" / "0001"

    text_path = store.write_text(run_dir, "note.txt", "hi")
    json_path = store.write_json(run_dir, "data.json", {"ok": True})

    assert text_path.read_text(encoding="utf-8") == "hi"
    assert json_path.exists()
