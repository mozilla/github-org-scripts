# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# # User Search
# For use to:
# 1. Try to find an account based on random knowledge
# 2. List all orgs they belong to (from a subset)
#   - You will need org owner permissions to perform these searches
# %% [markdown] heading_collapsed=true
# # Boiler plate
# Skip/hide this. Common usage is below.
# %% [markdown] hidden=true
# If you see this text, you may want to enable the nbextension "Collapsable Headings", so you can hide this in common usage.
# %% [markdown] heading_collapsed=true hidden=true
# ## Tune as needed
#
# There are several lru_cache using functions. Many of them are called len(orgs_to_check) times. If they are under sized, run times will get quite long. (Only the first query should be delayed - after that, all data should be in the cache.)
#
# See the "cache reporting" cell below.
# %% [markdown] heading_collapsed=true hidden=true
# #### Orgs to check
# %% [markdown] hidden=true
# This should be replaced with a call for all orgs the creds has owner access for.

# %% init_cell=true hidden=true
# use the output of ./get_org_info.py --names-only for below
orgs_to_check = set(
    """
Common-Voice
Mozilla-Commons
Mozilla-Games
Mozilla-JetPack
Mozilla-TWQA
MozillaDataScience
MozillaDPX
MozillaFoundation
MozillaReality
MozillaSecurity
MozillaWiki
Pocket
Thunderbird-client
devtools-html
firefox-devtools
fxos
fxos-eng
iodide-project
mdn
moz-pkg-testing
mozilla
mozilla-applied-ml
mozilla-archive
mozilla-b2g
mozilla-bteam
mozilla-conduit
mozilla-extensions
mozilla-frontend-infra
mozilla-iam
mozilla-it
mozilla-l10n
mozilla-lockbox
mozilla-lockwise
mozilla-metrics
mozilla-mobile
mozilla-partners
mozilla-platform-ops
mozilla-private
mozilla-rally
mozilla-releng
mozilla-services
mozilla-spidermonkey
mozilla-standards
mozilla-svcops
mozilla-tw
mozmeao
nss-dev
projectfluent
taskcluster
""".split()
)

print(f"{len(orgs_to_check):3d} orgs to check.")

# %% [markdown] heading_collapsed=true hidden=true
# #### Cache Tuning & Clearing
#
# Various functions use lru_cache -- this outputs the values to see if they are tuned appropriately.
#
# Note that these have no meaning until after 1 or more queries have been run.

# %% hidden=true
print("_search_for_user")
print(_search_for_user.cache_info())
print("_search_for_org")
print(_search_for_org.cache_info())

print("get_collaborators")
print(get_collaborators.cache_info())
print("get_members")
print(get_members.cache_info())

print("get_org_owners")
print(get_org_owners.cache_info())
print("get_inspectable_org_object")
print(get_inspectable_org_object.cache_info())


# %% hidden=true
print("clearing caches...")
_search_for_user.cache_clear()
_search_for_org.cache_clear()
get_collaborators.cache_clear()
get_members.cache_clear()
get_org_owners.cache_clear()
get_inspectable_org_object.cache_clear()

# %% [markdown] heading_collapsed=true hidden=true
# ## Code
# %% [markdown] heading_collapsed=true hidden=true
# ### main code (CIS/IAM)
# %% [markdown] hidden=true
# Not every operator will have a valid token for the CIS system, so fail gently if not

# %% init_cell=true hidden=true
def check_CIS(email):
    if _has_cis_access():
        login = _get_cis_info(email)
        display(f"CIS info for {email} reports '{login}'")
        return login
    else:
        display("Skipping CIS check, no token available.")


# %% init_cell=true hidden=true
def _has_cis_access():
    import os

    return os.environ.get("CIS_CLIENT_ID", "") and os.environ.get(
        "CIS_CLIENT_SECRET", ""
    )


# %% init_cell=true hidden=true
_cis_bearer_token = None
import requests


def _get_cis_bearer_token():
    global _cis_bearer_token
    if _cis_bearer_token:
        return _cis_bearer_token
    else:
        import requests

        url = "https://auth.mozilla.auth0.com/oauth/token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "client_id": os.environ["CIS_CLIENT_ID"],
            "client_secret": os.environ["CIS_CLIENT_SECRET"],
            "audience": "api.sso.mozilla.com",
            "grant_type": "client_credentials",
        }
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        _cis_bearer_token = data["access_token"]
        return _cis_bearer_token


