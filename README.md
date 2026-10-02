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

Copy `patients.dicom.example.json` (DICOM ZIP batches) or `patients.example.json` (NIfTI) to `patients.json` and replace the two lists with your patient names and file paths. Each name is paired with the path at the same list index. Use unique new patient names; `Test` and `LIDC-23` already exist from the walkthroughs. JSON Windows paths need doubled backslashes, as shown in the examples.

```json
{
  "patient_names": ["LIDC-24", "LIDC-25"],
  "file_paths": ["D:\\CT_DATA\\LIDC-24\\dcm.zip", "D:\\CT_DATA\\LIDC-25\\dcm.zip"]
}
```

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

The implementation follows the observed NIfTI and DICOM ZIP workflows. ZIP archives are expanded by LEARES into individual DICOM files: the script waits for a nonzero file count, clicks Import Radiology Files once, dismisses any tour, waits for the post-upload segmentation dialog, clicks Cancel, and returns to Manage master data with the database collapsed. Then it starts the next patient. If importing is already underway, it waits without submitting again. Other radiology formats that open extra series-selection dialogs may need additional handling. PDF/XML uploads and segmentation are outside this workflow.

The walkthroughs successfully uploaded `T1 - PRE.nii.gz` for `Test` and `dcm.zip` for `LIDC-23`. The ZIP walkthrough exposed and corrected a filename wait that blocked the import button; that run used a manual import click. Cancel and return to Manage master data were verified live. Local regression tests cover extracted ZIP contents, a NIfTI file, and an import already in progress. A complete unattended batch with the corrected script has not yet been run.

Run the local browser regression checks with `python -m unittest test_import_workflow.py`; they do not connect to LEARES.
