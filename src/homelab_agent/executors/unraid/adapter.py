import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from homelab_agent.config.models import TargetConfig


CommandRunner = Callable[[list[str]], str]
PasswordCommandRunner = Callable[[list[str], dict, object], str]


def run_command(command: list[str], env: Optional[dict] = None, stdin: object = None) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        env=env,
        stdin=stdin,
        text=True,
        timeout=120,
    )
    return completed.stdout


class SshCommandAdapter:
    def __init__(
        self,
        command_runner: CommandRunner = run_command,
        password_command_runner: PasswordCommandRunner = run_command,
    ) -> None:
        self._command_runner = command_runner
        self._password_command_runner = password_command_runner

    def _build_ssh_command(self, config: TargetConfig, remote_command: str) -> list[str]:
        command = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
        ]
        if config.ssh_identity_file is not None:
            command.extend(["-i", str(config.ssh_identity_file)])
        command.append("{0}@{1}".format(config.ssh_username, config.ssh_host))
        command.append(remote_command)
        return command

    def _run_ssh(self, config: TargetConfig, remote_command: str) -> str:
        if config.ssh_password is not None:
            return self._run_ssh_with_password(config, remote_command)
        return self._command_runner(self._build_ssh_command(config, remote_command))

    def _run_ssh_with_password(self, config: TargetConfig, remote_command: str) -> str:
        askpass_path = self._write_askpass_script()
        try:
            env = os.environ.copy()
            env.update(
                {
                    "DISPLAY": "homelab-agent:0",
                    "SSH_ASKPASS": str(askpass_path),
                    "SSH_ASKPASS_REQUIRE": "force",
                    "HOMELAB_AGENT_SSH_PASSWORD": config.ssh_password or "",
                }
            )
            return self._password_command_runner(
                self._build_ssh_command(config, remote_command),
                env,
                subprocess.DEVNULL,
            )
        finally:
            askpass_path.unlink(missing_ok=True)

    def _write_askpass_script(self) -> Path:
        with tempfile.NamedTemporaryFile("w", delete=False, prefix="homelab-agent-askpass-") as script:
            script.write('#!/bin/sh\nprintf "%s\\n" "$HOMELAB_AGENT_SSH_PASSWORD"\n')
        askpass_path = Path(script.name)
        askpass_path.chmod(0o700)
        return askpass_path

    def read_system_info(self, config: TargetConfig) -> dict:
        hostname = self._run_ssh(config, "hostname").strip()
        kernel = self._run_ssh(config, "uname -a").strip()
        return {
            "hostname": hostname,
            "kernel": kernel,
        }

    def list_containers(self, config: TargetConfig, all_containers: bool = False) -> List[dict]:
        remote_command = "docker ps --format '{{json .}}'"
        if all_containers:
            remote_command = "docker ps -a --format '{{json .}}'"
        output = self._run_ssh(config, remote_command)
        containers = []
        for line in output.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            containers.append(
                {
                    "id": payload["ID"],
                    "name": payload["Names"],
                    "image": payload["Image"],
                    "state": payload["State"],
                    "status": payload["Status"],
                }
            )
        return containers

    def configure_docker_registry_mirror(
        self,
        config: TargetConfig,
        mirror_url: str,
        restart_docker: bool = False,
    ) -> dict:
        if not mirror_url.startswith("https://"):
            raise ValueError("mirror_url must start with https://")
        if any(character.isspace() for character in mirror_url):
            raise ValueError("mirror_url must not contain whitespace")

        output = self._run_ssh(
            config,
            self._build_configure_docker_registry_mirror_command(mirror_url, restart_docker),
        )
        return self._parse_key_value_output(output)

    def configure_community_applications_proxy(
        self,
        config: TargetConfig,
        proxy_host: str,
        proxy_port: int,
        tunnel: bool = True,
    ) -> dict:
        if not proxy_host:
            raise ValueError("proxy_host is required")
        if proxy_port < 1 or proxy_port > 65535:
            raise ValueError("proxy_port must be between 1 and 65535")

        output = self._run_ssh(
            config,
            self._build_configure_community_applications_proxy_command(proxy_host, proxy_port, tunnel),
        )
        return self._parse_key_value_output(output)

    def configure_docker_daemon_proxy(
        self,
        config: TargetConfig,
        proxy_url: str,
        no_proxy: str,
        restart_docker: bool = False,
    ) -> dict:
        if not (proxy_url.startswith("http://") or proxy_url.startswith("https://")):
            raise ValueError("proxy_url must start with http:// or https://")
        if "\n" in proxy_url or "\n" in no_proxy:
            raise ValueError("proxy_url and no_proxy must not contain newlines")

        output = self._run_ssh(
            config,
            self._build_configure_docker_daemon_proxy_command(proxy_url, no_proxy, restart_docker),
        )
        return self._parse_key_value_output(output)

    def install_boot_network_acceleration_hook(
        self,
        config: TargetConfig,
        mirror_url: str,
        proxy_host: str,
        proxy_port: int,
        no_proxy: str,
    ) -> dict:
        if not mirror_url.startswith("https://"):
            raise ValueError("mirror_url must start with https://")
        if not proxy_host:
            raise ValueError("proxy_host is required")
        if proxy_port < 1 or proxy_port > 65535:
            raise ValueError("proxy_port must be between 1 and 65535")

        output = self._run_ssh(
            config,
            self._build_install_boot_network_acceleration_hook_command(
                mirror_url=mirror_url,
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                no_proxy=no_proxy,
            ),
        )
        return self._parse_key_value_output(output)

    def configure_webui_proxy(
        self,
        config: TargetConfig,
        proxy_url: str,
        no_proxy: str,
        restart_webui: bool = True,
    ) -> dict:
        if not (proxy_url.startswith("http://") or proxy_url.startswith("https://")):
            raise ValueError("proxy_url must start with http:// or https://")
        if "\n" in proxy_url or "\n" in no_proxy:
            raise ValueError("proxy_url and no_proxy must not contain newlines")

        output = self._run_ssh(
            config,
            self._build_configure_webui_proxy_command(proxy_url, no_proxy, restart_webui),
        )
        return self._parse_key_value_output(output)

    def backup_boot_config_to_local(
        self,
        config: TargetConfig,
        local_backup_root: Union[Path, str],
        timestamp: Optional[str] = None,
    ) -> dict:
        backup_timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = Path(local_backup_root).expanduser().resolve()
        destination = backup_root / "unraid-{0}".format(backup_timestamp)
        destination.mkdir(parents=True, exist_ok=True)
        remote_path = "/boot/config"

        command = self._build_scp_pull_command(config, remote_path, destination / "config")
        if config.ssh_password is not None:
            self._run_scp_with_password(config, command)
        else:
            self._command_runner(command)

        return {
            "remote_path": remote_path,
            "local_backup_path": str(destination),
            "backup_timestamp": backup_timestamp,
        }

    def _build_configure_community_applications_proxy_command(
        self,
        proxy_host: str,
        proxy_port: int,
        tunnel: bool,
    ) -> str:
        tunnel_value = "1" if tunnel else "0"
        return """set -eu
cfg=/boot/config/plugins/community.applications/proxy.cfg
proxy={proxy_host}
port={proxy_port}
tunnel={tunnel}
mkdir -p "$(dirname "$cfg")"
backup=""
if [ -f "$cfg" ]; then
  backup="${{cfg}}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$cfg" "$backup"
fi
printf 'proxy="%s"\\nport="%s"\\ntunnel="%s"\\n' "$proxy" "$port" "$tunnel" > "$cfg"
echo "config_path=$cfg"
echo "backup_path=$backup"
echo "proxy_url=http://$proxy:$port"
echo "tunnel=$tunnel"
""".format(
            proxy_host=shlex.quote(proxy_host),
            proxy_port=proxy_port,
            tunnel=tunnel_value,
        )

    def _build_configure_docker_daemon_proxy_command(
        self,
        proxy_url: str,
        no_proxy: str,
        restart_docker: bool,
    ) -> str:
        restart_value = "true" if restart_docker else "false"
        return """set -eu
cfg=/boot/config/docker.cfg
proxy_url={proxy_url}
no_proxy={no_proxy}
restart_docker={restart_docker}
begin="# homelab-agent docker daemon proxy begin"
end="# homelab-agent docker daemon proxy end"
backup="${{cfg}}.bak.$(date +%Y%m%d%H%M%S)"
tmp="${{cfg}}.tmp.$$"
if [ ! -f "$cfg" ]; then
  echo "error=missing_docker_config"
  echo "config_path=$cfg"
  exit 2
fi
cp "$cfg" "$backup"
awk -v begin="$begin" -v end="$end" '
  $0 == begin {{ skip = 1; next }}
  $0 == end {{ skip = 0; next }}
  skip == 0 {{ print }}
' "$cfg" > "$tmp"
cat >> "$tmp" <<'EOF'
# homelab-agent docker daemon proxy begin
HTTP_PROXY="{proxy_url_literal}"
HTTPS_PROXY="{proxy_url_literal}"
http_proxy="{proxy_url_literal}"
https_proxy="{proxy_url_literal}"
NO_PROXY="{no_proxy_literal}"
no_proxy="{no_proxy_literal}"
export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy
# homelab-agent docker daemon proxy end
EOF
mv "$tmp" "$cfg"
echo "config_path=$cfg"
echo "backup_path=$backup"
echo "proxy_url=$proxy_url"
echo "restart_docker=$restart_docker"
if [ "$restart_docker" = "true" ]; then
  /etc/rc.d/rc.docker restart >/tmp/homelab-agent-docker-restart.log 2>&1
  echo "docker_restarted=true"
else
  echo "docker_restarted=false"
fi
""".format(
            proxy_url=shlex.quote(proxy_url),
            no_proxy=shlex.quote(no_proxy),
            restart_docker=restart_value,
            proxy_url_literal=proxy_url,
            no_proxy_literal=no_proxy,
        )

    def _build_install_boot_network_acceleration_hook_command(
        self,
        mirror_url: str,
        proxy_host: str,
        proxy_port: int,
        no_proxy: str,
    ) -> str:
        proxy_url = "http://{0}:{1}".format(proxy_host, proxy_port)
        return f"""set -eu
go=/boot/config/go
script=/boot/config/plugins/homelab-agent/apply-network-acceleration.sh
mkdir -p "$(dirname "$script")"
go_backup="${{go}}.bak.$(date +%Y%m%d%H%M%S)"
script_backup=""
if [ -f "$go" ]; then
  cp "$go" "$go_backup"
else
  printf '#!/bin/bash\\n/usr/local/sbin/emhttp\\n' > "$go"
fi
if [ -f "$script" ]; then
  script_backup="${{script}}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$script" "$script_backup"
fi
cat > "$script" <<'EOF'
#!/bin/bash
set -eu
cfg=/boot/config/docker.cfg
mirror_url="{mirror_url}"
proxy_url="{proxy_url}"
no_proxy="{no_proxy}"
ca_cfg=/boot/config/plugins/community.applications/proxy.cfg

if [ -f "$cfg" ]; then
  current="$(grep '^DOCKER_OPTS=' "$cfg" || true)"
  opts=""
  if [ -n "$current" ]; then
    opts="$(printf '%s\\n' "$current" | sed -E 's/^DOCKER_OPTS="//; s/"$//')"
    opts="$(printf '%s\\n' "$opts" | sed -E 's#(^| )--registry-mirror(=| )[^ ]+##g' | xargs)"
  fi
  new_opts="--registry-mirror=$mirror_url"
  if [ -n "$opts" ]; then
    new_opts="$opts $new_opts"
  fi
  tmp="${{cfg}}.tmp.$$"
  awk -v replacement="DOCKER_OPTS=\\"$new_opts\\"" '
    BEGIN {{ done = 0 }}
    /^DOCKER_OPTS=/ {{ print replacement; done = 1; next }}
    {{ print }}
    END {{ if (done == 0) print replacement }}
  ' "$cfg" > "$tmp"
  mv "$tmp" "$cfg"

  begin="# homelab-agent docker daemon proxy begin"
  end="# homelab-agent docker daemon proxy end"
  tmp="${{cfg}}.tmp.$$"
  awk -v begin="$begin" -v end="$end" '
    $0 == begin {{ skip = 1; next }}
    $0 == end {{ skip = 0; next }}
    skip == 0 {{ print }}
  ' "$cfg" > "$tmp"
  cat >> "$tmp" <<'PROXY_EOF'
# homelab-agent docker daemon proxy begin
HTTP_PROXY="{proxy_url}"
HTTPS_PROXY="{proxy_url}"
http_proxy="{proxy_url}"
https_proxy="{proxy_url}"
NO_PROXY="{no_proxy}"
no_proxy="{no_proxy}"
export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy
# homelab-agent docker daemon proxy end
PROXY_EOF
  mv "$tmp" "$cfg"
fi

mkdir -p "$(dirname "$ca_cfg")"
printf 'proxy="%s"\\nport="%s"\\ntunnel="%s"\\n' "{proxy_host}" "{proxy_port}" "1" > "$ca_cfg"
EOF
chmod 755 "$script"
begin="# homelab-agent boot hook begin"
end="# homelab-agent boot hook end"
tmp="${{go}}.tmp.$$"
awk -v begin="$begin" -v end="$end" '
  $0 == begin {{ skip = 1; next }}
  $0 == end {{ skip = 0; next }}
  skip == 0 {{ print }}
' "$go" > "$tmp"
cat >> "$tmp" <<'HOOK_EOF'
# homelab-agent boot hook begin
/boot/config/plugins/homelab-agent/apply-network-acceleration.sh >>/var/log/homelab-agent-startup.log 2>&1 || true
# homelab-agent boot hook end
HOOK_EOF
mv "$tmp" "$go"
chmod 755 "$go"
echo "go_path=$go"
echo "go_backup_path=$go_backup"
echo "script_path=$script"
echo "script_backup_path=$script_backup"
echo "hook_installed=true"
"""

    def _build_configure_webui_proxy_command(
        self,
        proxy_url: str,
        no_proxy: str,
        restart_webui: bool,
    ) -> str:
        restart_value = "true" if restart_webui else "false"
        return """set -eu
go=/boot/config/go
env_file=/boot/config/plugins/homelab-agent/unraid-webui-proxy.env
script=/boot/config/plugins/homelab-agent/apply-webui-proxy.sh
proxy_url={proxy_url}
no_proxy={no_proxy}
restart_webui={restart_webui}
mkdir -p "$(dirname "$env_file")"
env_backup=""
script_backup=""
go_backup=""
if [ -f "$env_file" ]; then
  env_backup="${{env_file}}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$env_file" "$env_backup"
fi
if [ -f "$script" ]; then
  script_backup="${{script}}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$script" "$script_backup"
fi
if [ -f "$go" ]; then
  go_backup="${{go}}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$go" "$go_backup"
else
  printf '#!/bin/bash\\n/usr/local/sbin/emhttp\\n' > "$go"
fi
cat > "$env_file" <<'EOF'
HTTP_PROXY="{proxy_url_literal}"
HTTPS_PROXY="{proxy_url_literal}"
http_proxy="{proxy_url_literal}"
https_proxy="{proxy_url_literal}"
NO_PROXY="{no_proxy_literal}"
no_proxy="{no_proxy_literal}"
export HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy
EOF
cat > "$script" <<'EOF'
#!/bin/bash
set -eu
env_file=/boot/config/plugins/homelab-agent/unraid-webui-proxy.env
php_fpm_pool=/etc/php-fpm.d/www.conf
docker_update_php=/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerUpdate.php
if [ -f "$env_file" ]; then
  . "$env_file"
fi
if [ -f "$php_fpm_pool" ]; then
  begin='; homelab-agent webui proxy begin'
  end='; homelab-agent webui proxy end'
  tmp="${{php_fpm_pool}}.tmp.$$"
  awk -v begin="$begin" -v end="$end" '
    $0 == begin {{ skip = 1; next }}
    $0 == end {{ skip = 0; next }}
    skip == 0 {{ print }}
  ' "$php_fpm_pool" > "$tmp"
  cat >> "$tmp" <<'PHP_FPM_EOF'
; homelab-agent webui proxy begin
clear_env = no
env[HTTP_PROXY] = $HTTP_PROXY
env[HTTPS_PROXY] = $HTTPS_PROXY
env[NO_PROXY] = $NO_PROXY
env[http_proxy] = $http_proxy
env[https_proxy] = $https_proxy
env[no_proxy] = $no_proxy
; homelab-agent webui proxy end
PHP_FPM_EOF
  mv "$tmp" "$php_fpm_pool"
fi
if [ -f "$docker_update_php" ]; then
  php <<'PHP'
<?php
$path = "/usr/local/emhttp/plugins/dynamix.docker.manager/include/DockerUpdate.php";
$text = file_get_contents($path);
$begin = "// homelab-agent webui proxy begin";
$end = "// homelab-agent webui proxy end";
while (($start = strpos($text, $begin)) !== false && ($finish = strpos($text, $end, $start)) !== false) {{
    $finish += strlen($end);
    $suffix = substr($text, $finish, 2);
    if ($suffix === "\r\n") {{
        $finish += 2;
    }} elseif (substr($suffix, 0, 1) === "\n") {{
        $finish += 1;
    }}
    $text = substr($text, 0, $start) . substr($text, $finish);
}}
$block = <<<'PATCH'
// homelab-agent webui proxy begin
$proxyEnvFile = '/boot/config/plugins/homelab-agent/unraid-webui-proxy.env';
if (is_readable($proxyEnvFile)) {{
    foreach (file($proxyEnvFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {{
        if ($line === '' || strpos($line, 'export ') === 0) {{
            continue;
        }}
        $parts = explode('=', $line, 2);
        if (count($parts) !== 2 || $parts[0] === '') {{
            continue;
        }}
        $value = trim($parts[1], chr(34) . "'");
        putenv($parts[0] . '=' . $value);
        $_ENV[$parts[0]] = $value;
        $_SERVER[$parts[0]] = $value;
    }}
}}
// homelab-agent webui proxy end
PATCH;
$needle = "\\$docroot ??= (\\$_SERVER['DOCUMENT_ROOT'] ?: '/usr/local/emhttp');";
$pos = strpos($text, $needle);
if ($pos !== false) {{
    $text = substr($text, 0, $pos) . $block . "\n" . $needle . substr($text, $pos + strlen($needle));
    file_put_contents($path, $text);
}}
?>
PHP
fi
/etc/rc.d/rc.php-fpm restart >/tmp/homelab-agent-webui-php-fpm.log 2>&1 || true
/etc/rc.d/rc.nginx restart >/tmp/homelab-agent-webui-nginx.log 2>&1 || true
EOF
chmod 755 "$script"
begin="# homelab-agent webui proxy begin"
end="# homelab-agent webui proxy end"
tmp="${{go}}.tmp.$$"
awk -v begin="$begin" -v end="$end" '
  $0 == begin {{ skip = 1; next }}
  $0 == end {{ skip = 0; next }}
  skip == 0 {{ print }}
' "$go" > "$tmp"
cat >> "$tmp" <<'HOOK_EOF'
# homelab-agent webui proxy begin
/bin/bash /boot/config/plugins/homelab-agent/apply-webui-proxy.sh >>/var/log/homelab-agent-startup.log 2>&1 || true
# homelab-agent webui proxy end
HOOK_EOF
mv "$tmp" "$go"
chmod 755 "$go"
echo "go_path=$go"
echo "go_backup_path=$go_backup"
echo "env_path=$env_file"
echo "env_backup_path=$env_backup"
echo "script_path=$script"
echo "script_backup_path=$script_backup"
echo "proxy_url=$proxy_url"
echo "restart_webui=$restart_webui"
if [ "$restart_webui" = "true" ]; then
  /bin/bash "$script"
  echo "webui_restarted=true"
else
  echo "webui_restarted=false"
fi
""".format(
            proxy_url=shlex.quote(proxy_url),
            no_proxy=shlex.quote(no_proxy),
            restart_webui=restart_value,
            proxy_url_literal=proxy_url,
            no_proxy_literal=no_proxy,
        )

    def _build_scp_pull_command(self, config: TargetConfig, remote_path: str, local_path: Path) -> list[str]:
        command = [
            "scp",
            "-r",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
        ]
        if config.ssh_identity_file is not None:
            command.extend(["-i", str(config.ssh_identity_file)])
        command.append("{0}@{1}:{2}".format(config.ssh_username, config.ssh_host, remote_path))
        command.append(str(local_path))
        return command

    def _run_scp_with_password(self, config: TargetConfig, command: list[str]) -> str:
        askpass_path = self._write_askpass_script()
        try:
            env = os.environ.copy()
            env.update(
                {
                    "DISPLAY": "homelab-agent:0",
                    "SSH_ASKPASS": str(askpass_path),
                    "SSH_ASKPASS_REQUIRE": "force",
                    "HOMELAB_AGENT_SSH_PASSWORD": config.ssh_password or "",
                }
            )
            return self._password_command_runner(command, env, subprocess.DEVNULL)
        finally:
            askpass_path.unlink(missing_ok=True)

    def _build_configure_docker_registry_mirror_command(self, mirror_url: str, restart_docker: bool) -> str:
        restart_value = "true" if restart_docker else "false"
        return """set -eu
cfg=/boot/config/docker.cfg
mirror={mirror_url}
restart_docker={restart_docker}
backup="${{cfg}}.bak.$(date +%Y%m%d%H%M%S)"
tmp="${{cfg}}.tmp.$$"
if [ ! -f "$cfg" ]; then
  echo "error=missing_docker_config"
  echo "config_path=$cfg"
  exit 2
fi
cp "$cfg" "$backup"
current="$(grep '^DOCKER_OPTS=' "$cfg" || true)"
opts=""
if [ -n "$current" ]; then
  opts="$(printf '%s\\n' "$current" | sed -E 's/^DOCKER_OPTS="//; s/"$//')"
  opts="$(printf '%s\\n' "$opts" | sed -E 's#(^| )--registry-mirror(=| )[^ ]+##g' | xargs)"
fi
new_opts="--registry-mirror=$mirror"
if [ -n "$opts" ]; then
  new_opts="$opts $new_opts"
fi
awk -v replacement="DOCKER_OPTS=\\"$new_opts\\"" '
  BEGIN {{ done = 0 }}
  /^DOCKER_OPTS=/ {{ print replacement; done = 1; next }}
  {{ print }}
  END {{ if (done == 0) print replacement }}
' "$cfg" > "$tmp"
mv "$tmp" "$cfg"
echo "config_path=$cfg"
echo "backup_path=$backup"
echo "mirror_url=$mirror"
echo "restart_docker=$restart_docker"
if [ "$restart_docker" = "true" ]; then
  /etc/rc.d/rc.docker restart >/tmp/homelab-agent-docker-restart.log 2>&1
  echo "docker_restarted=true"
else
  echo "docker_restarted=false"
fi
""".format(
            mirror_url=shlex.quote(mirror_url),
            restart_docker=restart_value,
        )

    def _parse_key_value_output(self, output: str) -> dict:
        payload = {}
        for line in output.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            payload[key] = value
        return payload
