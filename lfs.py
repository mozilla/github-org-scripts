#!/usr/bin/env python
"""Extract current LFS stats from GitHub web UI."""

import ast
import json
import os
import re
import time
from github_selenium import GitHub2FA, WebDriverException
import argparse
import logging

_epilog = """
Requires both firefox and geckodriver to be in the path, and compatible.
"""


logger = logging.getLogger(__name__)

URL = "https://github.com/organizations/mozilla/settings/billing"
GH_LOGIN = os.getenv("GH_LOGIN", None)
GH_PASSWORD = os.getenv("GH_PASSWORD", None)


class LFS_Usage(GitHub2FA):
    # no init needed

    def get_values(self, selector):
        # get the "line" and parse it
        e = self.get_element(selector)
        if e:
            text = e.text
            # line format: 13,929.6 GB of 17,400 GB (29 data packs)
            match = re.match(r"""\D*(?P<used>\S+)\D+(?P<purchased>\S+)""", text)
            if match:
                d = match.groupdict()
                used = float(d["used"].replace(",", ""))
                purchased = float(d["purchased"].replace(",", ""))
            else:
                print(f"no match for '{selector}'")
                print(f"    for text '{text}'")
                used = purchased = None
        else:
            print(f"no element for '{selector}'")
            used = purchased = None
        return used, purchased

    def get_usage(self):
        r = {}

        r["sp_used"], r["sp_purchased"] = self.get_values(
            "div.Box-row:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2)"
        )

        r["bw_used"], r["bw_purchased"] = self.get_values(
            "div.Box-row:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2)"
        )
        return r


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument(
        "--debug", action="store_true", help="Drop into debugger on error"
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Make the browser window visible",
    )
    args = parser.parse_args()
    # check for env vars
    if not (GH_LOGIN and GH_PASSWORD):
        parser.error("You must set environment variables GH_LOGIN & GH_PASSWORD")
    return args


def main():
    args = parse_args()
    print("Obtain current LFS billing info")
    print(f"Attempting login as '{GH_LOGIN}', please enter OTP when asked")
    print("  (if wrong, set GH_LOGIN & GH_PASSWORD in environtment properly)")
    quit = not args.debug
    try:
        # hack to allow script reload in iPython without destroying
        # exisiting instance
        driver
    except NameError:
        driver = None
    if not driver:
        from selenium.webdriver.firefox.options import Options

        opts = Options()
        opts.log.level = "trace"
        try:
            token = ast.literal_eval(input("token please: "))
            driver = LFS_Usage(headless=args.headless, options=opts)
            driver.login(GH_LOGIN, GH_PASSWORD, URL, "Billing", token)
            results = driver.get_usage()
            results["time"] = time.strftime("%Y-%m-%d %H:%M")
            print(json.dumps(results))
        except WebDriverException:
            quit = not args.debug
            print("Deep error - did browser crash?")
        except ValueError as e:
            quit = not args.debug
            print(f"Navigation issue: {e.args[0]}")

        if quit:
            driver.quit()
        else:
            import pdb

            pdb.set_trace()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    main()
