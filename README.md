# LEARES sequential patient uploader

Uses Playwright in the existing Anaconda `collab` environment. Each patient name is paired with the file path at the same index. The script logs in, cancels the tour, opens Medical records, creates each patient in demoDATA, imports its radiology file, cancels automatic segmentation, and returns to the patient list before continuing.

## Set up on another system

Install Python 3.10 or newer, then run from this directory in an activated virtual environment or Conda environment:

```text
python -m pip install -r requirements.txt
python -m playwright install chromium
```

On Linux, install Chromium's system dependencies with `python -m playwright install --with-deps chromium` instead of the second command; this may require administrator privileges. Update the input JSON file paths to files present on the new system. Anaconda is optional.

## Run

Copy `patients.example.json` to `patients.json` and replace the two lists with your patient names and file paths. Use unique new patient names; `Test` already exists from the recorded walkthrough. JSON Windows paths need doubled backslashes, as shown in the example.

From this directory in PowerShell:

```powershell
conda activate collab
python leares_upload.py patients.json --validate-only
python leares_upload.py patients.json --username pbor.manash@gmail.com
```

The password is requested privately through a prompt. Alternatively supply `LEARES_USERNAME` and `LEARES_PASSWORD` as environment variables. Credentials are never saved in the code or results.

If conda is unavailable in your shell:

```powershell
& 'C:\Users\manas\anaconda3\envs\collab\python.exe' leares_upload.py patients.json --username pbor.manash@gmail.com
```

## Use from Python

```python
from leares_upload import upload_patients

patient_names = ["Patient_A", "Patient_B"]
file_paths = [r"E:\data\scan_a.nii.gz", r"E:\data\scan_b.nii.gz"]
upload_patients(patient_names, file_paths, username="pbor.manash@gmail.com")
```

The browser is visible by default. Add `--headless` to hide it or change the default 20-minute per-import timeout with `--upload-timeout-seconds 1800`.

## Progress and failures

`upload_results.json` records the current stage for every patient and is updated after each major step. The script stops on the first failure and leaves later patients pending. Creation and import are never automatically retried, since doing so could create duplicates. Inspect the website and results before rerunning, then remove completed or partially created patients from the input or resolve them manually. A completed import may still be present even if navigation afterward fails.

The implementation follows the observed NIfTI radiology workflow. Other radiology extensions accepted by the form are allowed, but formats that open extra series-selection dialogs may need additional handling. PDF/XML uploads and segmentation are outside this workflow.

The walkthrough successfully uploaded `T1 - PRE.nii.gz` for `Test`. Syntax compilation, sample input validation, and five invalid-input checks passed. The script's return-to-list helper was also verified against the live session without creating additional patients. A fresh batch execution remains to be checked with your next intended upload.
