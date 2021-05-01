__doc__ = """Searches for code across multiple github orgs."""

import argparse
import jsonstreams
import sys

from client import (
    get_github3_client,
    sleep_if_rate_limited,
)


DEFAULT_ORGS = [
    'mozilla',
    'mozilla-conduit',
    'mozilla-platform-ops',
    'mozilla-releng',
    'mozilla-services',
    'taskcluster',
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("query", type=str,
                        help='code search query. syntax at https://help.github.com/articles/searching-code/')
    parser.add_argument("--orgs", default=DEFAULT_ORGS, nargs='*',
                        help=f'organizations to search (defaults to {DEFAULT_ORGS})')
    parser.add_argument("--json",
                        help='path to output json results', type=str, default=None)
    parser.add_argument("--verbose", action='store_true',
                        help='print logins for all changes')

    return parser.parse_args()


def main():
    args = parse_args()
    gh = get_github3_client()

    json_fout = jsonstreams.Stream(jsonstreams.Type.array, args.json, indent=4) if args.json else None

    for org in args.orgs:
        full_query = f'org:{org} {args.query}'

        if args.verbose:
            print(f'searching with query {full_query}')

        sleep_if_rate_limited(gh, verbose=args.verbose)

        print("{:<16}{:<32}{:<64}".format('org', 'repo', 'file path'))
        for result in gh.search_code(full_query):
            print("{0:<16}{1.repository.name:<32}{1.path:<64}".format(org, result))

            if json_fout:
                json_fout.write(result.to_json())

    if json_fout:
        # must explicitly close -- that's what outputs the closing delimiter
        json_fout.close()


if __name__ == '__main__':
    main()
