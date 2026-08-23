from pathlib import Path

root = Path("/home/ubuntu/Genesis-AI-Engine")
p = root / "dashboard/frontend/app/components/FarmDashboard.tsx"
t = p.read_text(encoding="utf-8")
changed = False

if "MoneyHunterPanel" not in t:
    if 'import { FarmQueuesPanel } from "./FarmQueuesPanel";' in t:
        t = t.replace(
            'import { FarmQueuesPanel } from "./FarmQueuesPanel";\n',
            'import { FarmQueuesPanel } from "./FarmQueuesPanel";\n'
            'import { MoneyHunterPanel } from "./MoneyHunterPanel";\n',
        )
        changed = True
    elif 'import { ApiFarmPanel } from "./ApiFarmPanel";' in t:
        t = t.replace(
            'import { ApiFarmPanel } from "./ApiFarmPanel";\n',
            'import { ApiFarmPanel } from "./ApiFarmPanel";\n'
            'import { MoneyHunterPanel } from "./MoneyHunterPanel";\n',
        )
        changed = True

if "<MoneyHunterPanel" not in t:
    if "<FarmQueuesPanel compact />" in t:
        t = t.replace(
            "<FarmQueuesPanel compact />",
            "<FarmQueuesPanel compact />\n\n        <MoneyHunterPanel compact />",
        )
        changed = True
    elif "<ApiFarmPanel compact />" in t:
        t = t.replace(
            "<ApiFarmPanel compact />",
            "<MoneyHunterPanel compact />\n\n        <ApiFarmPanel compact />",
        )
        changed = True

if changed:
    p.write_text(t, encoding="utf-8")
    print("PATCHED")
else:
    print("NO_CHANGE_OR_ALREADY")

text = p.read_text(encoding="utf-8")
print("has_import", 'import { MoneyHunterPanel' in text)
print("has_mount", "<MoneyHunterPanel" in text)
for rel in (
    "lib/backendApiBase.ts",
    "components/ApiFarmPanel.tsx",
    "components/FarmQueuesPanel.tsx",
    "components/MoneyHunterPanel.tsx",
):
    print(rel, (root / "dashboard/frontend/app" / rel).exists())
