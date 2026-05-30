import logging

from goalseek.core.artifact_store import ArtifactStore
from goalseek.core.project_service import ProjectService


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


def test_artifact_store_logs_only_when_creating_files(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="goalseek")
    store = ArtifactStore(tmp_path)
    run_dir = tmp_path / "runs" / "0001"
    source = tmp_path / "source.txt"
    source.write_text("source\n", encoding="utf-8")

    store.write_text(run_dir, "note.txt", "hi")
    store.write_json(run_dir, "data.json", {"ok": True})
    store.copy_file(run_dir, source, "copy.txt")
    store.append_result({"iteration": 0, "outcome": "baseline", "run_dir": "runs/0000_baseline"})

    assert "[write_text] creating file" in caplog.text
    assert "[write_json] creating file" in caplog.text
    assert "[copy_file] creating file" in caplog.text
    assert "[append_result] creating file" in caplog.text

    caplog.clear()
    store.write_text(run_dir, "note.txt", "bye")
    store.write_json(run_dir, "data.json", {"ok": False})
    store.copy_file(run_dir, source, "copy.txt")
    store.append_result({"iteration": 1, "outcome": "kept", "run_dir": "runs/0001"})

    assert "[write_text] creating file" not in caplog.text
    assert "[write_json] creating file" not in caplog.text
    assert "[copy_file] creating file" not in caplog.text
    assert "[append_result] creating file" not in caplog.text


def test_create_scaffold_logs_created_files(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="goalseek")

    project_root = ProjectService().create_scaffold("demo", path=str(tmp_path), git_init=False)

    assert f"[create_scaffold] creating file {project_root / 'manifest.yaml'}." in caplog.text
    assert f"[create_scaffold] creating file {project_root / 'config' / 'project.yaml'}." in caplog.text
    assert f"[create_scaffold] creating file {project_root / 'runs' / '.gitkeep'}." in caplog.text
