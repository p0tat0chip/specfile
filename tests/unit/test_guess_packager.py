# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import subprocess
from collections.abc import Iterable
from pathlib import Path
from unittest.mock import patch

import pytest
import rpm

from specfile.changelog import guess_packager


@pytest.fixture
def clean_guess_packager(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterable[None]:
    """
    Ensure a clean environment
    """
    # For $RPM_PACKAGER
    monkeypatch.delenv("RPM_PACKAGER", False)
    # Make sure git doesn't read existing config
    monkeypatch.setenv("HOME", "/dev/null")
    monkeypatch.delenv("XDG_CONFIG_HOME", False)
    monkeypatch.chdir(tmp_path)
    # For %packager
    old = rpm.expandMacro("%packager")
    with patch("specfile.changelog._getent_name", return_value=""):
        try:
            rpm.delMacro("packager")
            yield
        finally:
            if old != "%packager":
                rpm.addMacro("packager", old)


@pytest.fixture
def set_packager_env(monkeypatch: pytest.MonkeyPatch) -> str:
    packager = "Patty Packager <patty@packager.me>"
    monkeypatch.setenv("RPM_PACKAGER", packager)
    return packager


@pytest.fixture
def set_packager_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterable[str]:
    packager = "Packager, Patty <packager@patty.dev>"

    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Packager, Patty"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "packager@patty.dev"],
        check=True,
        capture_output=True,
    )
    return packager


@pytest.fixture
def set_packager_macro() -> Iterable[str]:
    try:
        packager = "Patricia Packager"
        rpm.addMacro("packager", packager)
        yield packager
    finally:
        rpm.delMacro("packager")


@pytest.fixture
def set_packager_passwd() -> Iterable[str]:
    packager = "Ms. Packager"
    with patch("specfile.changelog._getent_name", return_value=packager):
        yield packager


def test_guess_packager_env(clean_guess_packager, set_packager_env):
    assert guess_packager() == set_packager_env


def test_guess_packager_macro(clean_guess_packager, set_packager_macro):
    assert guess_packager() == set_packager_macro


def test_guess_packager_git(clean_guess_packager, set_packager_git):
    assert guess_packager() == set_packager_git


def test_guess_packager_passwd(clean_guess_packager, set_packager_passwd):
    assert guess_packager() == set_packager_passwd


def test_guess_packager_pref1(
    clean_guess_packager,
    set_packager_env,
    set_packager_macro,
    set_packager_git,
    set_packager_passwd,
):
    assert guess_packager() == set_packager_env


def test_guess_packager_pref2(
    clean_guess_packager, set_packager_macro, set_packager_git, set_packager_passwd
):
    assert guess_packager() == set_packager_macro


def test_guess_packager_pref3(
    clean_guess_packager, set_packager_git, set_packager_passwd
):
    assert guess_packager() == set_packager_git


def test_guess_packager_pref4(
    clean_guess_packager, set_packager_git, set_packager_passwd
):
    subprocess.run(["git", "config", "--unset", "user.email"])
    assert guess_packager() == "Packager, Patty"

def test_guess_packager_empty(clean_guess_packager):
    """
    The function should return an empty string if it can't detect the packager
    """
    assert guess_packager() == ""
