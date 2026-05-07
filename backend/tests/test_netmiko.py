"""
独立验证脚本: 读取 /data/ CSV，连接第一台设备，执行 show arp，打印回显

Usage: python -m backend.tests.test_netmiko
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from backend.routes.inventory import load_devices_on_startup, devices
from backend.executor.device import run_device_commands


def main():
    load_devices_on_startup()
    if not devices:
        logger.error("No devices loaded from /data/ directory. Place CSV files in /data/.")
        return

    dev = devices[0]
    logger.info(f"Testing connection to {dev.ip} ({dev.type})...")

    result = run_device_commands(dev.ip, ["show arp"])

    if result["status"] == "success":
        logger.info(f"Success! Duration: {result['duration_ms']}ms")
        for cmd, output in result["outputs"].items():
            logger.info(f"\n{'='*60}\n  Command: {cmd}\n{'='*60}\n{output}\n{'='*60}")
    else:
        logger.error(f"Failed: {result['error']}")

if __name__ == "__main__":
    main()
