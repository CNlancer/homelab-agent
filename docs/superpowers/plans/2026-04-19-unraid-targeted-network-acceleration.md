# Unraid Targeted Network Acceleration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add auditable, reversible Unraid actions that route only Community Applications and Docker daemon download traffic through the Mac mini Surge proxy at `10.0.0.2:6152`.

**Architecture:** Extend the existing Unraid SSH adapter and executor with two explicit safe-write actions. Each action writes backups on the Unraid boot device, returns rollback metadata, and relies on the existing `ExecutionService` audit path plus local ops log rules.

**Tech Stack:** Python 3.9, `uv`, pytest, existing `SshCommandAdapter`, Unraid SSH profile in `local/secrets/unraid.json`, JSONL audit under `var/`.

---

## File Structure

- Modify `src/homelab_agent/executors/unraid/adapter.py`: add CA proxy config and Docker daemon proxy config helpers.
- Modify `src/homelab_agent/executors/unraid/executor.py`: expose two structured actions and validate arguments.
- Modify `src/homelab_agent/bootstrap.py`: register both actions when the Unraid profile exists.
- Modify `tests/executors/unraid/test_adapter.py`: TDD coverage for remote command construction and returned metadata.
- Modify `tests/executors/unraid/test_executor.py`: TDD coverage for action dispatch and argument validation.
- Modify `tests/test_bootstrap.py`: TDD coverage for router registration.

## Task 1: Community Applications Proxy Action

**Files:**
- Modify: `tests/executors/unraid/test_adapter.py`
- Modify: `tests/executors/unraid/test_executor.py`
- Modify: `tests/test_bootstrap.py`
- Modify: `src/homelab_agent/executors/unraid/adapter.py`
- Modify: `src/homelab_agent/executors/unraid/executor.py`
- Modify: `src/homelab_agent/bootstrap.py`

- [ ] **Step 1: Write failing adapter test**

Add this test to `tests/executors/unraid/test_adapter.py`:

```python
def test_configure_ca_proxy_writes_proxy_cfg_with_backup_metadata():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "config_path=/boot/config/plugins/community.applications/proxy.cfg",
                "backup_path=/boot/config/plugins/community.applications/proxy.cfg.bak.20260419130000",
                "proxy_url=http://10.0.0.2:6152",
                "tunnel=1",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.configure_community_applications_proxy(
        config,
        proxy_host="10.0.0.2",
        proxy_port=6152,
        tunnel=True,
    )

    remote_command = commands[0][-1]
    assert "cfg=/boot/config/plugins/community.applications/proxy.cfg" in remote_command
    assert "proxy=10.0.0.2" in remote_command
    assert "port=6152" in remote_command
    assert 'printf \'proxy="%s"\\nport="%s"\\ntunnel="%s"\\n\'' in remote_command
    assert payload["proxy_url"] == "http://10.0.0.2:6152"
    assert payload["tunnel"] == "1"
```

- [ ] **Step 2: Verify adapter test fails**

Run: `uv run pytest tests/executors/unraid/test_adapter.py::test_configure_ca_proxy_writes_proxy_cfg_with_backup_metadata -q`

Expected: FAIL with `AttributeError` because `configure_community_applications_proxy` does not exist.

- [ ] **Step 3: Write failing executor and router tests**

Add a stub method to `StubSshAdapter` in `tests/executors/unraid/test_executor.py`:

```python
    def configure_community_applications_proxy(
        self,
        config: TargetConfig,
        proxy_host: str,
        proxy_port: int,
        tunnel: bool = True,
    ) -> dict:
        self.calls.append(("configure_community_applications_proxy", config.label, proxy_host, proxy_port, tunnel))
        return {"proxy_url": f"http://{proxy_host}:{proxy_port}", "tunnel": "1" if tunnel else "0"}
```

Add this test:

