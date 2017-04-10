# github org helper scripts

**NOTE: branch 'invitations' requires a version of github3.py which has
not yet been released.** See
[PR](https://github.com/sigmavirus24/github3.py/pull/675) for details.

These are some API helper scripts for sanely managing a github org. For now this is somewhat hardcoded for the mozilla org; no need for it to remain that way though.

## Scripts
### auditlog.py
Download audit log for $ORG via headless firefox via selenium
([``geckodriver``][gd_url] must be installed). Credentials as environment
variables, and 2FA token passed as input when requested.

### contributing.py
Analyze all the "sources" repositories (i.e., those that aren't forks) in a github org and list the repositories that do *NOT* have a CONTRIBUTING file.

### get_active_hooks.py
Find all hooks configured for an organization -- see --help for details

### team_update.py
Update administrative teams so they can be used for the new GitHub discussion
feature. Use the ``--help`` option for more information.

### lfs.py
Get current LFS Billing values using a headless firefox via selenium
(``geckodriver`` must be installed). Credentials as environment
variables, and 2FA token passed as input.

### Audit logs
Sadly, the org audit log does not have an API, so we'll screen scrape a little.

#### audit-log-export.js
So here's a little bit of JavaScript you can run on any audit log page to export the data into a somewhat more digestible JSON format.

Example URL: https://github.com/orgs/acmecorp/audit-log

Yes, you have to go to the next page and re-run this to get another file.

#### hooks.py
Analyzes a list of audit log export files (from the JS script) for hook/service creation/deletion and provides a summary. Use it to show commonly used apps/services/webhooks across the org.

### old_repos.py
Generate a list of empty (should be deleted) repositories as well as untouched repos (might need to be archived).

## Auth
The API calls need you to authenticate. Generate a "personal access token" on the github settings page, then create a file ``.credentials`` like this:

    johndoe
    123abcmygithubtoken123...

where the first line is your github username and the second line is the token you generated.

## License
This code is free software and licensed under an MPL-2.0 license. &copy; 2015-2018 Fred Wenzel and others. For more information read the file ``LICENSE``.

[gd_url]: https://github.com/mozilla/geckodriver/releases