def _get_cis_info(email):
    import urllib.request, urllib.parse, urllib.error

    bearer_token = _get_cis_bearer_token()
    # first get the v4 id
    url = (
        "https://person.api.sso.mozilla.com/v2/user/primary_email/{}?active=any".format(
            urllib.parse.quote(email)
        )
    )
    headers = {"Authorization": f"Bearer {bearer_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    login = v4id = None
    try:
        v4id = data["identities"]["github_id_v4"]["value"]
    except KeyError:
        pass
    if v4id:
        # if there was a v4 id, map it to a login, via graphQL
        query = """
            query id_lookup($id_to_check: ID!) {
              node(id: $id_to_check) {
                ... on User {
                  login
                  id
                  databaseId
                }
              }
            }
            """
        variables = '{ "id_to_check": "' + str(v4id) + '" }'
        url = "https://api.github.com/graphql"
        headers = {"Authorization": f"Token {api_key}"}
        payload = {
            "query": query,
            "variables": variables,
        }
        resp = requests.post(url, headers=headers, json=payload)
        try:
            data = resp.json()
            login = data["data"]["node"]["login"]
        except KeyError:
            login = None
    return login


# %% [markdown] heading_collapsed=true hidden=true
# ### main code (GitHub)
# %% [markdown] heading_collapsed=true hidden=true
# #### helpers

# %% init_cell=true hidden=true
# print some debug information
import github3

print(github3.__version__)
print(github3.__file__)


# %% init_cell=true hidden=true
# set values here - you can also override below

# get api key from environment, fall back to file
import os

api_key = os.environ.get("GITHUB_PAT", "")
if not api_key:
    api_key = open(".credentials").readlines()[1].strip()
if not api_key:
    raise OSError("no GitHub PAT found")


# %% init_cell=true hidden=true
import time


# %% init_cell=true hidden=true


def print_limits(e=None, verbose=False):
    if e:
        #         display("API limit reached, try again in 5 minutes.\n")
        display(str(e))

    reset_max = reset_min = 0
    limits = gh.rate_limit()
    resources = limits["resources"]
    #     print("{:3d} keys: ".format(len(resources.keys())), resources.keys())
    #     print(resources)
    for reset in list(resources.keys()):
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


try:
    gh = github3.login(token=api_key)
    print(f"You are authenticated as {gh.me().login}")
except (github3.exceptions.ForbiddenError, github3.exceptions.ConnectionError) as e:
    print(str(e))
    print_limits()
try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

print_limits()

# %% [markdown] hidden=true
# From here on, use ``gh`` to access all data

# %% init_cell=true hidden=true
@lru_cache(maxsize=128)
def _search_for_user(user):
    l = list(gh.search_users(query="type:user " + user))
    display(f"found {len(l)} potentials for {user}")
    return l


@lru_cache(maxsize=512)
def _search_for_org(user):
    l = list(gh.search_users(query="type:org " + user))
    display(f"found {len(l)} potentials for {user}")
    return l


def get_user_counts(user):
    # display(u"SEARCH '{}'".format(user))
    l = _search_for_user(user)
    yield from l


# %% init_cell=true hidden=true
displayed_users = set()  # cache to avoid duplicate output


def show_users(user_list, search_term):
    global displayed_users
    unique_users = set(user_list)
    count = len(unique_users)
    if count > 10:
        # Even if there are too many, we still want to check the 'root' term, if it matched
        try:
            seed_user = gh.user(search_term.encode("ascii", "replace"))
            display(
                "... too many to be useful, still trying '{}' ...".format(
                    seed_user.login
                )
            )
            displayed_users.add(seed_user)
        #             print("search_term {}; seed_user {}; seed_user.login {}".format(search_term, seed_user, seed_user.login))
        except github3.exceptions.NotFoundError:
            display(f"... too many to be useful, '{search_term}' is not a user")
    else:
        for u in [x for x in unique_users if not x in displayed_users]:
            displayed_users.add(u)
            user = u.user.refresh()
    if 0 < count <= 10:
        return [u.login for u in unique_users]
    else:
        return []


from itertools import permutations


def _permute_seeds(seeds):
    if len(seeds) == 1:
        yield seeds[0]
    else:
        for x, y in permutations(seeds, 2):
            permutation = " ".join([x, y])
            display(f"   trying phrase permutation {permutation}")
            yield permutation
            permutation = "".join([x, y])
            display(f"   trying permutation {permutation}")
            yield permutation


def gather_possibles(seeds):
    found = set()
    # sometimes get a phrase coming in - e.g. "First Last"
    for seed in _permute_seeds(seeds.split()):
        maybes = show_users(get_user_counts(seed), seed)
        found.update(maybes)
        # if it was an email addr, try again with the mailbox name
        if "@" in seed:
            seed2 = seed.split("@")[0]
            display(f"Searching for mailbox name '{seed2}' (gather_possibles)")
            maybes = show_users(get_user_counts(seed2), seed2)
            found.update(maybes)
    return found


# %% init_cell=true hidden=true
class OutsideCollaboratorIterator(github3.structs.GitHubIterator):
    def __init__(self, org):
        super().__init__(
            count=-1,  # get all
            url=org.url + "/outside_collaborators",
            cls=github3.users.ShortUser,
            session=org.session,
        )


@lru_cache(maxsize=512)
def get_collaborators(org):
    collabs = [x.login.lower() for x in OutsideCollaboratorIterator(org)]
    return collabs


def is_collaborator(org, login):
    return bool(login.lower() in get_collaborators(org))


# provide same interface for members -- but the iterator is free :D
@lru_cache(maxsize=512)
def get_members(org):
    collabs = [x.login.lower() for x in org.members()]
    return collabs


def is_member(org, login):
    return bool(login.lower() in get_members(org))


# %% init_cell=true hidden=true
@lru_cache(maxsize=64)
def get_org_owners(org):
    owners = org.members(role="admin")
    logins = [x.login for x in owners]
    return logins


@lru_cache(maxsize=128)
def get_inspectable_org_object(org_name):
    try:
        o = gh.organization(org_name)
        # make sure we have enough chops to inspect it
        get_org_owners(o)
        is_member(o, "qzu" * 3)
        is_collaborator(o, "qzu" * 3)
    except github3.exceptions.NotFoundError:
        o = None
        display(f"No such organization: '{org_name}'")
    except github3.exceptions.ForbiddenError as e:
        o = None
        display(f"\n\nWARNING: Not enough permissions for org '{org_name}'\n\n")
    except Exception as e:
        o = None
        display("didn't expect to get here")
    return o


def check_login_perms(logins, headers=None, ldap=None):
    any_perms = []
    any_perms.append("=" * 30)
    if headers:
        any_perms.extend(headers)
    if not len(logins):
        any_perms.append("\nFound no valid usernames")
    else:
        any_perms.append(
            "\nChecking {} usernames for membership in {} orgs".format(
                len(logins), len(orgs_to_check)
            )
        )
        for login in logins:
            start_msg_count = len(any_perms)
            for org in orgs_to_check:
                o = get_inspectable_org_object(org)
                if o is None:
                    continue
                if is_member(o, login):
                    url = "https://github.com/orgs/{}/people?utf8=%E2%9C%93&query={}".format(
                        o.login, login
                    )
                    msg = f"FOUND! {o.login} has {login} as a member: {url}"
                    owner_logins = get_org_owners(o)
                    is_owner = login in owner_logins
                    if is_owner:
                        msg += f"\n  NOTE: {login} is an OWNER of {org}"
                    any_perms.append(msg)
                if is_collaborator(o, login):
                    url = "https://github.com/orgs/{}/outside-collaborators?utf8=%E2%9C%93&query={}".format(
                        o.login, login
                    )
                    any_perms.append(
                        "FOUND! {} has {} as a collaborator: {}".format(
                            o.login, login, url
                        )
                    )
            else:
                end_msg_count = len(any_perms)
                if end_msg_count > start_msg_count:
                    # some found, put a header on it, the add blank line
                    any_perms.insert(
                        start_msg_count,
                        "\nFound {:d} orgs for {}:".format(
                            end_msg_count - start_msg_count, login
                        ),
                    )
                    any_perms.append("")
                else:
                    any_perms.append(f"No permissions found for {login}")
    return any_perms


# %% init_cell=true hidden=true
def extract_addresses(text):
    """Get email addresses from text."""
    # ASSUME that text is a list of email addresses (possibly empty)
    if not text:
        return []
    #     print("before: %s" % text)
    text = text.replace("[", "").replace("]", "").replace("b'", "").replace("'", "")
    #     print("after: %s" % text)
    #     print(" split: %s" % text.split())
    return text.split()
    # raise ValueError("couldn't parse '{}'".format(text))


# %% [markdown] heading_collapsed=true hidden=true
# #### main driver

# %% init_cell=true hidden=true
def check_for_acls(logins, ldap=None):

    """Check for these items in code, could be an acl to be removed.

    Note that we haven't pruned logins to just the orgs we found hits on
    -- we're using all GitHub logins. May want to modify in the future.
    """
    possibles = set()
    possibles.update(logins)
    if ldap is not None:
        possibles.add(ldap)
    # import pdb ; pdb.set_trace()
    hits = ["\nChecking for possible ACLs\n"]
    for org in orgs_to_check:
        for l in possibles:
            try:
                hit_list = list(gh.search_code(query=f"org:{org} {l}"))
            except Exception as e:
                if e.code not in [403, 422]:
                    print(f"org={org} l={l} exception={str(e)}")
            num_repos = len(hit_list)
            if num_repos > 0:
                hits.append(
                    f"{num_repos} hits in https://github.com/search?q=org%3A{org}+{l}&type=code"
                )
    return hits


# %% init_cell=true hidden=true
import re
import os

re_flags = re.MULTILINE | re.IGNORECASE


def process_from_email(email_body):
    # get rid of white space
    email_body = os.linesep.join(
        [s.strip() for s in email_body.splitlines() if s.strip()]
    )
    if not email_body:
        return

    user = set()

    # Extract data from internal email format
    match = re.search(r"^Full Name: (?P<full_name>\S.*)$", email_body, re_flags)
    if match:
        # add base and some variations
        full_name = match.group("full_name")
        user.add(full_name)
        # remove spaces, forward & reversed
        user.add(full_name.replace(" ", ""))
        user.add("".join(full_name.split()[::-1]))
        # use hypens, forward & reversed
        user.add(full_name.replace(" ", "-"))
        user.add("-".join(full_name.split()[::-1]))

    match = re.search(r"^Email: (?P<primary_email>.*)$", email_body, re_flags)
    primary_email = match.group("primary_email") if match else None
    user.add(primary_email)
    default_login = primary_email.split("@")[0] if primary_email else None
    if default_login:
        # add some common variations that may get discarded for "too many" matches
        user.update(
            [
                f"moz{default_login}",
                f"moz-{default_login}",
                f"mozilla{default_login}",
                f"mozilla-{default_login}",
                f"{default_login}moz",
                f"{default_login}-moz",
            ]
        )

    # let user start manual work before we do all the GitHub calls
    display("Check these URLs for Heroku activity:")
    display(
        "  Heroku Access: https://people.mozilla.org/a/heroku-members/edit?section=members"
    )
    display(f"     copy/paste for ^^ query:  :{primary_email}:  ")
    display(
        "  People: https://people.mozilla.org/s?who=all&query={}".format(
            primary_email.replace("@", "%40")
        )
    )
    display(
        "  Heroku: https://dashboard.heroku.com/teams/mozillacorporation/access?filter={}".format(
            primary_email.replace("@", "%40")
        )
    )
    display(email_body)

    match = re.search(r"^Github Profile: (?P<github_profile>.*)$", email_body, re_flags)
    declared_github = match.group("github_profile") if match else None
    user.add(declared_github)
    display(f"Declared GitHub {declared_github}")

    # check CIS for verified login (not all users will have creds)
    verified_github_login = check_CIS(primary_email)
    if verified_github_login:
        user.add(verified_github_login)
        display(f"Verified GitHub {verified_github_login}")

    match = re.search(r"^Zimbra Alias: (?P<other_email>.*)$", email_body, re_flags)
    possible_aliases = extract_addresses(match.group("other_email") if match else None)
    user.update(possible_aliases)

    # new field: Email Alias -- list syntax (brackets)
    match = re.search(r"^Email Alias: \s*\[(?P<alias_email>.*)\]", email_body, re_flags)
    user.add(match.group("alias_email") if match else None)

    # we consider each token in the IM line as a possible GitHub login
    match = re.search(r"^IM:\s*(.*)$", email_body, re_flags)
    if match:
        im_line = match.groups()[0]
        matches = re.finditer(r"\W*((\w+)(?:\s+\w+)*)", im_line)
        user.update([x.group(1) for x in matches] if matches else None)

    match = re.search(r"^Bugzilla Email: (?P<bz_email>.*)$", email_body, re_flags)
    user.add(match.group("bz_email") if match else None)

    # grab the department name, for a heuristic on whether we expect to find perms
    expect_github_login = False
    match = re.search(r"^\s*Dept Name: (?P<dept_name>\S.*)$", email_body, re_flags)
    if match:
        department_name = match.groups()[0].lower()
        dept_keys_infering_github = ["firefox", "engineering", "qa", "operations"]
        for key in dept_keys_infering_github:
            if key in department_name:
                expect_github_login = True
                break

    # clean up some noise, case insensitively, "binary" markers
    user = {x.lower() for x in user if x and (len(x) > 2)}
    to_update = [x[2:-1] for x in user if (x.startswith("b'") and x.endswith("'"))]
    user.update(to_update)
    user = {x for x in user if not (x.startswith("b'") and x.endswith("'"))}

    # the tokens to ignore are added based on discovery,
    # they tend to cause the searches to get rate limited.
    user = user - {
        None,
        "irc",
        "slack",
        "skype",
        "b",
        "hotmail",
        "mozilla",
        "ro",
        "com",
        "softvision",
        "mail",
        "twitter",
        "blog",
        "https",
        "jabber",
        "net",
        "github",
        "gmail",
        "facebook",
        "guy",
        "pdx",
        "yahoo",
        "aim",
        "whatsapp",
        "gtalk",
        "google",
        "gpg",
        "telegram",
        "keybase",
        "zoom",
        "name",
    }
    global displayed_users
    displayed_users = set()
    try:
        headers = [
            "Search seeds: '{}'".format("', '".join(user)),
        ]
        display(*headers)
        guesses = set()
        for term in user:
            possibles = gather_possibles(term)
            guesses.update({x.lower() for x in possibles})
        # include declared_github if it exists
        if declared_github:
            guesses.add(declared_github.lower())
        guesses.update({x.login.lower() for x in displayed_users})
        display(f"Checking logins {guesses}")
        msgs = []
        msgs = check_login_perms(guesses, headers)
        found_perms = "FOUND!" in "".join(msgs)
        display(f"msgs {len(msgs)}; headers {len(headers)}")
        display(
            "found_perms {}; declared_github {} {}".format(
                found_perms, declared_github, bool(declared_github)
            )
        )

        if declared_github and not found_perms:
            msgs.append(f"Even for declared login '{declared_github}'.")
        if expect_github_login and not found_perms:
            msgs.append(
                "WARNING: expected GitHub permissions for dept '{}'".format(
                    department_name
                )
            )

        # check for GitHub login or ldap in a file (might be permissions)
        new_msgs = check_for_acls(guesses, default_login)
        msgs.extend(new_msgs)
        msgs.append("Finished all reporting.")
        display(*msgs)
    except github3.exceptions.ForbiddenError as e:
        print_limits(e)
        raise e


# %% init_cell=true hidden=true
from ipywidgets import interact_manual, Layout, widgets
from IPython.display import display

text = widgets.Textarea(
    value="email: \nim: ",
    placeholder="Paste ticket description here!",
    description="Email body:",
    layout=Layout(width="95%"),
    disabled=False,
)

run_process = interact_manual.options(manual_name="Process")


# %% init_cell=true hidden=true
def display(*args):
    # iPyWidgets don't like unicode - ensure everything we try to put there is ascii
    text = "\n".join(
        [str(x) for x in args]
    )  # deal with None values by casting to unicode
    # python 3 no longer requires us to play the convert-to-ascii game
    cleaned = text  # .encode("ascii", "replace")
    if cleaned.strip():
        print(str(cleaned))


# %% init_cell=true hidden=true
def check_github_logins(logins):
    logins_to_check = set(logins.split())
    # import pdb; pdb.set_trace()
    for login in logins_to_check:
        print("\nworking on %s:" % login)
        msgs = check_login_perms([login])
        display(*msgs)
    msgs = check_for_acls(logins_to_check)
    display(*msgs)


# %% [markdown] heading_collapsed=true hidden=true
# #### EML file support

# %% init_cell=true hidden=true
# read EML file support
import email
from ipywidgets import FileUpload
from pprint import pprint as pp
from IPython.display import display as display_widget


# %% init_cell=true hidden=true


def extract_reply(body):
    extracted = []
    for l in body.split("\r\n"):
        if l.startswith("> --"):
            break
        elif l.startswith("> "):
            extracted.append(l[2:])
    return extracted


def process_from_file(uploader):
    # message = email.message_from_string()
    for file in list(uploader.value.keys()):
        print("checking %s" % file)
        pp(list(uploader.value[file].keys()))
        content = uploader.value[file]["content"]
        pp(type(content))
        pp(type(uploader.value[file]))
        # pp(uploader.value[file])
        message = email.message_from_bytes(content)
        # message = email.message_from_string(uploader.value[file]["content"])
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            else:
                mime = part.get_content_type()
                if "plain" in mime:
                    body = part.get_payload()
                    # this could be the original, or a reply
                    if re.search(r"""^Full Name:""", body, re_flags):
                        print("original email:")
                        process_from_email(body)
                    elif re.search(r"""^> Full Name:""", body, re_flags):
                        print("reply:")
                        process_from_email("\n".join(extract_reply(body)))
                    else:
                        print("no match!\n%s" % body)


# %% [markdown]
# # Start of common usage (How To)
# %% [markdown]
# Currently, there are three common use cases:
# - processing an offboarding email (via downloaded EML file),
# - processing an offboarding email (via message copy/paste), and
# - adhoc lookup of GitHub login
#
# For anything else, you're on your own!
#
# All usage requires the following setup:
# 1. Supply your PAT token via the environment variable `GITHUB_PAT` when starting the notebook server. (If you can't do that, read the code for another way.)
# 2. Supply your CIS credentials via the environment variables `CIS_CLIENT_ID` and `CIS_CLIENT_SECRET`.
#
# %% [markdown]
# ## EML File parsing
# %% [markdown]
# Upload the file using the button below, then process that file by running the cell below the button. You can only process one file at a time, but the "file uploaded" count will continue to increase (ui glitch).

# %% init_cell=true
_uploader = FileUpload(accept="*.eml", multiple=False)
display_widget(_uploader)
# check_file(_uploader)


# %%
def check_file(f):
    try:
        # display_widget(_uploader)
        process_from_file(f)
        print("completed")
    except Exception as e:
        print(repr(e))
        raise


check_file(_uploader)

# %% [markdown] heading_collapsed=true
# ## Process offboarding email body text (copy/paste)
# %% [markdown] hidden=true
# Usage steps - for each user:
#     1. Copy entire text of email
#     2. Paste into the text area below
#     3. Click the "Process" button
#     4. Use the generated links to check for Heroku authorization
#     5. After "process finished" printed, copy/paste final output into email

# %% hidden=true
@run_process(t=text)
def show_matches(t):
    try:
        process_from_email(t)
    except Exception as e:
        print(repr(e))
        pass


# %% [markdown] heading_collapsed=true
# ## Adhoc Lookup
# %% [markdown] hidden=true
# Fill in list of the desired logins in the cell below

# %% hidden=true
check_github_logins(
    """
 """
)
print("done")

# %% [markdown] heading_collapsed=true
# # To Do
# %% [markdown] hidden=true
# - check invites as well, using manage_invitations.py
# - code doesn't handle hyphenated github logins, e.g. 'marco-c' (gets split)
# - github lookup should strip https... so can use link from people.m.o
# - dpreston, aka fzzy, doesn't have any GitHub perms
# - fix permutations of names
# - preprocess to remove all (colon separated) :b':':[:]: (maybe not the :b: & :':)
# - add link to Heroku service accounts to check
#
#
# - ~~GitHub login no longer part of email, but user id is available via CIS~~
# - ~~add "clear cache" button to purge after long idle~~ _(in tuning section)_
# - ~~add common login with 'moz{,illa}' taked on, sometimes with a dash~~
# - ~~update link to view access group on people.m.o~~
# - ~~add "trying" info to copy/paste output~~
# - ~~double check that "even for declared login" code still active~~
# - ~~add formatted output summary for copy/paste~~
# - ~~when a guess is multiple words, each word should be tried separately as well~~
# - ~~code should always search for stated github, even if search is "too many" (e.g. "past")~~
# - ~~does not call out owner status (reports as member)~~
# - ~~add short ldap name as an "always check"~~
# - ~~always check stem when search gives too many (i.e. go for the exact match)~~
# - ~~treat Zimbra Aliases as a potential multi valued list (or empty)~~
# - ~~"-" is a valid character in GitHub logins. Try as separator first-last and last-first~~
#