```python
def test_executor_configures_community_applications_proxy():
    adapter = StubSshAdapter()
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root", ssh_password="secret")
    executor = UnraidExecutor(adapter=adapter, target_configs={"unraid": config})

    payload = executor.run(
        "configure_community_applications_proxy",
        target_name="unraid",
        arguments={"proxy_host": "10.0.0.2", "proxy_port": 6152, "tunnel": True},
    )

    assert adapter.calls == [("configure_community_applications_proxy", "unraid", "10.0.0.2", 6152, True)]
    assert payload["community_applications_proxy"]["proxy_url"] == "http://10.0.0.2:6152"
```

Add this test to `tests/test_bootstrap.py`:

```python
def test_build_router_registers_unraid_community_applications_proxy_action(tmp_path: Path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "unraid.json").write_text(
        '{"label":"unraid","ssh_host":"10.0.0.11","ssh_username":"root","ssh_password":"secret"}',
        encoding="utf-8",
    )
    router = build_router(config_root=secrets_dir)
    task = TaskSpec(
        target_type="unraid",
        target_name="unraid",
        action="configure_community_applications_proxy",
        arguments={"proxy_host": "10.0.0.2", "proxy_port": 6152},
        risk_level=RiskLevel.SAFE_WRITE,
        confirmation_required=True,
    )

    registered = router.resolve(task)

    assert registered.executor_name == "unraid"
    assert registered.action_name == "configure_community_applications_proxy"
```

- [ ] **Step 4: Verify executor and router tests fail**

Run: `uv run pytest tests/executors/unraid/test_executor.py::test_executor_configures_community_applications_proxy tests/test_bootstrap.py::test_build_router_registers_unraid_community_applications_proxy_action -q`

Expected: FAIL because the action is not registered or implemented.

- [ ] **Step 5: Implement CA proxy action**

Add `configure_community_applications_proxy` and a command builder to `src/homelab_agent/executors/unraid/adapter.py`. It must:

- require non-empty `proxy_host`
- require `1 <= proxy_port <= 65535`
- create `/boot/config/plugins/community.applications`
- back up an existing `proxy.cfg`
- write:

```text
proxy="10.0.0.2"
port="6152"
tunnel="1"
```

Return parsed key-value output with `config_path`, `backup_path`, `proxy_url`, and `tunnel`.

Expose the action in `src/homelab_agent/executors/unraid/executor.py` as `configure_community_applications_proxy`.

Register the action in `src/homelab_agent/bootstrap.py`.

- [ ] **Step 6: Verify CA proxy tests pass**

Run: `uv run pytest tests/executors/unraid/test_adapter.py tests/executors/unraid/test_executor.py tests/test_bootstrap.py -q`

Expected: PASS.

## Task 2: Docker Daemon Proxy Action

**Files:**
- Modify: `tests/executors/unraid/test_adapter.py`
- Modify: `tests/executors/unraid/test_executor.py`
- Modify: `tests/test_bootstrap.py`
- Modify: `src/homelab_agent/executors/unraid/adapter.py`
- Modify: `src/homelab_agent/executors/unraid/executor.py`
- Modify: `src/homelab_agent/bootstrap.py`

- [ ] **Step 1: Write failing adapter test**

Add this test to `tests/executors/unraid/test_adapter.py`:

```python
def test_configure_docker_daemon_proxy_writes_boot_env_with_no_proxy():
    commands = []

    def runner(command: list[str]) -> str:
        commands.append(command)
        return "\n".join(
            [
                "config_path=/boot/config/docker-proxy.env",
                "backup_path=",
                "proxy_url=http://10.0.0.2:6152",
                "restart_docker=false",
                "docker_restarted=false",
            ]
        )

    adapter = SshCommandAdapter(command_runner=runner)
    config = TargetConfig(label="unraid", ssh_host="10.0.0.11", ssh_username="root")

    payload = adapter.configure_docker_daemon_proxy(
        config,
        proxy_url="http://10.0.0.2:6152",
        no_proxy="localhost,127.0.0.1,10.0.0.0/8",
        restart_docker=False,
    )

    remote_command = commands[0][-1]
    assert "cfg=/boot/config/docker-proxy.env" in remote_command
    assert "HTTP_PROXY=http://10.0.0.2:6152" in remote_command
    assert "NO_PROXY=localhost,127.0.0.1,10.0.0.0/8" in remote_command
    assert payload["proxy_url"] == "http://10.0.0.2:6152"
    assert payload["docker_restarted"] == "false"
```

