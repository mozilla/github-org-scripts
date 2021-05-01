# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # GitHub playground
# Designed for adhoc queries using the GitHub3.py library

# %%
# set values here - you can also override below
# get api key from environment, fall back to file
import os
api_key = os.environ.get("GITHUB_PAT", "")
if not api_key:
    api_key = open(".credentials").readlines()[1].strip()
if not api_key:
    raise OSError("no GitHub PAT found")


# %%
import github3
gh = github3.login(token=api_key)
print(f"You are authenticated as {gh.me().login}")

# %% [markdown]
# From here on, use ``gh`` to access all data

# %%
orgs = ["MozillaReality"]


# %%
for o in orgs:
    org = gh.organization(o)
    print((org.login, org.id))


# %%
u = gh.user(o)
u.login
