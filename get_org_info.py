#!/usr/bin/env python
"""
    Report Basic info about orgs
"""
from __future__ import print_function

# additional help text
_epilog = """
This script outputs some information about organizations, mostly immutable
identifiers and contact info.
"""
# hwine believes keeping the doc above together is more important than PEP-8
import argparse  # NOQA
import logging  # NOQA

from client import get_github3_client  # NOQA

logger = logging.getLogger(__name__)
DEBUG = False


def get_info(gh, org):
    try:
        org = gh.organization(org)
        orgd = org.as_dict()
        print("{:>15}: {!s}".format("Name", org.name))
        print("{:>15}: {!s}".format("API v3 id", org.id))
        print("{:>15}: {!s}".format("API v4 id", orgd['type'] + str(org.id)))
        print("{:>15}: {!s}".format("contact", org.email))
        print("{:>15}: {!s}".format("billing", orgd['billing_email']))
        print("{:>15}: {!s}".format("private repos",
                                    orgd['owned_private_repos']))
        print("{:>15}: {!s}".format("plan", orgd['plan']['name']))
        print("{:>15}: {!s}".format("seats", orgd['plan']['filled_seats']))
    except Exception:
        logger.error("Error obtaining data for org '%s'", str(org))
    finally:
        if DEBUG:
            from pprint import pprint
            pprint(orgd)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument("--debug", action='store_true',
                        help="include dump of all data returned")
    parser.add_argument("orgs", nargs='*', default=['mozilla', ],
                        help='github organizations to check (defaults to '
                             'mozilla)')
    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = args.debug
    return args


def main():
    args = parse_args()
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            if len(args.orgs) > 1:
                print("Processing org {}".format(org))
            get_info(gh, org)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
