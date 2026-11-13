"""GitHub 공개 저장소의 언어 비중을 집계해 langs.svg 카드를 만든다.
사용: GITHUB_TOKEN=... python scripts/langs.py
포크 제외, HIDE 목록 제외, 코드 용량(bytes) 기준.
"""
import json, os, sys, urllib.request

USER = "masterjms"
HIDE = {"HTML", "CSS", "Jupyter Notebook", "SCSS"}
TOP = 6
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "langs.svg")

QUERY = """
{ user(login:"%s"){ repositories(first:100, ownerAffiliations:OWNER, isFork:false){
  nodes{ name languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } } } }
""" % USER

token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not token:
    sys.exit("GITHUB_TOKEN 환경변수가 필요합니다.")
req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": QUERY}).encode(),
                             headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                                      "User-Agent": "langs-card"})
data = json.load(urllib.request.urlopen(req))
if "errors" in data:
    sys.exit(data["errors"])

total, colors = {}, {}
for repo in data["data"]["user"]["repositories"]["nodes"]:
    for e in repo["languages"]["edges"]:
        n = e["node"]["name"]
        if n in HIDE:
            continue
        total[n] = total.get(n, 0) + e["size"]
        colors[n] = e["node"]["color"] or "#8b949e"
s = sum(total.values()) or 1
langs = sorted(total.items(), key=lambda kv: -kv[1])[:TOP]
langs = [(n, 100 * v / s) for n, v in langs]
rest = 100 - sum(p for _, p in langs)

W, PAD = 495, 25
BAR_Y, BAR_H, BAR_W = 55, 8, W - 2 * PAD
rows = (len(langs) + 1) // 2
H = BAR_Y + BAR_H + 22 + rows * 22 + 18

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="Most used languages">',
       '<style>.h{font:600 18px "Segoe UI",Ubuntu,sans-serif;fill:#2f80ed}.l{font:400 11px "Segoe UI",Ubuntu,sans-serif;fill:#434d58}.p{fill:#434d58;font:600 11px "Segoe UI",Ubuntu,sans-serif}</style>',
       f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="4.5" fill="#fffefe" stroke="#e4e2e2"/>',
       f'<text x="{PAD}" y="35" class="h">Most Used Languages</text>']
x = PAD
svg.append(f'<rect x="{PAD}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" rx="4" fill="#e4e2e2"/>')
for n, p in langs:
    w = BAR_W * p / 100
    svg.append(f'<rect x="{x:.1f}" y="{BAR_Y}" width="{w:.1f}" height="{BAR_H}" fill="{colors[n]}"/>')
    x += w
# 둥근 모서리를 위한 마스크 대신 양 끝 덮개
svg.append(f'<rect x="{PAD}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" rx="4" fill="none" stroke="#fffefe" stroke-width="2"/>')
y0 = BAR_Y + BAR_H + 26
col_w = BAR_W / 2
for i, (n, p) in enumerate(langs):
    cx = PAD + (i % 2) * col_w
    cy = y0 + (i // 2) * 22
    svg.append(f'<circle cx="{cx+5}" cy="{cy-4}" r="5" fill="{colors[n]}"/>')
    svg.append(f'<text x="{cx+16}" y="{cy}" class="l">{n}</text>')
    svg.append(f'<text x="{cx+16+len(n)*6.6+6:.0f}" y="{cy}" class="p">{p:.1f}%</text>')
svg.append("</svg>")
open(OUT, "w", encoding="utf-8").write("\n".join(svg))
print("wrote", OUT, [(n, round(p, 1)) for n, p in langs], "other", round(rest, 1))
