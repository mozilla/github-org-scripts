#!/usr/bin/env python

import json
import re
import sys


err = lambda s: sys.stderr.write('%s\n' % s)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        err('Usage: %s audit-log.json audit-log-2.json ...' % sys.argv[0])
        sys.exit(1)

    # Load logs from file.
    logs = []
    for logfile in sys.argv[1:]:
        logs.extend(json.loads(open(logfile).read()))

    # Reduce to hook.{create,destroy}, sort.
    logs = filter(lambda i: i['type'] in ('hook.create', 'hook.destroy'), logs)
    logs.sort(key=lambda i: i['when'])

    # List hooks and services per repo...
    tally = {}
    for log in logs:
        # Find service/repo
        m = re.search(r'(?:un)?installed (.+)\sfor ([\w/]+)', log['what'])
        if not m:
            err('No match for %s' % str(log))
            continue
        else:
            service = m.group(1)
            repo = m.group(2)

        if log['type'] == 'hook.create':
            if not tally.get(service):
                tally[service] = set([repo])
            else:
                tally[service].add(repo)

        elif log['type'] == 'hook.destroy':
            if tally.get(service):
                tally[service].discard(repo)
                if not tally[service]:  # Now empty
                    del tally[service]
            # Else ignore.

    # ... then count.
    tally = [(name, len(repos)) for name, repos in tally.items()]
    # Sort by amount of use, descending.
    tally.sort(key=lambda i: i[1], reverse=True)

    for service, usage in tally:
        print '%s: %s' % (service, usage)
