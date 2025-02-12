# Some code has been borrowed from https://github.com/jsoma/selenium-github-actions
# Under the MIT License.

# Standard libraries
import atexit
import json
import os
import time
from tempfile import TemporaryDirectory
from time import sleep
from typing import List
from urllib.parse import urljoin

# Third-party libraries
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

TIMEOUT_SECONDS = 10


class RodanConnection:
    """RodanConnection allows one to programmatically interact with the Rodan website.
    It has functions that interact with the Rodan API and those that
    directly interact with the page.
    """

    def __init__(self, url, username, password, protocol="https"):
        self.url = f"{protocol}://{url}"
        self.username = username
        self.password = password
        self.downloads_dir = TemporaryDirectory()
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, TIMEOUT_SECONDS)
        atexit.register(self.cleanup)

    def cleanup(self):
        """Cleanup any filesystem resources that were allocated."""
        self.downloads_dir.cleanup()

    def setup_driver(self):
        """Set up the Chrome webdriver.
        These options make the driver headless (no GUI) so that it can be
        run on GitHub Actions. We also specify a custom downloads directory.
        """
        prefs = {
            "profile.default_content_settings.popups": 0,
            "download.default_directory": self.downloads_dir.name,
        }
        options = [
            "--headless",
            "--disable-gpu",
            "--window-size=1920,1200",
            "--ignore-certificate-errors",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
        chrome_options = Options()
        for option in options:
            chrome_options.add_argument(option)
        chrome_options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        return driver

    def double_click(self, element: WebElement):
        """Double click on a WebElement."""
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.double_click()
        actions.perform()

    def navigate_home(self):
        """Get the Rodan homepage."""
        self.driver.get(self.url)

    def login_to_rodan(self):
        """Login to Rodan and wait for the login cookie to be set."""
        username_field = self.find_visible(By.ID, "text-login_username")
        password_field = self.find_visible(By.ID, "text-login_password")
        login_button = self.find_visible(By.ID, "button-login")

        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        login_button.click()

        # Wait for the login cookie to be present.
        while not self.driver.get_cookies():
            sleep(1)

    def delete_all_resources(self, resource_type: str):
        """Delete all resources of a particular type."""
        resource_url = urljoin(self.url, f"api/{resource_type}/?format=json")
        resource_json = requests.get(resource_url, auth=(self.username, self.password))
        if not resource_json.ok:
            raise Exception(
                f"Couldn't load {resource_url}: received HTTP {resource_json.status_code}."
            )
        resources = json.loads(resource_json.text)
        for resource in resources["results"]:
            requests.delete(resource["url"], auth=(self.username, self.password))

    def get_rodan_build_hash(self) -> str:
        """Retrieve the hash of the commit from which rodan-main was built."""
        api_url = urljoin(self.url, "api?format=json")
        api_request = requests.get(api_url, auth=(self.username, self.password))
        if not api_request.ok:
            raise Exception(
                f"Couldn't load {api_url}: received HTTP {api_request.status_code}."
            )
        api_json = json.loads(api_request.text)
        return api_json["build_hash"]

    def find_visible(self, by: By, arg):
        """Find an element on the page that is both visible and clickable."""
        element = self.wait.until(EC.visibility_of_element_located((by, arg)))
        self.wait.until(EC.element_to_be_clickable(element))
        return element

    def find_visibles(self, by: By, arg):
        """Find all matching elements on the page that are visible."""
        return self.wait.until(EC.visibility_of_all_elements_located((by, arg)))

    def get_most_recent_from_table(
        self, item_type: str, timeout_secs=TIMEOUT_SECONDS
    ) -> WebElement:
        """Find the most recent item from a Rodan table.
        Raises an exception if the table doesn't have any elements before TIMEOUT_SECONDS.
        """
        now_time = start_time = time.monotonic()
        items = None
        while not items:
            items = self.find_visibles(
                By.XPATH, f'//*[@id="table-{item_type}"]/tbody/tr'
            )
            now_time = time.monotonic()
            if now_time - start_time > timeout_secs:
                break
        if not items:
            raise Exception(
                f"Couldn't get item from {item_type} table before timeout of {timeout_secs} seconds was reached!"
            )
        # td[3] corresponds to the "Created" field in the table.
        items = sorted(
            items, reverse=True, key=lambda p: str(p.find_element(By.XPATH, "td[3]"))
        )
        most_recent = items[0]
        self.wait.until(EC.element_to_be_clickable(most_recent))
        return most_recent

    def create_project(self):
        """Create a new project."""
        new_project_button = self.find_visible(By.ID, "button-new_project")
        new_project_button.click()

    def create_workflow(self, project: WebElement) -> WebElement:
        """Create a new workflow and return the WebElement that represents it in the Workflows table."""
        self.double_click(project)
        self.find_visible(By.ID, "workflow_count").click()
        self.find_visible(By.ID, "button-new_workflow").click()
        return self.get_most_recent_from_table("workflows")

    def wait_for_text_present(
        self, element: WebElement, text: str, timeout_secs=TIMEOUT_SECONDS
    ):
        """Wait for an element to contain certain text.
        Raises an exception if TIMEOUT_SECONDS is reached.
        """
        now_time = start_time = time.monotonic()
        while now_time - start_time < timeout_secs:
            if text in element.text:
                return
            sleep(1)
        raise Exception(f"Timed out waiting for {text} to be present in {element}!")

    def build_hello_world_workflow(self, workflow) -> str:
        """Build and run an entire "hello world" workflow.
        Returns the text from the file created by running this workflow.
        """
        # Enter the workflow editor.
        self.double_click(workflow)
        # Click the "Workflow" dropdown menu.
        workflow_dropdown = self.find_visible(
            By.XPATH, '//*[@id="region-main"]//*[contains(text(), "Workflow")]'
        )
        workflow_dropdown.click()
        # Click "Add Job".
        add_job_button = self.find_visible(By.ID, "button-add_job")
        add_job_button.click()
        # Click "Add Search Filter".
        filter_button = self.find_visible(By.ID, "filter-menu")
        filter_button.click()
        # Click "Name".
        name_button = self.find_visible(
            By.XPATH, '//*[@id="filter-menu"]//*[@data-id="filter_name"]'
        )
        name_button.click()
        # Type "hello" into the search field.
        name_filter = self.find_visible(By.ID, "name__icontains")
        name_filter.send_keys("hello")
        # Double click the "Hello World - Python3" job.
        hello_job_row = self.find_visible(
            By.XPATH, '//*[@id="table-jobs"]//td[text()="Hello World - Python3"]'
        )
        self.double_click(hello_job_row)
        # Close the "Jobs" modal.
        close_button = self.find_visible(
            By.XPATH, '//*[@id="modal-generic"]//button[@class="close"]'
        )
        close_button.click()
        # Wait for workflow to be validated before running it.
        sleep(5)
        # Run the workflow, which takes us to the Workflow Runs page.
        workflow_dropdown.click()
        run_job_button = self.find_visible(By.ID, "button-run")
        run_job_button.click()
        # Double click the workflow run we just created.
        workflow_run = self.get_most_recent_from_table("workflowruns")
        self.wait_for_text_present(workflow_run, "Finished")
        self.double_click(workflow_run)
        # For some reason we need this sleep before we click Resources.
        sleep(1)
        # Click "Resources".
        resources_button = self.find_visible(By.ID, "button-resources_show")
        resources_button.click()
        # Double click the resource created by the workflow run.
        # This downloads the resource.
        resource_row = self.get_most_recent_from_table("resources")
        self.double_click(resource_row)
        # Wait for download to complete.
        sleep(5)
        # Return the text of the downloaded resource.
        with open(
            os.path.join(
                self.downloads_dir.name,
                "Hello World - Python3 - Text output.txt",
            ),
            "r",
        ) as f:
            hello_world_output = f.read()
            return hello_world_output
