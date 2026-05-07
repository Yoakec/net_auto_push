import time
import logging
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

from backend.config import SSH_TIMEOUT
from backend.routes.inventory import devices

logger = logging.getLogger(__name__)


def run_device_commands(device_ip: str, commands: list[str]) -> dict:
    """Connect to a device and execute commands sequentially. Returns result dict."""
    dev = next((d for d in devices if d.ip == device_ip), None)
    if not dev:
        return {"status": "error", "error": f"Device {device_ip} not found in inventory"}

    device_params = {
        "device_type": dev.type.lower() if dev.type.lower() in ["huawei", "cisco_ios"] else "huawei",
        "host": dev.ip,
        "username": dev.username,
        "password": dev.password,
        "port": dev.port,
        "timeout": SSH_TIMEOUT,
    }

    conn = None
    outputs = {}
    errors = []
    start_time = time.time()

    try:
        conn = ConnectHandler(**device_params)

        # Suppress pagination
        try:
            conn.send_command("screen-length 0 disable", expect_string=r"[>#\]]", read_timeout=5)
        except Exception:
            pass  # silently ignore if pagination disable fails

        for cmd in commands:
            try:
                output = conn.send_command(cmd, read_timeout=30)
                outputs[cmd] = output
                if "Error:" in output or "Unrecognized command" in output:
                    errors.append({"command": cmd, "error": output})
                    break  # Fail-fast
            except Exception as e:
                errors.append({"command": cmd, "error": str(e)})
                break  # Fail-fast

    except NetmikoAuthenticationException:
        errors.append({"command": "", "error": "Auth failed"})
    except NetmikoTimeoutException:
        errors.append({"command": "", "error": "Connection timeout"})
    except Exception as e:
        errors.append({"command": "", "error": str(e)})
    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass

    duration_ms = int((time.time() - start_time) * 1000)

    if errors:
        return {
            "status": "failed",
            "outputs": outputs,
            "error": errors[-1]["error"],
            "duration_ms": duration_ms,
        }

    return {
        "status": "success",
        "outputs": outputs,
        "duration_ms": duration_ms,
    }
