#!/usr/bin/env python3
from __future__ import print_function
import json
import os
import re
import time
from github_selenium import GitHub2FA, WebDriverException

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


if __name__ == "__main__":
    # if all goes well, we quit. If not user is dropped into pdb while
    # browser is still alive for introspection
    # TODO put behind --debug option
    print("Obtain current LFS billing info")
    print("Attempting login as '{}', please enter OTP when asked".format(GH_LOGIN))
    print("  (if wrong, set GH_LOGIN & GH_PASSWORD in environtment properly)")
    quit = True
    try:
        # hack to allow script reload in iPython without destroyind
        # exisiting instance
        driver
    except NameError:
        driver = None
    if not driver:
        try:
            token = input("token please: ")
            driver = LFS_Usage()
            driver.login(GH_LOGIN, GH_PASSWORD, URL, 'Billing', token)
            results = driver.get_usage()
            results['time'] = time.strftime('%Y-%m-%d %H:%M')
            print(json.dumps(results))
        except WebDriverException:
            quit = False
            print("Deep error - did browser crash?")
        except ValueError as e:
            quit = False
            print("Navigation issue: {}".format(e.args[0]))

        if quit:
            driver.quit()
        else:
            import pdb; pdb.set_trace()
