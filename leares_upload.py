"""Sequential LEARES radiology uploads using the recorded Medical records workflow."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


def validate_inputs(patient_names: list[str], file_paths: list[str]) -> list[tuple[str, Path]]:
    if not isinstance(patient_names, list) or not isinstance(file_paths, list):
        raise ValueError("patient_names and file_paths must be lists")
    if not patient_names or len(patient_names) != len(file_paths):
        raise ValueError("Provide nonempty lists with equal lengths")
    if any(not isinstance(name, str) or not name.strip() for name in patient_names):
        raise ValueError("Every patient name must be a nonempty string")
    names = [name.strip() for name in patient_names]
    if len(set(names)) != len(names):
        raise ValueError("Patient names must be unique within this batch")
    pairs = []
    for name, raw_path in zip(names, file_paths):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"Missing file path for {name}")
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"File does not exist: {path}")
        if not path.name.lower().endswith((".nii", ".nii.gz", ".vti", ".nrrd", ".mhd", ".dcm", ".dicom", ".zip")):
            raise ValueError(f"Unsupported radiology file: {path.name}")
        pairs.append((name, path))
    return pairs


def button(page: Page, name: str):
    return page.get_by_role("button", name=name, exact=True)


def dismiss_overlays(page: Page) -> None:
    for name in ("Decline cookies", "Skip Tour"):
        control = button(page, name)
        if control.is_visible():
            control.click()


def login(page: Page, username: str, password: str, timeout_ms: int) -> None:
    page.goto("https://leares.net/login", wait_until="domcontentloaded")
    page.locator("#email").wait_for(state="visible")
    dismiss_overlays(page)
    page.locator("#email").fill(username)
    page.locator("#password").fill(password)
    button(page, "Log in").click()
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        dismiss_overlays(page)
        if button(page, "Logout").is_visible() and page.get_by_title("Medical records", exact=True).is_visible():
            return
        page.wait_for_timeout(250)
    raise RuntimeError("Login did not reach Medical records; check credentials or complete any login challenge")


def open_patient_list(page: Page, database: str, timeout_ms: int = 30000) -> None:
    expand = button(page, f"Expand {database} patients")
    collapse = button(page, f"Collapse {database} patients")
    deadline = time.monotonic() + timeout_ms / 1000
    next_navigation = 0.0
    while time.monotonic() < deadline:
        dismiss_overlays(page)
        if expand.is_visible():
            expand.click()
        if collapse.is_visible():
            return
        # The viewer can finish updating after navigation. Retry only this read-only navigation.
        if time.monotonic() >= next_navigation:
            button(page, "Manage master data").click()
            next_navigation = time.monotonic() + 5
        page.wait_for_timeout(250)
    raise RuntimeError(f"Could not open the patient list for {database}")


def create_and_upload(page: Page, name: str, path: Path, database: str,
                      upload_timeout_ms: int, status: dict, save_status) -> None:
    open_patient_list(page, database)
    patient = page.get_by_text(name, exact=True)
    if patient.count():
        raise RuntimeError(f"Patient {name!r} already exists or matches another visible label; stopped to avoid a duplicate")
    status["stage"] = "creating_patient"
    save_status()
    button(page, f"Create new patient in {database}").click()
    page.get_by_role("textbox", name="Patient name", exact=True).fill(name)
    button(page, "Create patient").click()
    page.get_by_role("textbox", name="Patient name", exact=True).wait_for(state="hidden")
    patient.wait_for(state="visible")
    status["stage"] = "patient_created"
    save_status()
    patient.click()
    page.get_by_title("Upload Data", exact=True).click()
    page.locator("#upload-data-file-input").set_input_files(str(path), timeout=upload_timeout_ms)
    button(page, "Upload Data").click()
    page.get_by_text(path.name, exact=True).wait_for(state="visible", timeout=upload_timeout_ms)
    import_button = button(page, "Import Radiology Files")
    import_button.wait_for(state="visible", timeout=upload_timeout_ms)
    status["stage"] = "importing"
    save_status()
    import_button.click()
    # This dialog was observed only after the imported series opened in the viewer.
    segmentation = page.get_by_text("Automatic Post-Upload Segmentation", exact=True)
    segmentation.wait_for(state="visible", timeout=upload_timeout_ms)
    status["stage"] = "import_completed"
    save_status()
    button(page, "Cancel").click()
    segmentation.wait_for(state="hidden")
    open_patient_list(page, database)
    button(page, f"Collapse {database} patients").click()
    status["stage"] = "completed"
    save_status()


def upload_patients(patient_names: list[str], file_paths: list[str], *,
                    username: str | None = None, password: str | None = None,
                    database: str = "demoDATA", headless: bool = False,
                    upload_timeout_seconds: int = 1200,
                    results_path: str = "upload_results.json") -> list[dict]:
    """Pair names and paths by index. Stop on the first failure; never retry creation/import."""
    pairs = validate_inputs(patient_names, file_paths)
    if upload_timeout_seconds <= 0:
        raise ValueError("upload_timeout_seconds must be positive")
    username = username or os.getenv("LEARES_USERNAME") or input("LEARES email: ").strip()
    password = password or os.getenv("LEARES_PASSWORD") or getpass.getpass("LEARES password: ")
    if not username or not password:
        raise ValueError("Username and password are required")
    results = [{"patient_name": name, "file_path": str(path), "stage": "pending"} for name, path in pairs]
    output = Path(results_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    def save_status():
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(results, indent=2), encoding="utf-8")
        temporary.replace(output)

    save_status()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(30000)
            login(page, username, password, 120000)
            for index, ((name, path), status) in enumerate(zip(pairs, results), start=1):
                print(f"[{index}/{len(pairs)}] Creating and uploading {name}", flush=True)
                try:
                    create_and_upload(page, name, path, database,
                                      upload_timeout_seconds * 1000, status, save_status)
                except Exception as exc:
                    status["failed_at"] = status["stage"]
                    status["stage"] = "failed"
                    # Do not persist exceptions that could include callback URLs/tokens.
                    status["error_type"] = type(exc).__name__
                    save_status()
                    raise RuntimeError(
                        f"Stopped at patient {name!r}, stage {status['failed_at']}. "
                        f"Review LEARES and {output} before rerunning; a patient or import may already exist."
                    ) from None
                print(f"[{index}/{len(pairs)}] Completed {name}", flush=True)
        finally:
            browser.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="JSON object with patient_names and file_paths lists")
    parser.add_argument("--username", help="Email; otherwise LEARES_USERNAME or prompt")
    parser.add_argument("--database", default="demoDATA")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--upload-timeout-seconds", type=int, default=1200)
    parser.add_argument("--results", default="upload_results.json")
    parser.add_argument("--validate-only", action="store_true", help="Check the lists and local files without opening a browser")
    args = parser.parse_args()
    try:
        data = json.loads(args.input_json.read_text(encoding="utf-8-sig"))
        pairs = validate_inputs(data["patient_names"], data["file_paths"])
        if args.validate_only:
            print(f"Validated {len(pairs)} patient/file pairs; no website changes made")
            return 0
        upload_patients(data["patient_names"], data["file_paths"], username=args.username,
                        database=args.database, headless=args.headless,
                        upload_timeout_seconds=args.upload_timeout_seconds, results_path=args.results)
        return 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, PlaywrightTimeoutError) as exc:
        print(f"Upload stopped: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
