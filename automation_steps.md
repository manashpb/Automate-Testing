# LEARES automation — fresh recording

Started: 2026-10-01. This record replaces the discarded attempt.

Runtime: `C:\Users\manas\anaconda3\envs\collab\python.exe`
Browser: Playwright Chromium, headed, with a persistent running browser context.
Credentials must be supplied at runtime and excluded from source files and logs.

## 1. Log in

1. Open `https://leares.net/login` in a fresh browser context.
2. Wait for `page.locator("#email")` to be visible.
3. If visible, click `page.get_by_role("button", name="Decline cookies", exact=True)`.
4. Fill `#email` and `#password` with the supplied credentials.
5. Click `page.get_by_role("button", name="Log in", exact=True)`.
6. Wait for the authenticated interface: `page.get_by_role("button", name="Logout", exact=True)` becomes visible.

Do not log full redirect URLs: the OAuth callback fragment may contain an authentication token.

## 2. Dismiss introductory UI

1. The tour appeared after the authenticated interface finished loading (`Step 1 of 2`, `Switch View Mode`).
2. Click `page.get_by_role("button", name="Skip Tour", exact=True)` to cancel it.
3. Dismiss the dedicated site's cookie banner with its `Decline cookies` button.
4. Confirm the `Logout` button remains visible, indicating the authenticated session is ready.

Stop here awaiting the next instruction. No navigation to AI Training or creation of projects has been performed in this fresh attempt.

## 3. Expand demoDATA and click +

1. In the default Medical records view, click `page.get_by_role("button", name="Expand demoDATA patients", exact=True)`.
2. Verify the button changes to `Collapse demoDATA patients` and the patient list appears.
3. Click the plus button: `page.get_by_role("button", name="Create new patient in demoDATA", exact=True).click()`.
4. Verified result: an inline new-patient name entry opens, with the instruction `Leave blank to use an automatic name`. Await the next instruction before submitting.

## 4. Name and create the patient

1. Set the runtime input `patient_name` to `Test` for this recorded run. The future script must accept this value as an input parameter.
2. Fill `page.get_by_role("textbox", name="Patient name", exact=True)` with `patient_name`.
3. Click the green tick using `page.get_by_role("button", name="Create patient", exact=True).click()`.
4. Wait for `page.get_by_text(patient_name, exact=True)` to become visible.
5. Verified result: `Test` appears in the patient list and the inline patient-name input closes.

```python
patient_name = "Test"  # Replace with a caller-provided input in the final script.
page.get_by_role("textbox", name="Patient name", exact=True).fill(patient_name)
page.get_by_role("button", name="Create patient", exact=True).click()
page.get_by_text(patient_name, exact=True).wait_for(state="visible")
```

## 5. Open the created patient

1. Click `page.get_by_text(patient_name, exact=True).click()` while the patient name appears once in the list.
2. Performed with `patient_name = "Test"`.
3. Verified result: the patient detail panel opens, displaying `patient`, `Test`, and the account owner and collaborators information.
4. After opening, the name appears in both the list and detail panel. Subsequent clicks must use a scoped locator if needed to avoid multiple matches.

## 6. Open Upload Data

1. Click the top-left upload button using `page.get_by_title("Upload Data", exact=True).click()`.
2. Verified result: the `Upload Data` panel opens for `Patient: Test`, with a file drop/browse area, automatic format detection instructions, hospital PACS import, and manual spirometry entry.
3. No file has been selected or uploaded.

## 7. Select the input data file

1. Accept `file_path` as an input parameter in the future script. This run uses `E:\FREELANCE\SIMONE\GEMELLI\PRE\T1 - PRE.nii.gz`.
2. Confirm the path exists before selection.
3. The browse text is intercepted by the surrounding drop area when clicked directly. Use the underlying file input for reliable automation:

```python
page.locator("#upload-data-file-input").set_input_files(file_path)
```

4. Verified result: the upload panel displays `Selected file: T1 - PRE.nii.gz` and `Size: 179194.47 KB`.
5. No additional upload/import confirmation has been clicked in this step.

## 8. Upload and import the selected NIfTI file

1. Click `page.get_by_role("button", name="Upload Data", exact=True).click()` in the upload panel.
2. This opens `Radiology Import`; wait for the selected file to appear under `Files (1)` (initially it shows `Files (0)` while loading).
3. Verified staging result: `T1 - PRE.nii.gz`, `175.0 MB`.
4. Click `page.get_by_role("button", name="Import Radiology Files", exact=True).click()`.
5. The import begins and displays `Preparing files...`. Wait for the final result before reporting completion.
6. The status changes to `Uploading and processing files...`.
7. Verified completion: the viewer opens for patient `Test`, displaying `Series: T1 - PRE`. An `Automatic Post-Upload Segmentation` dialog appears with Cardiac, Lungs, and Whole Body options, plus Cancel and Start Segmentation buttons.
8. Stop at that dialog awaiting the next instruction; no segmentation has been started.

## 9. Cancel automatic segmentation

1. Click `page.get_by_role("button", name="Cancel", exact=True).click()` in the automatic post-upload segmentation dialog.
2. Wait for `page.get_by_text("Automatic Post-Upload Segmentation", exact=True)` to become hidden.
3. The imported series remains loaded; no automatic segmentation was requested.

## 10. Return to the patient list

1. Click `page.get_by_role("button", name="Manage master data", exact=True).click()`.
2. Wait for the Medical records list with `demoDATA` to appear. In this run, the first click was interrupted by the viewer updating; a second click opened the list.
3. The database initially appears collapsed. Click `page.get_by_role("button", name="Expand demoDATA patients", exact=True)` if visible to show its patients.
4. Verify `Test` is visible and the database button is named `Collapse demoDATA patients`.
5. A website error notification appeared during navigation: `patient radiology. Cannot read properties of null (reading 'children').` The patient list still opened successfully.

## 11. Click demoDATA again

1. Click `page.get_by_role("button", name="Collapse demoDATA patients", exact=True).click()`.
2. Verified result: the patient list collapses and the button changes to `Expand demoDATA patients`.