- [ ] **Step 2: Verify adapter test fails**

Run: `uv run pytest tests/executors/unraid/test_adapter.py::test_configure_docker_daemon_proxy_writes_boot_env_with_no_proxy -q`

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Write failing executor and router tests**

Add a stub method and executor test mirroring the CA proxy pattern, using action name `configure_docker_daemon_proxy`.

Add a router test in `tests/test_bootstrap.py` asserting `configure_docker_daemon_proxy` resolves for target type `unraid`.

- [ ] **Step 4: Implement Docker daemon proxy action**

Add `configure_docker_daemon_proxy` to `src/homelab_agent/executors/unraid/adapter.py`. It must:

- require `proxy_url` to start with `http://` or `https://`
- write `/boot/config/docker-proxy.env`
- back up an existing file
- store `HTTP_PROXY`, `HTTPS_PROXY`, `http_proxy`, `https_proxy`, `NO_PROXY`, and `no_proxy`
- optionally restart Docker with `/etc/rc.d/rc.docker restart`
- return `config_path`, `backup_path`, `proxy_url`, `restart_docker`, and `docker_restarted`

Expose and register the action in executor and bootstrap.

- [ ] **Step 5: Verify Docker proxy tests pass**

Run: `uv run pytest tests/executors/unraid/test_adapter.py tests/executors/unraid/test_executor.py tests/test_bootstrap.py -q`

Expected: PASS.

## Task 3: Execute Against Unraid

**Files:**
- Runtime local logs: `var/audit.jsonl`, `var/ops-log.jsonl`
- Remote files: `/boot/config/plugins/community.applications/proxy.cfg`, `/boot/config/docker-proxy.env`

- [ ] **Step 1: Verify Surge proxy reachability**

Run a read-only Unraid SSH check that verifies `10.0.0.2:6152` is open and CA/GHCR/LSCR endpoints respond through the proxy.

- [ ] **Step 2: Configure Community Applications proxy**

Run:

```bash
uv run homelab-agent \
  --target-type unraid \
  --target-name unraid \
  --action configure_community_applications_proxy \
  --arguments '{"proxy_host":"10.0.0.2","proxy_port":6152,"tunnel":true}' \
  --risk-level safe_write \
  --confirm
```

Expected: success JSON with `config_path`, `backup_path`, and `proxy_url`.

- [ ] **Step 3: Verify CA proxy**

Read `/boot/config/plugins/community.applications/proxy.cfg` and test CA endpoints through `curl -x http://10.0.0.2:6152`.

- [ ] **Step 4: Configure Docker daemon proxy without restart first**

Run:

```bash
uv run homelab-agent \
  --target-type unraid \
  --target-name unraid \
  --action configure_docker_daemon_proxy \
  --arguments '{"proxy_url":"http://10.0.0.2:6152","restart_docker":false}' \
  --risk-level safe_write \
  --confirm
```

Expected: success JSON with `config_path` and `docker_restarted=false`.

- [ ] **Step 5: Decide restart timing**

If the user wants the Docker daemon proxy active immediately, rerun with `restart_docker=true`. Otherwise leave the persistent env file ready for the next Docker service restart.

- [ ] **Step 6: Verify logs**

Confirm `var/audit.jsonl` contains successful structured action entries and append `var/ops-log.jsonl` only if a manual operation was needed.

## Self-Review

- Spec coverage: CA proxy, Docker daemon proxy, default-route preservation, container runtime isolation, verification, rollback metadata, and local audit logging are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: action names are `configure_community_applications_proxy` and `configure_docker_daemon_proxy`; both use existing `TargetConfig` and `SshCommandAdapter` patterns.
