#!/usr/bin/env python3
# This script is invoked to pre-process inputs to adviser. As we download the
# request file from Ceph using Argo, relevant input files for adviser need to
# be extracted. They cannot be supplied directly via environment variables as
# the size of the input can be too large (based on the user request).

"""Prepare inputs to the adviser container."""

import json
import os
from typing import Any
from typing import Dict

_DOCUMENT_ID = os.getenv("THOTH_DOCUMENT_ID")
_REQUEST_FILE_DIR = os.getenv("THOTH_ADVISER_REQUEST_FILE_PATH", "/mnt/workdir/")
_ADVISER_WORKDIR = os.getenv("THOTH_ADVISER_WORKDIR", "/opt/app-root/src")
_ADVISER_INPUTS_DIR = os.path.join(_ADVISER_WORKDIR, "input")
_ADVISER_SUBCOMMAND = os.getenv("THOTH_ADVISER_SUBCOMMAND")


def main() -> None:
    """Prepare input files for adviser."""
    os.makedirs(_ADVISER_INPUTS_DIR, exist_ok=False)

    if not _DOCUMENT_ID:
        raise ValueError("Configuration error: no document id supplied")

    request_file_path = os.path.join(_REQUEST_FILE_DIR, f"{_DOCUMENT_ID}.request")
    if not os.path.isfile(request_file_path):
        raise ValueError("Configuration error: no request file to extract inputs from")

    with open(request_file_path, "r") as fp:
        request_file_content = json.load(fp)

    if _ADVISER_SUBCOMMAND == "advise":
        prepare_adviser(request_file_content)
    elif _ADVISER_SUBCOMMAND == "provenance":
        prepare_provenance(request_file_content)
    elif _ADVISER_SUBCOMMAND == "dependency-monkey":
        prepare_dependency_monkey(request_file_content)
    else:
        raise ValueError(f"Unknown adviser subcommand: {_ADVISER_SUBCOMMAND}")


def _prepare_application_stack(request_file_content: Dict[str, Any]) -> None:
    """Prepare Pipfile and Pipfile.lock."""
    pipfile_content = request_file_content["application_stack"]["requirements"]
    with open(os.path.join(_ADVISER_INPUTS_DIR, "Pipfile"), "w") as pf:
        pf.write(pipfile_content)

    pipfile_lock_content = request_file_content["application_stack"]["requirements_lock"] or "null"
    with open(os.path.join(_ADVISER_INPUTS_DIR, "Pipfile.lock"), "w") as pf:
        pf.write(pipfile_lock_content)


def prepare_adviser(request_file_content: Dict[str, Any]) -> None:
    """Prepare inputs for adviser."""
    _prepare_application_stack(request_file_content)

    library_usage = request_file_content["library_usage"]
    with open(os.path.join(_ADVISER_INPUTS_DIR, "library_usage.json"), "w") as f:
        json.dump(library_usage, f, indent=2)

    runtime_environment = request_file_content["runtime_environment"] or None
    with open(os.path.join(_ADVISER_INPUTS_DIR, "runtime_environment.json"), "w") as f:
        json.dump(runtime_environment, f, indent=2)

    constraints_content = request_file_content.get("constraints") or []
    with open(os.path.join(_ADVISER_INPUTS_DIR, "constraints.txt"), "w") as f:
        json.dump(constraints_content, f, indent=2)

    labels = request_file_content.get("labels") or {}
    with open(os.path.join(_ADVISER_INPUTS_DIR, "labels.json"), "w") as f:
        json.dump(labels, f, indent=2)


def prepare_provenance(request_file_content: Dict[str, Any]) -> None:
    """Prepare inputs for provenance-checker."""
    _prepare_application_stack(request_file_content)


def prepare_dependency_monkey(request_file_content: Dict[str, Any]) -> None:
    """Prepare inputs for dependency-monkey."""
    pipeline = request_file_content["pipeline"]
    with open(os.path.join(_ADVISER_INPUTS_DIR, "pipeline.json"), "w") as f:
        json.dump(pipeline, f, indent=2)

    runtime_environment = request_file_content["runtime_environment"] or None
    with open(os.path.join(_ADVISER_INPUTS_DIR, "runtime_environment.json"), "w") as f:
        json.dump(runtime_environment, f, indent=2)

    requirements = request_file_content["requirements"]
    with open(os.path.join(_ADVISER_INPUTS_DIR, "Pipfile"), "w") as f:
        json.dump(requirements, f, indent=2)

    context = request_file_content["context"] or None
    with open(os.path.join(_ADVISER_INPUTS_DIR, "context.json"), "w") as f:
        json.dump(context, f, indent=2)


__name__ == "__main__" and main()  # type: ignore
