"""Exercise shell entry points in disposable projects, without external services."""

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project with spaces"
    shutil.copytree(SCRIPTS, root / "scripts")
    (root / "bin").mkdir()
    return root


def executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\nset -eu\n" + content)
    path.chmod(0o755)


def run_script(
    project: Path,
    script: str,
    *args: str,
    input_text: str = "",
    overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        key: value for key, value in os.environ.items() if key not in {"DATABASE_URL", "BASH_ENV"}
    }
    env.update(
        PATH=f"{project / 'bin'}:/usr/bin:/bin",
        PYTHONPATH="",
        LLM_SERVER_N_GPU_LAYERS="0",
        MODELS_DIR=str(project / "models"),
    )
    env.update(overrides or {})
    return subprocess.run(
        ["bash", str(project / "scripts" / script), *args],
        cwd=project.parent,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def install_python_stub(project: Path) -> None:
    executable(
        project / ".venv/bin/python",
        'if [[ "${1:-}" == -m && "${2:-}" == alembic ]]; then\n'
        '  printf "%s\\n" "$*" >> "$COMMAND_LOG"\n'
        '  exit "${MIGRATION_STATUS:-0}"\n'
        "fi\n"
        f'exec "{sys.executable}" "$@"\n',
    )


@pytest.mark.parametrize("script", ["clean.sh", "db.sh", "env.sh", "llm.sh"])
@pytest.mark.parametrize("args", [("typo",), ("--help",), ("exit",)])
def test_arguments_are_handled_without_side_effects(
    project: Path, script: str, args: tuple[str, ...]
) -> None:
    result = run_script(project, script, *args)
    assert result.returncode == (2 if args == ("typo",) else 0), result.stderr
    assert not (project / ".env").exists()
    assert not (project / "data").exists()
    assert not (project / "logs").exists()


@pytest.mark.parametrize(
    "script,command",
    [("clean.sh", "data"), ("db.sh", "upgrade"), ("env.sh", "quick"), ("llm.sh", "start")],
)
def test_extra_arguments_do_not_run_commands(project: Path, script: str, command: str) -> None:
    result = run_script(project, script, command, "invalid")
    assert result.returncode == 2
    assert not (project / ".env").exists()
    assert not (project / "data").exists()


@pytest.mark.parametrize("command", ["inspect", "gpu"])
def test_environment_inspection_does_not_create_env(project: Path, command: str) -> None:
    result = run_script(project, "env.sh", command)
    assert result.returncode == 0, result.stderr
    assert not (project / ".env").exists()


def test_uv_sync_runs_in_project_root(project: Path) -> None:
    log = project / "commands"
    executable(project / "bin/uv", 'printf "%s\\n" "$PWD" "$*" >> "$COMMAND_LOG"\n')
    result = run_script(project, "env.sh", "quick", overrides={"COMMAND_LOG": str(log)})
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [str(project), "sync"]


def test_pip_fallback_creates_and_uses_virtual_environment(project: Path) -> None:
    log = project / "commands"
    executable(
        project / "bin/python3",
        'printf "%s\\n" "$0 $*" >> "$COMMAND_LOG"\n'
        'if [[ "${1:-}" == -m && "${2:-}" == venv ]]; then\n'
        '  mkdir -p "$3/bin"\n'
        '  cp "$0" "$3/bin/python"\n'
        "fi\n",
    )
    result = run_script(project, "env.sh", "quick", overrides={"COMMAND_LOG": str(log)})
    assert result.returncode == 0, result.stderr
    lines = log.read_text().splitlines()
    assert "-m venv" in lines[0]
    assert lines[1].startswith(f"{project}/.venv/bin/python -m pip install")


def test_failed_cleanup_does_not_report_success(project: Path) -> None:
    executable(project / "bin/find", "exit 1\n")
    result = run_script(project, "clean.sh", "artifacts", input_text="y\nCLEAN\n")
    assert result.returncode != 0
    assert "generated code cleaned" not in result.stdout


def test_cleanup_refuses_symlinked_data(project: Path) -> None:
    external = project.parent / "external"
    external.mkdir()
    (external / "keep").write_text("preserve")
    (project / "data").symlink_to(external, target_is_directory=True)
    result = run_script(project, "clean.sh", "data", input_text="y\nCLEAN\n")
    assert result.returncode != 0
    assert (external / "keep").read_text() == "preserve"


def test_status_does_not_create_missing_database(project: Path) -> None:
    install_python_stub(project)
    log = project / "commands"
    result = run_script(project, "db.sh", "status", overrides={"COMMAND_LOG": str(log)})
    assert result.returncode == 0, result.stderr
    assert not (project / "data").exists()
    assert log.read_text().splitlines() == ["-m alembic history --verbose"]


def test_explicit_database_environment_overrides_dotenv(project: Path) -> None:
    install_python_stub(project)
    (project / ".env").write_text("DATABASE_URL=sqlite:///wrong.sqlite3\n")
    result = run_script(
        project,
        "db.sh",
        "status",
        overrides={
            "DATABASE_URL": "sqlite:///chosen.sqlite3",
            "COMMAND_LOG": str(project / "commands"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert str(project / "chosen.sqlite3") in result.stdout
    assert not (project / "wrong.sqlite3").exists()


def test_generated_migration_requires_review_before_apply(project: Path) -> None:
    install_python_stub(project)
    log = project / "commands"
    result = run_script(
        project,
        "db.sh",
        "both",
        "-m",
        "review me",
        input_text="n\n",
        overrides={"COMMAND_LOG": str(log)},
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ["-m alembic revision --autogenerate -m review me"]


def make_database(project: Path) -> Path:
    path = project / "data/db.sqlite3"
    path.parent.mkdir()
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE experiments (id INTEGER)")
        connection.execute("INSERT INTO experiments VALUES (42)")
    return path


@pytest.mark.parametrize(
    "command,confirmation", [("clear", "CLEAR"), ("reset", "RESET"), ("rollback", "")]
)
def test_destructive_database_commands_preserve_verified_backup(
    project: Path, command: str, confirmation: str
) -> None:
    install_python_stub(project)
    executable(project / "bin/lsof", "exit 1\n")
    database = make_database(project)
    result = run_script(
        project,
        "db.sh",
        command,
        input_text=f"y\n{confirmation}\n",
        overrides={"COMMAND_LOG": str(project / "commands")},
    )
    assert result.returncode == 0, result.stderr
    backups = list(database.parent.glob("*.bak"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert connection.execute("SELECT id FROM experiments").fetchall() == [(42,)]


def test_busy_database_cannot_be_reset(project: Path) -> None:
    install_python_stub(project)
    executable(project / "bin/lsof", "echo 12345\n")
    database = make_database(project)
    original = database.read_bytes()
    result = run_script(project, "db.sh", "reset", input_text="y\nRESET\n")
    assert result.returncode != 0
    assert "in use" in result.stderr
    assert database.read_bytes() == original
    assert not list(database.parent.glob("*.bak"))


def test_corrupt_database_is_not_deleted(project: Path) -> None:
    install_python_stub(project)
    executable(project / "bin/lsof", "exit 1\n")
    database = project / "data/db.sqlite3"
    database.parent.mkdir()
    database.write_bytes(b"not a database")
    result = run_script(project, "db.sh", "reset", input_text="y\nRESET\n")
    assert result.returncode != 0
    assert database.read_bytes() == b"not a database"
    assert not list(database.parent.glob("*.bak"))


def test_stop_refuses_unrelated_pid(project: Path) -> None:
    (project / "logs").mkdir()
    (project / "logs/server.pid").write_text("12345\n")
    hooks = project / "hooks"
    hooks.write_text('kill() { echo "$*" >> "$KILL_LOG"; return 0; }\n')
    executable(project / "bin/ps", "echo 'unrelated-service'\n")
    log = project / "kills"
    result = run_script(
        project, "llm.sh", "stop", overrides={"BASH_ENV": str(hooks), "KILL_LOG": str(log)}
    )
    assert result.returncode != 0
    assert "refusing" in result.stderr
    assert all(line.startswith("-0 ") for line in log.read_text().splitlines())
    assert (project / "logs/server.pid").exists()


@pytest.mark.parametrize("model,expected", [("different.gguf", 1), ("model's-name.gguf", 0)])
def test_start_checks_model_identity_and_handles_quoted_names(
    project: Path, model: str, expected: int
) -> None:
    install_python_stub(project)
    (project / "models").mkdir()
    (project / "models/model's-name.gguf").write_bytes(b"fixture")
    executable(project / "bin/curl", 'printf \'{"data":[{"id":"%s"}]}\' "$ACTIVE_MODEL"\n')
    result = run_script(project, "llm.sh", "start", overrides={"ACTIVE_MODEL": model})
    assert result.returncode == expected, result.stderr
    assert not (project / "logs/server.pid").exists()


def test_http_errors_are_not_accepted_as_ready(project: Path) -> None:
    install_python_stub(project)
    executable(
        project / "bin/curl",
        '[[ "$*" == *"--fail"* && "$*" == *"--max-time"* ]] || exit 99\nexit 22\n',
    )
    result = run_script(project, "llm.sh", "status")
    assert result.returncode == 0, result.stderr
    assert "Unresponsive" in result.stdout


def test_cleanup_refuses_broad_model_directory(project: Path) -> None:
    install_python_stub(project)
    result = run_script(project, "llm.sh", "cleanup", overrides={"MODELS_DIR": str(project)})
    assert result.returncode != 0
    assert "unsafe model directory" in result.stderr


@pytest.mark.parametrize("matching_identity", [True, False])
def test_stop_checks_process_identity(project: Path, matching_identity: bool) -> None:
    logs = project / "logs"
    logs.mkdir()
    (logs / "server.pid").write_text("12345\n")
    (logs / "server.pid.identity").write_text("original start\n")
    state = project / "running"
    state.touch()
    hooks = project / "hooks"
    hooks.write_text(
        "kill() {\n"
        '  if [[ "$1" == -0 ]]; then [[ -f "$RUNNING_STATE" ]]; return; fi\n'
        '  echo "$*" >> "$KILL_LOG"\n'
        '  rm "$RUNNING_STATE"\n'
        "}\n"
    )
    executable(
        project / "bin/ps",
        'if [[ "$*" == *command=* ]]; then echo "project-python -m llama_cpp.server";\n'
        'else echo "$PROCESS_IDENTITY"; fi\n',
    )
    log = project / "kills"
    result = run_script(
        project,
        "llm.sh",
        "stop",
        overrides={
            "BASH_ENV": str(hooks),
            "KILL_LOG": str(log),
            "RUNNING_STATE": str(state),
            "PROCESS_IDENTITY": "original start" if matching_identity else "reused PID start",
        },
    )
    if matching_identity:
        assert result.returncode == 0, result.stderr
        assert log.read_text().splitlines() == ["12345"]
        assert not (logs / "server.pid").exists()
        assert not (logs / "server.pid.identity").exists()
    else:
        assert result.returncode != 0
        assert not log.exists()
        assert state.exists()


def test_uv_fallback_uses_separate_arguments(project: Path) -> None:
    log = project / "commands"
    executable(
        project / "bin/uv",
        'printf "%s\\n" "$1" "$2" "$3" "$4" >> "$COMMAND_LOG"\n'
        '[[ "$1" == run && "$2" == --project && "$4" == python ]]\n'
        "shift 4\n"
        'if [[ "${1:-}" == -m ]]; then exit 0; fi\n'
        f'exec "{sys.executable}" "$@"\n',
    )
    result = run_script(project, "db.sh", "status", overrides={"COMMAND_LOG": str(log)})
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ["run", "--project", str(project), "python"] * 2


def test_backup_contains_committed_wal_and_never_overwrites(project: Path) -> None:
    database = make_database(project)
    with sqlite3.connect(database) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO experiments VALUES (99)")
        writer.commit()
        assert Path(f"{database}-wal").exists()
        for _ in range(2):
            subprocess.run(
                [
                    sys.executable,
                    str(project / "scripts/utils/db_ops.py"),
                    "backup",
                    "--db",
                    str(database),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        backups = list(database.parent.glob("*.bak"))
        assert len(backups) == 2
        for backup in backups:
            with sqlite3.connect(backup) as reader:
                assert reader.execute("SELECT id FROM experiments").fetchall() == [(42,), (99,)]


def test_migration_failures_are_not_reported_as_success(project: Path) -> None:
    install_python_stub(project)
    result = run_script(
        project,
        "db.sh",
        "upgrade",
        overrides={"COMMAND_LOG": str(project / "commands"), "MIGRATION_STATUS": "7"},
    )
    assert result.returncode == 7
    assert "Database is up to date" not in result.stdout


def test_reset_can_still_initialize_a_missing_database(project: Path) -> None:
    install_python_stub(project)
    log = project / "commands"
    result = run_script(
        project, "db.sh", "reset", input_text="y\nRESET\n", overrides={"COMMAND_LOG": str(log)}
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ["-m alembic upgrade head"]


def test_server_exit_status_is_preserved_and_pid_is_cleaned(project: Path) -> None:
    executable(
        project / ".venv/bin/python",
        'if [[ "${1:-}" == -m && "${2:-}" == llama_cpp.server ]]; then\n'
        "  /bin/sleep 1\n"
        "  exit 9\n"
        "fi\n"
        f'exec "{sys.executable}" "$@"\n',
    )
    (project / "models").mkdir()
    (project / "models/mock.gguf").write_bytes(b"fixture")
    executable(project / "bin/lsof", "exit 1\n")
    executable(project / "bin/ps", "echo 'mock process identity'\n")
    executable(
        project / "bin/curl",
        'if [[ ! -f "$PROBE_STATE" ]]; then touch "$PROBE_STATE"; exit 7; fi\n'
        'echo \'{"data":[{"id":"mock.gguf"}]}\'\n',
    )
    result = run_script(
        project, "llm.sh", "start", overrides={"PROBE_STATE": str(project / "probed")}
    )
    assert result.returncode == 9, result.stderr
    assert "Server is ready" in result.stdout
    assert not (project / "logs/server.pid").exists()
    assert not (project / "logs/server.pid.identity").exists()


def test_server_startup_failure_does_not_leave_pid_file(project: Path) -> None:
    executable(
        project / ".venv/bin/python",
        'if [[ "${1:-}" == -m && "${2:-}" == llama_cpp.server ]]; then exit 7; fi\n'
        f'exec "{sys.executable}" "$@"\n',
    )
    (project / "models").mkdir()
    (project / "models/mock.gguf").write_bytes(b"fixture")
    executable(project / "bin/lsof", "exit 1\n")
    executable(project / "bin/ps", "echo 'mock process identity'\n")
    executable(project / "bin/curl", "exit 7\n")
    result = run_script(project, "llm.sh", "start")
    assert result.returncode != 0
    assert not (project / "logs/server.pid").exists()


@pytest.mark.parametrize("script", ["clean.sh", "db.sh", "env.sh", "llm.sh"])
def test_shell_syntax(script: str) -> None:
    subprocess.run(["bash", "-n", str(SCRIPTS / script)], check=True)
