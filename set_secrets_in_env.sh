#!/usr/bin/env bash
# this file is to be sourced only, and only by the Makefile
if [[ "$0" != "${BASH_SOURCE}" ]]; then
  : # do the normal stuff
else
  : # not sourced
  echo "${0##*/}: not sourced. Run: source $0 $(test $# -gt 0 && printf " %q" "$@")" 1>&2
  exit 1
fi

# to support non-secops users, allow the credentials to be pre configured via
# environment variables.

# We require either:
#   1. all 3 credentials are supplied via envronment variables &
#      SECOPS_SOPS_PATH is empty, or
#   2. SECOPS_SOPS_PATH is supplied & valid, and all 3 credentials are empty
#      In this case, the relative path to the actual credentials file must be
#      passed as the first arguement

if [[ -n $GITHUB_PAT && -n $CIS_CLIENT_ID && -n $CIS_CLIENT_SECRET \
    && -z $SECOPS_SOPS_PATH ]]; then
    # nothing to do
    :
elif [[ -n $SECOPS_SOPS_PATH
    && -z "${GITHUB_PAT}${CIS_CLIENT_ID}${CIS_CLIENT_SECRET}" ]] ; then
    if [[ -d $SECOPS_SOPS_PATH && -n "$1" ]]; then
        SOPS_credentials="$1"
        export GITHUB_PAT="$(sops -d --extract "[\"GitHub creds\"][\"token\"]" "${SOPS_credentials}")"
        # if we didn't get anything, something's wrong with config
        if [[ -z $GITHUB_PAT ]]; then
          echo "Improperly configured SOPS, see $BASH_SOURCE" >/dev/stderr
          # don't exit, as we're being sourced and don't want to kill our shell :)
          false
        fi
        export CIS_CLIENT_ID="$(sops -d --extract "[\"Person API creds\"][\"person api client id\"]" "${SOPS_credentials}")"
        export CIS_CLIENT_SECRET="$(sops -d --extract "[\"Person API creds\"][\"person api client secret\"]" "${SOPS_credentials}")"
    else
        echo "Improperly configured SOPS, see $BASH_SOURCE" >/dev/stderr
        false
    fi
else
    echo "Improperly configured credentials. See $BASH_SOURCE" >/dev/stderr
    false
fi
