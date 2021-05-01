#!/usr/bin/env python
from datetime import datetime
import getopt
import urllib.request, urllib.parse, urllib.error
import sys

import requests
from functools import reduce


def _parse_github_datetime(datetime_string):
    try:
        return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    except TypeError:
        pass


def usage():
    print("python repo-pr-stats.py <owner> <repo>")


def main(argv):
    owner = argv[0]
    repo = argv[1]

    params = {"state": "closed", "per_page": 100}

    all_pulls_url = "{}?{}".format(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        urllib.parse.urlencode(params),
    )
    resp = requests.get(all_pulls_url)

    all_pulls = resp.json()
    review_times = []
    for pull in all_pulls:
        if pull["merged_at"] is not None:
            created_at = _parse_github_datetime(pull["created_at"])
            merged_at = _parse_github_datetime(pull["merged_at"])
            review_time = merged_at - created_at
            print("Pull {} review took {} to merge".format(pull["id"], review_time))
            review_times.append(review_time)

    print("Total Average Review Time (%s pulls): " % len(review_times))
    print(reduce(lambda x, y: x + y, review_times) / len(review_times))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
    else:
        main(sys.argv[1:])
