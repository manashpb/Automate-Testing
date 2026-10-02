"""Local browser regression checks; these never connect to LEARES."""
import unittest

from playwright.sync_api import sync_playwright

from leares_upload import finish_radiology_import


class ImportWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def run_import(self, initial_content, automatic=False):
        page = self.browser.new_page()
        try:
            page.set_content(r'''<main id="screen"></main><script>
              window.importClicks = 0;
              function completed() {
                document.querySelector('#screen').innerHTML =
                  '<p>Automatic Post-Upload Segmentation</p>' +
                  '<button onclick="document.querySelector(\'#screen\').innerHTML=\'Viewer\'">Cancel</button>';
              }
              function startImport() {
                window.importClicks++;
                document.querySelector('#screen').innerHTML = '<p>Uploading and processing files...</p>';
                setTimeout(completed, 100);
              }
            </script>''')
            page.locator('#screen').evaluate('(e, html) => e.innerHTML = html', initial_content)
            if automatic:
                page.evaluate('setTimeout(completed, 100)')
            status = {'stage': 'preparing_import'}
            finish_radiology_import(page, 3000, status, lambda: None)
            self.assertEqual(status['stage'], 'import_completed')
            self.assertEqual(page.locator('#screen').inner_text(), 'Viewer')
            return page.evaluate('window.importClicks')
        finally:
            page.close()

    def test_extracted_zip_without_original_filename(self):
        clicks = self.run_import('<p>Files (137)</p><p>slice001.dcm</p>'
                                 '<button aria-label="Import Radiology Files" onclick="startImport()"></button>')
        self.assertEqual(clicks, 1)

    def test_single_nifti_file(self):
        clicks = self.run_import('<p>Files (1)</p><p>scan.nii.gz</p>'
                                 '<button aria-label="Import Radiology Files" onclick="startImport()"></button>')
        self.assertEqual(clicks, 1)

    def test_already_processing_does_not_submit_again(self):
        clicks = self.run_import('<p>Files (137)</p><p>Uploading and processing files...</p>'
                                 '<button aria-label="Import Radiology Files" onclick="startImport()"></button>',
                                 automatic=True)
        self.assertEqual(clicks, 0)


if __name__ == '__main__':
    unittest.main()
