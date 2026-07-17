#!/usr/bin/env python3
import json
import re
import sys

# 1. O Claude Code manda o evento como JSON via stdin
data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

# 2. Padrões que violam a regra "nunca deletar dados"
padroes_perigosos = [
    r"\bDROP\s+TABLE\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\s+\w+\s*;",                          # sem WHERE
    r"\bDELETE\s+FROM\s+\w+\s+WHERE\s+(true|1\s*=\s*1)\s*;",  # WHERE trivial
]

bloqueado = any(re.search(p, command, re.IGNORECASE) for p in padroes_perigosos)

# 3. Resposta: JSON só é lido se sys.exit(0)
if bloqueado:
    resposta = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Comando SQL destrutivo bloqueado (LOOP_INSTRUCTIONS.md, "
                "seção 7: nunca deletar dados). Rode manualmente se tiver certeza."
            ),
        }
    }
    print(json.dumps(resposta))

sys.exit(0)