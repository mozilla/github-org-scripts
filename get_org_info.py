#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Report Basic info about orgs."""

# additional help text
_epilog = """
This script outputs some information about organizations, mostly immutable
identifiers and contact info.

Current owner list is available via the '--owners' option.
"""
# hwine believes keeping the doc above together is more important than PEP-8
import argparse  # NOQA
import base64
import logging  # NOQA
import json
from collections import defaultdict  # NOQA

import argcomplete
import github3  # NOQA
from client import get_github3_client  # NOQA

logger = logging.getLogger(__name__)
DEBUG = False


def jsonl_out(d):
    print(json.dumps(d))


def show_info(gh, org_name, show_owners=False, show_emails=False, show_json=False):
    def miss():
        return "<hidden>"

    try:
        org = gh.organization(org_name)
        orgd = defaultdict(miss, org.as_dict())
        if show_json:
            jsonl_out(orgd)
            return
        v4decoded = "{:03}:{}{}".format(len(orgd["type"]), orgd["type"], str(org.id))
        v4encoded = base64.b64encode(bytes(v4decoded, "utf-8"))
        print("{:>15}: {!s} ({})".format("Name", org.name or org_name, orgd["login"]))
        print("{:>15}: {!s}".format("API v3 id", org.id))
        print("{:>15}: {!s}".format("API v4 id", f"{v4encoded} ({v4decoded})"))
        print("{:>15}: {!s}".format("contact", org.email))
        print("{:>15}: {!s}".format("billing", orgd["billing_email"]))
        print(
            "{:>15}: {!s}".format(
                "2FA required", orgd["two_factor_requirement_enabled"]
            )
        )
        print("{:>15}: {!s}".format("private repos", orgd["owned_private_repos"]))
        # Nested dictionaries need special handling
        plan = orgd["plan"]
        if not isinstance(plan, dict):
            plan = defaultdict(miss)
        print("{:>15}: {!s}".format("plan", plan["name"]))
        print("{:>15}: {!s}".format("seats", plan["filled_seats"]))
        if show_owners:
            print("{:>15}:".format("Org Owners"))
            for owner in org.members(role="admin"):
                owner.refresh()  # get name
                name = owner.name or "<hidden>"
                if show_emails:
                    email = " " + (owner.email or "<email hidden>")
                else:
                    email = ""
                print(f"                  {name} ({owner.login}{email})")
    except Exception as e:
        logger.error("Error %s obtaining data for org '%s'", str(e), str(org))
    finally:
        if DEBUG:
            from pprint import pprint

            pprint(orgd)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument(
        "--debug", action="store_true", help="include dump of all data returned"
    )
    parser.add_argument("--owners", action="store_true", help="Also show owners")
    parser.add_argument("--email", action="store_true", help="include owner email")
    parser.add_argument("--json", action="store_true", help="output as json lines")
    parser.add_argument(
        "--all-my-orgs",
        action="store_true",
        help="act on all orgs for which you're an owner",
    )
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="Only output your org names for which you're an owner",
    )
    parser.add_argument(
        "orgs",
        nargs="*",
        help="github organizations to check (defaults to " "mozilla)",
        default=["mozilla"],
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.names_only:
        args.all_my_orgs = True
        if args.owners or args.email:
            parser.error("Can't specify owners or emails with --all-my-orgs")
    if args.all_my_orgs and len(args.orgs):
        parser.error("Can't specify orgs with --all-my-orgs")
    if args.email and not args.owners:
        # implies owners
        args.owners = True
    if args.debug:
        global DEBUG
        DEBUG = args.debug
    return args


# api.github.com/user/orgs endpoint not natively supported
# belongs in authenticated user
class MyOrganizationsIterator(github3.structs.GitHubIterator):
    def __init__(self, me):
        super().__init__(
            count=-1,  # get all
            url=me.session.base_url + "/user/orgs",
            cls=github3.orgs.Organization,
            session=me.session,
        )


def print_limits(e=None, verbose=False):
    if e:
        #         display("API limit reached, try again in 5 minutes.\\n")
        display(str(e))

    reset_max = reset_min = 0
    limits = gh.rate_limit()
    resources = limits["resources"]
    #     print("{:3d} keys: ".format(len(resources.keys())), resources.keys())
    #     print(resources)
    for reset in resources.keys():
        reset_at = resources[reset]["reset"]
        reset_max = max(reset_at, reset_max)
        if not resources[reset]["remaining"]:
            reset_min = min(reset_at, reset_min if reset_min else reset_at)
            if verbose:
                print("EXPIRED for {} {}".format(reset, resources[reset]["remaining"]))
        else:
            if verbose:
                print(
                    "remaining for {} {}".format(reset, resources[reset]["remaining"])
                )

    if not reset_min:
        print("No limits reached currently.")
    else:
        print(
            "Minimum reset at {} UTC ({})".format(
                time.asctime(time.gmtime(reset_min)),
                time.asctime(time.localtime(reset_min)),
            )
        )
    print(
        "All reset at {} UTC".format(
            time.asctime(time.gmtime(reset_max)),
            time.asctime(time.localtime(reset_max)),
        )
    )


def main():
    args = parse_args()
    if args.orgs or args.all_my_orgs:
        gh = get_github3_client()
        try:
            if args.all_my_orgs:
                authorized_user = gh.me()
                me = gh.user(authorized_user.login)
                my_orgs = MyOrganizationsIterator(me)
                for org in my_orgs:
                    owner_logins = [u.login for u in org.members(role="admin")]
                    if me.login in owner_logins:
                        args.orgs.append(org.login)
                if args.names_only:
                    print("\n".join(sorted(args.orgs)))
                    return

            newline = ""
            for org in args.orgs:
                if len(args.orgs) > 1 and not args.json:
                    print(f"{newline}Processing org {org}")
                    newline = "\n"
                show_info(gh, org, args.owners, args.email, args.json)
        except github3.exceptions.ForbiddenError as e:
            print_limits(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    main()
