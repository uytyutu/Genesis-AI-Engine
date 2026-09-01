"""Real hardware discovery — no user questionnaire."""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GpuInfo:
    name: str | None = None
    vram_mib: float | None = None
    utilization_pct: float | None = None
    power_watts: float | None = None
    temperature_c: float | None = None
    driver: str | None = None
    cuda_available: bool = False
    opencl_hint: str = "unknown"


@dataclass
class HardwareSnapshot:
    timestamp: str
    os: str
    arch: str
    python: str
    cpu_name: str | None
    cpu_cores: int | None
    cpu_threads: int | None
    ram_gb: float | None
    gpu: GpuInfo = field(default_factory=GpuInfo)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _run(cmd: list[str], timeout: float = 12.0) -> str:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        return (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _ps(script: str) -> str:
    return _run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            script,
        ],
        timeout=20.0,
    )


def _detect_cpu() -> tuple[str | None, int | None, int | None]:
    out = _ps(
        "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name; "
        "(Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfCores; "
        "(Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfLogicalProcessors"
    )
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    name = lines[0] if lines else platform.processor() or None
    cores = threads = None
    if len(lines) >= 2 and lines[1].isdigit():
        cores = int(lines[1])
    if len(lines) >= 3 and lines[2].isdigit():
        threads = int(lines[2])
    return name, cores, threads


def _detect_ram_gb() -> float | None:
    out = _ps("[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)")
    for ln in out.splitlines():
        ln = ln.strip().replace(",", ".")
        try:
            return float(ln)
        except ValueError:
            continue
    return None


def _detect_nvidia() -> GpuInfo:
    gpu = GpuInfo()
    if not shutil.which("nvidia-smi"):
        gpu.opencl_hint = "nvidia-smi missing"
        return gpu
    q = _run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,utilization.gpu,power.draw,temperature.gpu,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    line = q.strip().splitlines()[0] if q.strip() else ""
    if not line:
        return gpu
    parts = [p.strip() for p in line.split(",")]
    if len(parts) >= 1:
        gpu.name = parts[0]
    try:
        if len(parts) >= 2:
            gpu.vram_mib = float(parts[1])
        if len(parts) >= 3:
            gpu.utilization_pct = float(parts[2])
        if len(parts) >= 4:
            gpu.power_watts = float(parts[3])
        if len(parts) >= 5:
            gpu.temperature_c = float(parts[4])
        if len(parts) >= 6:
            gpu.driver = parts[5]
    except ValueError:
        pass
    # CUDA runtime check (optional)
    try:
        import torch  # type: ignore

        gpu.cuda_available = bool(torch.cuda.is_available())
    except Exception:
        gpu.cuda_available = False
        gpu.opencl_hint = "torch not imported — CUDA flag false (GPU may still mine via external binary)"
    return gpu


def detect_hardware() -> HardwareSnapshot:
    notes: list[str] = []
    cpu_name, cores, threads = _detect_cpu()
    ram = _detect_ram_gb()
    gpu = _detect_nvidia()
    if not gpu.name:
        notes.append("No NVIDIA GPU via nvidia-smi — CPU-only path.")
    else:
        notes.append(f"GPU detected: {gpu.name}")
        if not gpu.cuda_available:
            notes.append("CUDA runtime not confirmed in-process — GPU adapters stay DISABLED until verified.")
    return HardwareSnapshot(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        os=f"{platform.system()} {platform.release()}",
        arch=platform.machine(),
        python=platform.python_version(),
        cpu_name=cpu_name,
        cpu_cores=cores,
        cpu_threads=threads,
        ram_gb=ram,
        gpu=gpu,
        notes=notes,
    )


if __name__ == "__main__":
    print(json.dumps(detect_hardware().to_dict(), indent=2, ensure_ascii=False))
