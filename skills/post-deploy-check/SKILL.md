---
name: post-deploy-check
description: Verify a deploy by exercising the deployed instance, not the local one. Use immediately after any deploy, restart, migration or configuration change that reaches a running environment.
---

# Post-deploy check

> **After a deploy, integration tests run against the deployed instance — never
> the local one.**

A green suite on a developer machine, or a green CI job on a branch, proves
nothing about what is running. Only a transaction executed against the deployed
instance does.

## A connectivity check is not an integration test

Paid for twice:

- four applications answered `200` on their health endpoints while **every
  registration returned 500**. A gateway between two of them was not running,
  and nothing that only checked reachability could see it. The stack "looked
  like it worked".
- a port was open and a unit reported `active` while the component behind it had
  never started.

**So assert on content, never on a status code alone.**

## What to run

One real transaction, end to end — the one whose failure would matter most:

1. **Write, then read back.** A create followed by a fetch of the same object.
   A read-only probe cannot see a broken write path.
2. **Cross every boundary the request really crosses** — proxy, gateway, queue,
   database. Hitting the application directly skips the component most likely to
   be missing.
3. **Assert on the payload.** A field with an expected value, not `200`.
4. **Then clean up**, and prove the cleanup happened.

## Before declaring it done

```sh
# the thing is actually the thing you think it is
curl -s <deployed>/version        # expected build, not just a response
# the transaction, not the port
curl -s -X POST <deployed>/<path> -d '<minimal payload>' | grep -q '<expected>'
```

⚠️ If any of this cannot be run, say **so** — "not verified" is a complete and
useful answer. "Deployed successfully" said after a connectivity check is not.

## What makes this fail silently

- **A fixture or a double left in place.** A test that passes against a stub
  proves the stub works.
- **A cached response.** The second call may never reach the deployed instance.
- **Testing the instance you just built locally** because its address was the
  convenient one. Check the host you assert against; it is the single most
  common way this check gets inverted.
