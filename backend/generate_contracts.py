"""Генерирует модули Python из общих gRPC-контрактов."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent / "contracts" / "src"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{root}",
            f"--python_out={root}",
            f"--pyi_out={root}",
            f"--grpc_python_out={root}",
            str(root / "olympiad_contracts" / "access.proto"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
