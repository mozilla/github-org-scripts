#!/usr/bin/env python
'''
    Extract current LFS stats from GitHub web UI
'''
from __future__ import print_function
import json
import os
import re
import time
from github_selenium import GitHub2FA, WebDriverException
import argparse
import logging

_epilog = '''
Requires both firefox and geckodriver to be in the path, and compatible.
'''


logger = logging.getLogger(__name__)

URL = "https://github.com/organizations/mozilla/settings/billing"
GH_LOGIN = os.getenv('GH_LOGIN', "org_owner_login")
GH_PASSWORD = os.getenv('GH_PASSWORD', 'password')




class LFS_Usage(GitHub2FA):
    # no init needed

    def get_values(self, selector):
        # get the "line" and parse it
        e = self.get_element(selector)
        if e:
            text = e.text
            match = re.match(r'''\D+(?P<used>\S+)\D+(?P<purchased>\S+)''', text)
            if match:
                d = match.groupdict()
                used = float(d['used'].replace(',', ''))
                purchased = float(d['purchased'].replace(',', ''))
        else:
            print("no element for '{}'".format(selector))
            used = purchased = None
        return used, purchased


    def get_usage(self):
        r = {}
        r['bw_used'], r['bw_purchased'] = self.get_values('div.mt-2:nth-child(4)')
        r['sp_used'], r['sp_purchased'] = self.get_values('div.mt-2:nth-child(5)')
        return r


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument('--debug', action='store_true',
                        help='Drop into debugger on error')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                        help='Make the browser window visible')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    print("Obtain current LFS billing info")
    print("Attempting login as '{}', please enter OTP when asked".format(GH_LOGIN))
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
            token = input("token please: ")
            driver = LFS_Usage(headless=args.headless, options=opts)
            driver.login(GH_LOGIN, GH_PASSWORD, URL, 'Billing', token)
            results = driver.get_usage()
            results['time'] = time.strftime('%Y-%m-%d %H:%M')
            print(json.dumps(results))
        except WebDriverException:
            quit = not args.debug
            print("Deep error - did browser crash?")
        except ValueError as e:
            quit = not args.debug
            print("Navigation issue: {}".format(e.args[0]))

        if quit:
            driver.quit()
        else:
            import pdb; pdb.set_trace()

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
