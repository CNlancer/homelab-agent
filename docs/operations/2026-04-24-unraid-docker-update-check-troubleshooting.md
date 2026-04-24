# Unraid Docker Update Check Troubleshooting

## Summary

This note captures the debugging path and durable fixes for a specific Unraid
Docker page problem:

- `home-assistant` showed `not available`
- the row still exposed `force update`
- the internal Docker manager status was `update:3`

The same Unraid host correctly showed `plex` and `qbittorrent` as
`up-to-date`.

The final fix was **not** "switch Home Assistant to Docker Hub". The real issue
was that Unraid's Docker manager update-check path did not inherit the same
proxy route already configured for:

- Community Applications
- Docker daemon image pulls

Once the WebUI/PHP path was patched to import the same proxy environment,
Home Assistant returned to `update:0 / up-to-date`.

## Environment

- Unraid host: `10.0.0.11`
- Proxy host: `10.0.0.2:6152`
- Home Assistant container: `home-assistant`
- Home Assistant image in steady state: `ghcr.io/home-assistant/home-assistant:stable`

## Symptoms

- Unraid Docker page rendered Home Assistant as:
  - `not available`
  - `force update`
  - `stable`
- Docker manager internal payload showed:

```text
docker.push({name:'home-assistant', ..., update:3});
```

- Direct `docker pull` on Unraid still worked.
- Docker daemon already had working proxy settings.
- Community Applications already had working proxy settings.

## What Was Ruled Out

### 1. The container itself was not broken

Home Assistant was reachable and healthy:

- UI on `http://10.0.0.11:8123`
- HomeKit ports reachable
- config checks passed

### 2. Docker registry access itself was not broken

Unraid could already:

- `docker pull homeassistant/home-assistant:stable`
- reach Docker-related endpoints through the configured proxy

That proved the failure was not basic registry reachability.

### 3. Switching to Docker Hub was not the real fix

There was a temporary experiment switching Home Assistant from:

```text
ghcr.io/home-assistant/home-assistant:stable
```

to:

```text
homeassistant/home-assistant:stable
```

That did **not** fix the `not available` state by itself.

Conclusion:

- keep Home Assistant on the official image path that best fits the workflow
- do not treat "use Docker Hub instead of GHCR" as the root solution here

## Real Root Cause

Unraid had three separate outbound paths:

1. Community Applications plugin downloads
2. Docker daemon image pulls and registry access
3. Docker page update checks performed by Unraid WebUI / PHP

Only the first two were already routed through the special proxy path.

The third path, Unraid WebUI's Docker update check, used PHP cURL logic inside
Docker manager and did **not** automatically inherit the proxy environment used
by the Docker daemon.

That mismatch caused Docker manager to save:

```json
{
  "homeassistant/home-assistant:stable": {
    "local": "...",
    "remote": null,
    "status": "undef"
  }
}
```

and the UI mapped that to `update:3 / not available`.

## Important Discovery About Verification

Manually posting to:

```text
/plugins/dynamix.docker.manager/include/DockerUpdate.php
```

without the page's `csrf_token` is misleading.

It can look like the update check "ran", while the Docker page still stays on
stale state.

The reliable verification flow is:

1. log into Unraid
2. load `/Docker`
3. extract `var csrf_token = "..."`
4. POST `DockerUpdate.php` with that token
5. re-read `DockerContainers.php`

After this, the result changed from:

```text
update:3
```

to:

```text
update:0
```

and the row rendered `up-to-date`.

## Durable Fix Implemented

The repo now provides `unraid.configure_webui_proxy`.

It installs a persistent Unraid-side fix that writes:

- `/boot/config/plugins/homelab-agent/unraid-webui-proxy.env`
- `/boot/config/plugins/homelab-agent/apply-webui-proxy.sh`
- a boot hook in `/boot/config/go`

It also patches runtime consumers that matter for Docker page checks:

- `/etc/php-fpm.d/www.conf`
- `/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerUpdate.php`

### Why both php-fpm and DockerUpdate.php needed attention

`php-fpm` defaults can clear environment, so exporting variables in a shell
script alone is not enough to prove the Docker manager PHP code will see them.

The durable path was:

- enable the needed proxy values for the PHP-FPM side
- explicitly import the proxy env file inside `DockerUpdate.php`

This avoids depending on fragile assumptions about daemon startup environment.

## Lessons Learned

### 1. Separate "pull path" from "update-check path"

If `docker pull` works but the Docker page still says `not available`, inspect
the WebUI/PHP path separately.

### 2. Check the real Docker manager data source

The page is ultimately driven by:

```text
/plugins/dynamix.docker.manager/include/DockerContainers.php
```

If that still emits `update:3`, the UI is not the problem.

### 3. Use CSRF-correct replay for Unraid page actions

For Docker page actions, replaying the request without the page's CSRF token is
not a trustworthy validation step.

### 4. Do not normalize image registries without evidence

Changing HA from GHCR to Docker Hub was a diagnostic detour, not the fix.

### 5. Do not normalize tag names blindly

`stable` and `latest` are image-owner policy choices, not a single universal
standard.

For this host:

- Home Assistant uses official `stable`
- `plex` and `qbittorrent` currently use LinuxServer images on `latest`

Do **not** force them all to the same tag family unless the upstream image
actually publishes an equivalent and intended tag.

Good rule:

- `stable` is appropriate when the upstream officially uses `stable`
- `latest` is appropriate when the upstream or current template expects
  `latest`
- changing tags should be treated as an image-policy migration, not cosmetic
  cleanup

## Practical Guidance For This Host

### Home Assistant

Preferred steady-state image:

```text
ghcr.io/home-assistant/home-assistant:stable
```

Reason:

- official upstream path
- the `not available` issue was caused by Unraid WebUI proxy handling, not by
  GHCR vs Docker Hub

### Plex and qBittorrent

Current state is acceptable:

- `lscr.io/linuxserver/plex:latest`
- `lscr.io/linuxserver/qbittorrent:latest`

Do not switch them to `stable` just for visual consistency unless:

- the upstream publishes an intended `stable` tag
- the Unraid template and maintenance workflow are adjusted accordingly

## Verification Checklist

When this issue reappears, verify in this order:

1. `docker pull` still works on Unraid
2. `/boot/config/plugins/homelab-agent/unraid-webui-proxy.env` still exists
3. `/boot/config/go` still contains the webui proxy hook
4. `DockerUpdate.php` still contains the homelab-agent proxy block
5. `/Docker` page CSRF token can be extracted
6. posting `DockerUpdate.php` with CSRF changes `DockerContainers.php` output
7. `home-assistant` row becomes `up-to-date`

## Repo References

- [adapter.py](/Users/lancer/projects/homelab-agent/src/homelab_agent/executors/unraid/adapter.py)
- [executor.py](/Users/lancer/projects/homelab-agent/src/homelab_agent/executors/unraid/executor.py)
- [bootstrap.py](/Users/lancer/projects/homelab-agent/src/homelab_agent/bootstrap.py)
- [test_adapter.py](/Users/lancer/projects/homelab-agent/tests/executors/unraid/test_adapter.py)
- [test_executor.py](/Users/lancer/projects/homelab-agent/tests/executors/unraid/test_executor.py)
- [test_bootstrap.py](/Users/lancer/projects/homelab-agent/tests/test_bootstrap.py)
