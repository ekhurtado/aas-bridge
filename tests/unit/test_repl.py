"""Unit tests for the standard-library REPL (actions stubbed, no stdin)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aas_bridge.cli import actions, i18n, repl
from aas_bridge.cli import main as cli
from aas_bridge.engine.detect import DetectionResult, PartDetection

runner = CliRunner()


def feed(lines: list[str]) -> Callable[[str], str]:
    iterator = iter(lines)

    def input_fn(prompt: str) -> str:
        try:
            return next(iterator)
        except StopIteration:
            raise EOFError from None

    return input_fn


def _detection(label: str | None) -> DetectionResult:
    declared = None if label is None else f"https://admin-shell.io/aas/3/{label[-1]}"
    return DetectionResult(
        file="file.aasx",
        parts=[
            PartDetection(
                part_name="/aasx/data.xml",
                format="xml",
                declared_version=declared,
                version_label=label,
            )
        ],
        consistent=label is not None,
        version_label=label,
    )


def test_banner_and_prompt_in_both_locales(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.PROMPT == "aas-bridge> "
    assert repl.run_repl(language="en", input_fn=feed(["exit"])) == 0
    english = capsys.readouterr().out
    assert "AAS Bridge 0.2.0 — AASX detection & migration (AAS 3.x)" in english
    assert "type 'help' for commands, 'exit' to leave" in english

    assert repl.run_repl(language="es", input_fn=feed(["exit"])) == 0
    spanish = capsys.readouterr().out
    assert "AAS Bridge 0.2.0 — AASX detection & migration (AAS 3.x)" in spanish
    assert "escribe 'help' para ver los comandos" in spanish


def test_banner_keys_are_complete_in_both_locales() -> None:
    for key in ("repl.banner_title", "repl.banner_hint"):
        assert set(i18n.MESSAGES[key]) == set(i18n.SUPPORTED_LANGUAGES)


@pytest.mark.parametrize("command", ["exit", "quit"])
def test_exit_and_quit_return_zero(command: str) -> None:
    assert repl.run_repl(language="en", input_fn=feed([command])) == 0


def test_eof_returns_zero() -> None:
    assert repl.run_repl(language="en", input_fn=feed([])) == 0


def test_ctrl_c_returns_zero() -> None:
    def interrupt(prompt: str) -> str:
        raise KeyboardInterrupt

    assert repl.run_repl(language="en", input_fn=interrupt) == 0


def test_help_lists_the_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.run_repl(language="en", input_fn=feed(["help", "exit"])) == 0

    output = capsys.readouterr().out
    assert "Commands:" in output
    for command in ("check", "migrate", "smia", "update", "lang", "version", "exit"):
        assert command in output


def test_help_for_one_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.run_repl(language="en", input_fn=feed(["help check", "exit"])) == 0

    assert "check <file>" in capsys.readouterr().out


def test_version_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.run_repl(language="en", input_fn=feed(["version", "exit"])) == 0

    assert "aas-bridge 0.2.0" in capsys.readouterr().out


def test_unknown_command_is_reported_and_the_loop_continues(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert repl.run_repl(language="en", input_fn=feed(["bogus", "version", "exit"])) == 0

    captured = capsys.readouterr()
    assert "Unknown command: bogus" in captured.err
    assert "aas-bridge 0.2.0" in captured.out


def test_lang_changes_the_session_language(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(actions, "detect_versions", lambda path: _detection("3.0"))
    package = tmp_path / "package.aasx"
    package.write_bytes(b"placeholder")

    code = repl.run_repl(
        language="en",
        input_fn=feed(["lang", "lang es", f'check "{package}"', "exit"]),
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "Language: en" in output
    assert "Language set to es." in output
    assert "Detectado: AAS 3.0" in output
    assert "Actualización disponible: sí" in output


def test_lang_invalid_keeps_the_previous_language(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.run_repl(language="en", input_fn=feed(["lang fr", "lang", "exit"])) == 0

    captured = capsys.readouterr()
    assert "Unsupported language" in captured.err
    assert "Language: en" in captured.out


def test_check_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        actions, "execute_check", lambda file, language: calls.append((file, language)) or 0
    )

    assert repl.run_repl(language="es", input_fn=feed(["check file.aasx", "exit"])) == 0
    assert calls == [(Path("file.aasx"), "es")]


def test_migrate_dispatch_with_a_windows_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, str, Path | None]] = []
    monkeypatch.setattr(
        actions,
        "execute_migrate",
        lambda file, language, report: calls.append((file, language, report)) or 0,
    )

    code = repl.run_repl(
        language="en",
        input_fn=feed(
            [
                'migrate "C:\\dir with space\\f.aasx" --report "C:\\reports\\r.json"',
                "exit",
            ]
        ),
    )

    assert code == 0
    assert calls == [
        (
            Path("C:\\dir with space\\f.aasx"),
            "en",
            Path("C:\\reports\\r.json"),
        )
    ]


def test_smia_dispatch_with_and_without_a_file(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Path | None, str]] = []
    monkeypatch.setattr(
        actions, "execute_smia", lambda file, language: calls.append((file, language)) or 0
    )

    assert repl.run_repl(language="en", input_fn=feed(["smia", "smia file.aasx", "exit"])) == 0
    assert calls == [(None, "en"), (Path("file.aasx"), "en")]


def test_update_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(actions, "execute_update", lambda language: calls.append(language) or 0)

    assert repl.run_repl(language="en", input_fn=feed(["update", "exit"])) == 0
    assert calls == ["en"]


@pytest.mark.parametrize(
    ("line", "usage"),
    [
        ("check", "check <file>"),
        ("migrate", "migrate <file> [--report <path>]"),
        ("migrate file.aasx --bad value", "migrate <file> [--report <path>]"),
        ("smia a b", "smia [file]"),
        ("update extra", "update"),
        ("lang en extra", "Language set to en."),
    ],
)
def test_argument_usage_errors(
    line: str, usage: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(actions, "execute_check", lambda file, language: 0)
    monkeypatch.setattr(actions, "execute_migrate", lambda file, language, report: 0)
    monkeypatch.setattr(actions, "execute_smia", lambda file, language: 0)
    monkeypatch.setattr(actions, "execute_update", lambda language: 0)

    assert repl.run_repl(language="en", input_fn=feed([line, "exit"])) == 0
    captured = capsys.readouterr()
    assert usage in (captured.out + captured.err)


def test_tokenize_preserves_windows_backslashes_and_strips_quotes() -> None:
    assert repl.tokenize('migrate "C:\\dir with space\\f.aasx"') == [
        "migrate",
        "C:\\dir with space\\f.aasx",
    ]
    assert repl.tokenize("check 'C:\\dir\\f.aasx'") == ["check", "C:\\dir\\f.aasx"]
    assert repl.tokenize("check C:\\dir\\f.aasx") == ["check", "C:\\dir\\f.aasx"]


def test_unmatched_quote_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    assert repl.run_repl(language="en", input_fn=feed(['check "unterminated', "exit"])) == 0

    assert "Cannot parse the command line" in capsys.readouterr().err


def test_bare_invocation_opens_the_repl() -> None:
    result = runner.invoke(cli.app, [], input="exit\n")

    assert result.exit_code == 0
    assert "AAS Bridge 0.2.0" in result.stdout
    assert "aas-bridge> " in result.stdout


def test_shell_command_opens_the_repl() -> None:
    result = runner.invoke(cli.app, ["shell"], input="exit\n")

    assert result.exit_code == 0
    assert "AAS Bridge 0.2.0" in result.stdout
