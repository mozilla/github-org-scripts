#!/usr/bin/env python
import sys

from client import get_github3_client
from github3.exceptions import UnprocessableResponseBody, NotFoundError


def get_files(repo, directory):
    """Get the files from this repo.

    The interface on this for github3.py version 1.0.0a4 is not yet
    stable, so some coding-by-coincidence is used.
    """
    names = None
    try:
        response = repo.file_contents(directory)
    except UnprocessableResponseBody as e:
        response = e
        pass
    except NotFoundError:
        print(f"\nNo data for {repo.full_name}! (maybe empty)")
        return names
    if isinstance(response, UnprocessableResponseBody):
        # response.body contains json of the directory contents as a list of
        # dictionaries. The calling code wants a dictionary with file
        # names as keys.
        names = {x["name"]: None for x in response.body}
    else:
        raise Exception("github3.py behavior changed")
    return names


if __name__ == "__main__":
    gh = get_github3_client()

    # Divvy up into repositories that need/do not need a CONTRIBUTING file.
    good_repos = []
    bad_repos = []

    repos = gh.organization("mozilla-services").repositories(type="sources")
    for repo in repos:
        # All files in this repo's default branch.
        # {'filename.md': Content(), 'filename2.txt': Contents(), ...}
        files = get_files(repo, "/")

        if files:
            contrib_files = [
                f for f in list(files.keys()) if f.startswith("CONTRIBUTING")
            ]
        else:
            contrib_files = None

        if contrib_files:
            good_repos.append(repo.name)
        else:
            bad_repos.append(repo.name)

        sys.stderr.write(".")

    good_repos.sort()
    print()
    print("The following repos HAVE a CONTRIBUTING file:")
    for r in good_repos:
        print(r)

    bad_repos.sort()
    print()
    print()
    print("The following repos DO NOT HAVE a CONTRIBUTING file:")
    for r in bad_repos:
        print(r)
