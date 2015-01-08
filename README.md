# github org helper scripts

These are some API helper scripts for sanely managing a github org. For now this is somewhat hardcoded for the mozilla org; no need for it to remain that way though.

# Scripts
**contributing.py**: Analyze all the "sources" repositories (i.e., those that aren't forks) in a github org and file bugs / pull requests for those repositories do *NOT* have a CONTRIBUTING file.

This ensures that all repositories in an org make explicit what the requirements for contributing code to the organization are, be it a simple "this is how you submit a successful pull request" or "you have to sign this agreement before you can contribute".

## Auth
The API calls need you to authenticate. Generate a "personal access token" on the github settings page, then create a file ``.credentials`` like this:

    johndoe
    123abcmygithubtoken123...

where the first line is your github username and the second line is the token you generated.

## License
This code is free software and licensed under an MIT license. &copy; 2015 Fred Wenzel <fwenzel@mozilla.com>. For more information read the file ``LICENSE``.
