# github org helper scripts

These are some API helper scripts for sanely managing a github org. For now this is somewhat hardcoded for the mozilla org; no need for it to remain that way though.

## Scripts
### contributing.py
Analyze all the "sources" repositories (i.e., those that aren't forks) in a github org and list the repositories that do *NOT* have a CONTRIBUTING file.

### admins.py
Show all org admins *WITHOUT* [Two-Factor
Auth](https://help.github.com/articles/about-two-factor-authentication/) enabled

### audit-log-export.js
Sadly, the org audit log does not have an API. So here's a little bit of JavaScript you can run on any audit log page to export the data into a somewhat more digestible JSON format.

Example URL: https://github.com/orgs/acmecorp/audit-log

Yes, you have to go to the next page and re-run this to get another file.


## Auth
The API calls need you to authenticate. Generate a "personal access token" on the github settings page, then create a file ``.credentials`` like this:

    johndoe
    123abcmygithubtoken123...

where the first line is your github username and the second line is the token you generated.

## License
This code is free software and licensed under an MIT license. &copy; 2015 Fred Wenzel <fwenzel@mozilla.com>. For more information read the file ``LICENSE``.
