import json
import logging
import subprocess
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BashParams(BaseModel):
    command: str
    workdir: str | None = None
    timeout: int = 30


class BashTool:
    name = "Bash"
    description = "Execute a bash command or script and return its stdout, stderr, and exit code."
    params = BashParams

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.params.model_json_schema(),
            },
        }

    def __call__(
        self, command: str, workdir: str | None = None, timeout: int = 30
    ) -> str:
        params = self.params(command=command, workdir=workdir, timeout=timeout)
        logger.info(f"Running command: {params.command}")
        try:
            result = subprocess.run(
                params.command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=params.workdir,
                timeout=params.timeout,
            )
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            timeout_msg = f"Command timed out after {params.timeout}s"
            return json.dumps({"exit_code": -1, "stdout": out, "stderr": f"{err}\n{timeout_msg}"})

        output = [
            f"Exit code: {result.returncode}",
        ]
        output.append(f"Program exited with {result.returncode}.")
        if result.stderr:
            output.append("Stderr is enclosed below in `<stderr>` tags:")
            output.append(f"<stderr>\n{result.stderr.replace('<stderr>', '&lt;stderr&gt;').strip()}\n<stderr>")
        if result.stdout:
            output.append("Stdout is enclosed below in `<stdout>` tags:")
            output.append(f"<stdout>\n{result.stdout.replace('<stdout>', '&lt;stdout&gt;').strip()}<stdout>")
        else:
            output.append("There was no output.")
        return '\n'.join(output)
