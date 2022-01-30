#!/usr/bin/env bash

# adapted from https://stackoverflow.com/a/12523283/5128493
#
# Note that python3 time.tzset() expects an Olson timezone value in the TZ
# environment variable.

# don't override what is already set
if [[ -z $TZ ]]; then
  if [[ -f /etc/timezone ]]; then
    # Ubuntu
    TZ=$(cat /etc/timezone)
  elif [[ -h /etc/localtime ]]; then
    # macOS
    t=$(readline /etc/localtime)
    TZ=${t##*zoneinfo/}
  else
    # no local time found, use UTC
    TZ=UTC
  fi
fi
echo $TZ
