# github org helper scripts

Current minimums: python 3.7; GitHub3.py 1.3.0

These are some API helper scripts for sanely managing a github org. For now this is somewhat hardcoded for the mozilla org; no need for it to remain that way though.

## Credentials

Supplying credentials for execution is done by passing a PAT token as the value
of the environment variable `GITHUB_TOKEN` (preferred) or `GITHUB_PAT`.

The recommended way to set `GITHUB_TOKEN` is via cli access to your password
manager. For example, using [pass][pass]:
```bash
GITHUB_TOKEN=$(pass show myPAT) script args
```
[pass]: https://www.passwordstore.org/

## Jupyter Notebooks
### User Search.ipynb
Given a set of possible GitHub logins, determine if they might have any
permissions in various organizations. Links are provided for hits, so easy to
examine more closely.

N.B.: Both this script and the GitHub search interface make assumptions. It is
*your* responsibility to ensure any possible match is a valid match.

## Scripts
### auditlog.py
Download audit log for $ORG via headless firefox via selenium
([``geckodriver``][gd_url] must be installed). Credentials as environment
variables, and 2FA token passed as input when requested.

### contributing.py
Analyze all the "sources" repositories (i.e., those that aren't forks) in a github org and list the repositories that do *NOT* have a CONTRIBUTING file.

### get_active_hooks.py
Find all hooks configured for an organization -- see --help for details

### get_org_info.py
Output basic info about an org, more if you have permissions. See --help for details

### lfs.py
Get current LFS Billing values using a headless firefox via selenium
(``geckodriver`` must be installed). Credentials as environment
variables, and 2FA token passed as input.

### manage_invitations.py
Cancel all org & repository invitations older than a specified age (default 2
weeks). See --help for details.

### team_update.py
Update administrative teams so they can be used for the new GitHub discussion
feature. Use the ``--help`` option for more information.

### Audit logs
Sadly, the org audit log does not have an API, so we'll screen scrape a little.

#### hooks.py
Analyzes a list of audit log export files (from the JS script) for hook/service creation/deletion and provides a summary. Use it to show commonly used apps/services/webhooks across the org.

### old_repos.py
Generate a list of empty (should be deleted) repositories as well as untouched repos (might need to be archived).

## License
This code is free software and licensed under an MPL-2.0 license. &copy; 2015-2021 Fred Wenzel and others. For more information read the file ``LICENSE``.

[gd_url]: https://github.com/mozilla/geckodriver/releases
