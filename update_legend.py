with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Lower Risk" in line and "Moderate Risk" in lines[i+1]:
        lines[i] = '      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#22C55E;margin-right:7px;vertical-align:middle;"></span>🟢 Safe (75-100)</span>\n'
        lines[i+1] = '      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#FACC15;margin-right:7px;vertical-align:middle;"></span>🟡 Moderate (50-74)</span>\n'
        lines[i+2] = '      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#F97316;margin-right:7px;vertical-align:middle;"></span>🟠 Risky (25-49)</span>\n'
        lines.insert(i+3, '      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#EF4444;margin-right:7px;vertical-align:middle;"></span>🔴 Unsafe (&lt;25)</span>\n')
        break

with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
