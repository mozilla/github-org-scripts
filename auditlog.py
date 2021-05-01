#!/usr/bin/env python

import ast
import json
import os
import re
import sys
import time
from github_selenium import GitHub2FA, WebDriverException, webdriver

ORG = os.getenv("ORG", "mozilla")
URL = f"https://github.com/organizations/{ORG}/settings/audit-log"
URL_TITLE = "Audit log"
GH_LOGIN = os.getenv("GH_LOGIN", "org_owner_login")
GH_PASSWORD = os.getenv("GH_PASSWORD", "password")
HEADLESS = bool(os.getenv("HEADLESS", "YES"))

# hack for legacy python support of token input (tokens often look like bad
# octal numbers and raise a syntax error)
if sys.version_info.major == 2:
    input = raw_input  # noqa: E0602


class Audit_Log_Download(GitHub2FA):
    # no init needed
    def __init__(self, *args, **kwargs):
        # we have to create the profile before calling our superclass
        fp = self._buildProfile()
        kwargs["firefox_profile"] = fp
        super().__init__(*args, **kwargs)

    def _buildProfile(self):
        fx_profile = webdriver.FirefoxProfile()
        fx_profile.set_preference("browser.download.folderList", 2)
        fx_profile.set_preference("browser.download.manager.showWhenStarting", False)
        fx_profile.set_preference(
            "browser.download.dir", "/home/hwine/Downloads/geckodriver"
        )
        fx_profile.set_preference("browser.download.panel.shown", True)
        fx_profile.set_preference(
            "browser.helperApps.neverAsk.saveToDisk", "application/json"
        )
        return fx_profile

    def get_values(self, selector):
        # get the "line" and parse it
        e = self.get_element(selector)
        if e:
            text = e.text
            match = re.match(r"""\D+(?P<used>\S+)\D+(?P<purchased>\S+)""", text)
            if match:
                d = match.groupdict()
                used = float(d["used"].replace(",", ""))
                purchased = float(d["purchased"].replace(",", ""))
        else:
            print(f"no element for '{selector}'")
            used = purchased = None
        return used, purchased

    def download_file(self):
        form_selector = "div.select-menu-item:nth-child(1) > form:nth-child(1)"
        # Simplest approach (??) is to build URL from form ourselves, and
        # download. Avoids the system dialogs
        form = self.get_element(form_selector)
        results = {}
        data = {}
        allInputs = form.find_elements_by_xpath(".//INPUT")
        for web_element in [x for x in allInputs if x.tag_name == "input"]:
            name = web_element.get_attribute("name")
            value = web_element.get_attribute("value")
            data[name] = value
        # build url
        file_url = form.get_attribute("action")
        results["action_url"] = file_url
        results["body_data"] = data

        # make call & write to file
        # Have to get there by clicking -- can't click directly as it's not
        # visible.
        self.get_element(".btn-sm").click()  # The big export button
        self.get_element(
            "div.select-menu-item:nth-child(1) >"
            " form:nth-child(1)"
            " > button:nth-child(5)"
        ).click()  # The JSON option
        # the clicks return faster than the download can happen, and the
        # filename isn't deterministic. Try the easy way and wait 60 seconds.
        # The "Export" button dims, but only while compiling the file, not
        # during download.
        time.sleep(60)
        return results


if __name__ == "__main__":
    # if all goes well, we quit. If not user is dropped into pdb while
    # browser is still alive for introspection
    # TODO put behind --debug option
    print(f"Download latest audit log for organization {ORG}")
    print(f"Attempting login as '{GH_LOGIN}', please enter OTP when asked")
    print("  (if wrong, set GH_LOGIN & GH_PASSWORD in environtment properly)")
    quit = True
    try:
        # hack to allow script reload in iPython without destroying
        # exisiting instance
        driver
    except NameError:
        driver = None
    if not driver:
        try:
            token = ast.literal_eval(input("token please: "))
            driver = Audit_Log_Download(headless=HEADLESS)
            driver.login(GH_LOGIN, GH_PASSWORD, URL, URL_TITLE, token)
            results = driver.download_file()
            results["time"] = time.strftime("%Y-%m-%d %H:%M")
            print(json.dumps(results))
            print("File downloaded successfully - check your download" " directory")
            print("Any exception after this does not affect audit log")
            print("But may leave your browser running")
        except WebDriverException:
            quit = False
            print("Deep error - did browser crash?")
        except ValueError as e:
            quit = False
            print(f"Navigation issue: {e.args[0]}")

        if quit:
            # logout first
            driver.get_element("details.pl-2").click()
            driver.get_element(".logout-form").click()
            driver.wait_for_page("The world's leading")
            driver.quit()
        else:
            import pudb

            pudb.set_trace()  # noqa: E702
