# Unraid Targeted Network Acceleration Design

## Context

The Unraid host should keep its normal default route through the router at
`10.0.0.1`. The Mac mini at `10.0.0.2` runs Surge and has a faster outbound path
for Docker Hub, GitHub, GHCR, LSCR, and Community Applications resources through
the user's VPS.

The goal is to speed up Unraid Apps and Docker image update flows without
turning the Mac mini into the default gateway for all Unraid traffic and without
changing container runtime networking.

Surge LAN proxy access has been enabled and verified from Unraid:

- HTTP proxy: `10.0.0.2:6152`
- SOCKS proxy: `10.0.0.2:6153`

Measured through the HTTP proxy from Unraid:

- `https://ghcr.io/v2/` responds in about 0.44 seconds.
- `https://lscr.io/v2/` responds in about 0.48 seconds.
- `https://ca.unraid.net/assets/feed/applicationFeed-lastUpdated.json` responds in about 0.77 seconds.
- `https://assets.ca.unraid.net/feed/statistics.json` responds in about 0.63 seconds.
- `https://raw.githubusercontent.com/Squidly271/AppFeed/master/applicationFeed-lastUpdated.json` responds in about 0.42 seconds.

## Goals

- Keep Unraid's default gateway and normal host routing unchanged.
- Route only selected download clients through the Mac mini's Surge proxy.
- Improve Community Applications page and appfeed responsiveness.
- Improve Docker image update and pull behavior for Docker Hub, GHCR, and LSCR.
- Avoid routing running containers' own application traffic through the Mac mini.
- Keep the setup easy to audit and easy to roll back from this repository.

## Non-Goals

- Do not build a dashboard or general network management UI.
- Do not deploy a transparent proxy.
- Do not change Unraid's default route.
- Do not proxy all Unraid traffic.
- Do not require container templates to be rewritten unless a future registry
  cache phase explicitly needs it.
- Do not expose Surge remote control, HTTP API, or dashboard to the LAN.

## Recommended Approach

Use explicit proxy configuration for two clients:

1. Community Applications uses its own proxy config under
   `/boot/config/plugins/community.applications/proxy.cfg`.
2. Docker daemon uses `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` when it pulls
   images or talks to registries.

This keeps the routing boundary simple:

```text
Unraid default route -> 10.0.0.1

Community Applications downloads -> http://10.0.0.2:6152
Docker daemon registry requests   -> http://10.0.0.2:6152
Container runtime traffic         -> unchanged
LAN/internal traffic              -> unchanged
```

The existing Docker Hub registry mirror can remain in place:

```text
https://docker.1ms.run
```

The proxy and the mirror can coexist. Docker Hub pulls may benefit from either
path, while GHCR and LSCR require proxy handling because Docker's
`registry-mirrors` setting does not apply to those registries.

## Components

### Mac Mini Surge

Surge owns the outbound acceleration path. It should keep LAN proxy access
enabled for the proxy service only.

Required service:

- `http://10.0.0.2:6152`

Optional service:

- `socks5://10.0.0.2:6153`

Not required:

- Remote Controller
- HTTP API
- Web Dashboard
- Access from outside the LAN

Surge rules should send registry and Community Applications related domains
through the VPS-backed policy.

### Community Applications Proxy

Community Applications supports a proxy config file at:

```text
/boot/config/plugins/community.applications/proxy.cfg
```

The proxy should point to the Surge HTTP proxy:

```text
proxy="10.0.0.2"
port="6152"
tunnel="1"
```

This should affect appfeed, template, plugin, GitHub raw, and CA asset downloads
made by the Community Applications plugin. It should not change Unraid's default
route.

### Docker Daemon Proxy

Docker daemon should receive:

```text
HTTP_PROXY=http://10.0.0.2:6152
HTTPS_PROXY=http://10.0.0.2:6152
NO_PROXY=localhost,127.0.0.1,::1,10.0.0.0/8,192.168.0.0/16,172.16.0.0/12,.local
```

This affects Docker daemon registry access, including image pull and update
checks. It does not automatically proxy application traffic from already running
containers.

The exact Unraid persistence mechanism should be implemented as a structured
repo action after confirming the least invasive hook for this Unraid version.
The action should back up any modified boot config files before changing them.

## Domain Coverage

Community Applications and plugin resources:

- `ca.unraid.net`
- `assets.ca.unraid.net`
- `raw.githubusercontent.com`
- `github.com`

Docker and registry resources:

- `registry-1.docker.io`
- `auth.docker.io`
- `production.cloudflare.docker.com`
- `ghcr.io`
- `lscr.io`
- `quay.io` if future templates use it

Internal addresses should bypass the proxy through `NO_PROXY`.

## Implementation Plan Shape

Implementation should happen in two small, reversible phases.

### Phase 1: Community Applications Proxy

Add a structured Unraid action that:

- Reads the current CA proxy config if it exists.
- Writes a backup before any change.
- Writes `proxy.cfg` pointing at `10.0.0.2:6152`.
- Verifies appfeed endpoints through CA's proxy path where possible.
- Records the action in the audit log.

Rollback removes or restores the previous `proxy.cfg`.

### Phase 2: Docker Daemon Proxy

Add a structured Unraid action that:

- Detects the current Docker daemon startup/proxy configuration.
- Writes a backup before any change.
- Adds proxy environment for the Docker daemon only.
- Keeps `NO_PROXY` for localhost and private network ranges.
- Restarts Docker only after explicit confirmation.
- Verifies `docker manifest inspect` for Docker Hub, GHCR, and LSCR images.

Rollback restores the previous Docker daemon proxy configuration and restarts
Docker after confirmation.

## Verification

Before changing configuration:

- Confirm `10.0.0.2:6152` is reachable from Unraid.
- Confirm CA, GHCR, LSCR, and GitHub raw URLs work through the proxy.

After Phase 1:

- Confirm Community Applications appfeed timestamp downloads through the proxy.
- Check `/var/log/syslog` for Community Applications timeout errors.
- Open `/Apps` manually and confirm perceived responsiveness.

After Phase 2:

- Confirm Docker daemon still reports the existing Docker Hub mirror if it is
  retained.
- Confirm `docker manifest inspect ghcr.io/...` and `lscr.io/...` work through
  the daemon environment.
- Pull or update one small Docker Hub image and one GHCR image.
- Confirm running containers still use their original network paths.

## Failure Handling

- If Surge is not reachable, the repo action should fail before writing changes.
- If CA proxy verification fails after writing config, restore the backup.
- If Docker daemon fails to restart, restore the backup and restart Docker again.
- If proxy speed is worse than direct access, keep the config reversible rather
  than forcing all traffic through the Mac mini.

## Open Decisions

- Whether to keep `https://docker.1ms.run` as a Docker Hub mirror after Docker
  daemon proxy is enabled. The default recommendation is to keep it for now.
- Whether to later add registry cache containers. This is deferred until the
  explicit proxy path proves stable and the user sees repeated image pull pain.
