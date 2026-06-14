#!/usr/bin/env python3
"""AlphaSift v8: 1条HTML消息推送，完整10只股票"""
import json, os, sys, time, glob, requests
from datetime import datetime

TOKEN = "7836f927b1a449868d7875a0b4c808e3"
SDIR  = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(SDIR, "reports"), exist_ok=True)

def latest_json():
    files = sorted(glob.glob(os.path.join(SDIR, "data", "runs", "*.json")))
    if not files:
        files = sorted(glob.glob(os.path.join(SDIR, "data", "*.json")))
    if not files:
        print("[ERROR] 无数据")
        sys.exit(1)
    f = max(files, key=os.path.getmtime)
    return json.load(open(f, encoding="utf-8"))

def picks(d):
    for k in ["picks", "llm_ranked", "candidates"]:
        if k in d and d[k]:
            return d[k]
    return []

def esc(t):
    s = str(t)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fmt_concentration(raw):
    """将原始集中度数据解析为可读HTML"""
    if not raw:
        return ""
    items = raw if isinstance(raw, list) else [raw]
    lines = []
    for item in items:
        if not isinstance(item, str):
            continue
        # 解析: "Portfolio concentration bucket=周期: penalized=13, codes=600988:有色金属(-5.0),..."
        try:
            # 提取 bucket 名称
            bucket = "未知"
            penalized = 0
            codes = []
            m = item.find("bucket=")
            if m >= 0:
                rest = item[m+7:]
                colon = rest.find(":")
                if colon > 0:
                    bucket = rest[:colon].strip()
                    rest2 = rest[colon+1:]
                    # penalized
                    pm = rest2.find("penalized=")
                    if pm >= 0:
                        pstr = rest2[pm+10:]
                        penalized = int(''.join(c for c in pstr[:4] if c.isdigit()))
                    # codes
                    cm = rest2.find("codes=")
                    if cm >= 0:
                        cstr = rest2[cm+6:].rstrip(",")
                        # 解析每个 code:name(-score)
                        parts = cstr.split(",")
                        for p in parts:
                            p = p.strip()
                            if not p or p.startswith("+"):
                                continue
                            # 格式: 600988:有色金属(-5.0)
                            colon2 = p.find(":")
                            if colon2 > 0:
                                name = p[colon2+1:].strip()
                                codes.append(name)

            # 只取前3个代码，其余省略
            display_codes = ", ".join(codes[:3])
            if len(codes) > 3:
                display_codes += f" 等{len(codes)}只"

            penalty_color = "#C62828" if penalized >= 10 else "#E65100" if penalized >= 5 else "#F57C00"
            lines.append(f'<div style="margin:3px 0"><b style="color:{penalty_color}">{esc(bucket)}</b>'
                         f' <span style="color:#999">(扣{penalized}分)</span>: {esc(display_codes)}</div>')
        except Exception:
            # 解析失败就截断显示
            lines.append(f'<div>{esc(item[:80])}</div>')
    return "".join(lines)

def card(s, i):
    n = esc(s.get("name", ""))
    c = esc(s.get("code", ""))
    sc = s.get("final_score", s.get("llm_score", 0))
    ch = s.get("change_pct", 0)
    vr = s.get("volume_ratio", 0)
    am = s.get("amount", 0) or 0
    pe = s.get("pe_ratio", 0) or 0
    pb = s.get("pb_ratio", 0) or 0
    ind = esc(s.get("llm_sector", s.get("industry", "")))
    th = esc(s.get("llm_theme", ""))
    ts = esc(s.get("llm_thesis", ""))
    sf = esc(s.get("llm_style_fit", ""))
    ct = s.get("llm_catalysts", []) or []
    rk = s.get("llm_risks", []) or []
    wt = s.get("llm_watch_items", []) or []
    iv = s.get("llm_invalidators", []) or []
    fc = s.get("factor_scores", {}) or {}
    pa = s.get("post_analysis_tags", []) or []
    rl = esc(s.get("risk_level", ""))
    rs = esc(s.get("risk_summary", ""))

    h = ""
    bg = "#FCE4EC" if i <= 3 else "#fff"
    rk_cls = "t" if i <= 3 else "n"
    h += '<div class="c" style="background:' + bg + '">'
    # 第1行：排名 + 名字 + 标签 + 评分
    h += '<div class="r">'
    h += '<b class="' + rk_cls + '">' + str(i) + '</b>'
    h += '<span class="nm">' + n + '</span><span class="cd">(' + c + ')</span>'
    if ind:
        h += '<span class="tg p">' + ind + '</span>'
    if th:
        h += '<span class="tg o">' + th + '</span>'
    h += '<span class="sc">' + str(round(sc)) + '</span></div>'

    # 第2行：指标
    chs = "{:+.2f}%".format(ch)
    vrs = "{:.2f}".format(vr)
    ams = "{:.1f}亿".format(am / 1e8) if am else "-"
    pes = "{:.1f}".format(pe) if pe else "-"
    h += '<div class="row">'
    for lb, v, co in [("涨幅", chs, "#C62828"), ("量比", vrs, "#333"), ("金额", ams, "#1565C0"), ("PE", pes, "#333")]:
        h += "<div><i>" + lb + "</i><b style=color:" + co + ">" + v + "</b></div>"
    h += "</div>"

    # 理由
    if ts:
        h += "<div class=ln><em>&#128196;</em> " + ts[:80] + "</div>"

    # 风格+催化
    parts = []
    if sf:
        parts.append("<b style=color:#9C27B0>风格:</b> " + sf[:35])
    if ct:
        parts.append("<b style=color:#FF9800>催化:</b> " + " / ".join(esc(x)[:15] for x in ct[:2]))
    if parts:
        h += "<div class=ln>" + "<br>".join(parts) + "</div>"

    # 关注
    if wt:
        items = [esc(x)[:18] for x in wt[:2]]
        h += "<div class=ln g><em>&#128064;</em> " + " / ".join(items) + "</div>"

    # 风险+失效
    rp = []
    if rk:
        rp.append('<span class=rk>&#9888;&#65039; ' + " / ".join(esc(x)[:16] for x in rk[:2]) + "</span>")
    if iv:
        txt = esc(iv[0])[:20] if isinstance(iv, list) and iv else esc(iv)[:20]
        rp.append('<span class=iv>&#128680; ' + txt + "</span>")
    if rp:
        h += "<div class=ln>" + " ".join(rp) + "</div>"

    # 因子评分
    if fc:
        fl = []
        for lb2, k2, cl in [("价值","value","#4CAF50"),("流动","liquidity","#2196F3"),
                             ("动量","momentum","#FF9800"),("活跃","activity","#00BCD4"),
                             ("稳定","stability","#8BC34A"),("市值","size","#FF5722")]:
            v2 = min(int(fc.get(k2, 0) or 0), 100)
            fl.append(lb2 + "<b style=color:" + cl + ">" + str(v2) + "</b>")
        h += "<div class=fn>" + " | ".join(fl) + "</div>"

    # 底部
    tail = []
    if pa:
        tail.append(",".join(str(x) for x in pa[:2]))
    if rl:
        tail.append("风险:" + rl)
    if rs:
        tail.append("评估:" + rs[:22])
    if tail:
        h += "<div class=bt>" + " | ".join(tail) + "</div>"
    h += "</div>"
    return h

def build_html(d):
    ps = picks(d)
    if not ps:
        return ""
    mv = d.get("llm_market_view", "")
    sl = d.get("llm_selection_logic", "")
    pr = d.get("llm_portfolio_risk", "")
    cc = d.get("portfolio_concentration_notes", "")
    src = d.get("snapshot_source", "")
    st = d.get("strategy", "capital_heat")
    ver = d.get("strategy_version", "v1.1")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n = d.get("after_filter_count", len(ps))

    CSS = (
        ".w{max-width:640px;margin:0 auto;font-family:-apple-system,PingFang SC,sans-serif;background:#f6f6f6;color:#333}"
        ".hd{background:linear-gradient(135deg,#E91E63,#9C27B0);color:#fff;padding:12px 14px;border-radius:8px 8px 0 0}"
        ".hd b{font-size:16px}.hd span{font-size:11px;opacity:.85}"
        ".mv{margin:8px 12px;padding:10px 13px;background:#FFFDE7;border-left:3px solid #E91E63;font-size:12.5px;line-height:1.7}"
        ".sl{margin:6px 12px;padding:7px 12px;background:#F3E5F5;font-size:11.5px;line-height:1.65;border-left:3px solid #9C27B0;color:#555}"
        ".tt{background:#E91E63;color:#fff;padding:7px 14px;font-size:13px;font-weight:700}"
        ".c{margin:6px 10px;background:#fff;border-radius:8px;border:1px solid #eee;overflow:hidden}"
        ".r{display:flex;align-items:center;padding:8px 10px}"
        ".t,.n{width:22px;height:22px;line-height:22px;text-align:center;border-radius:50%;color:#fff;font-size:11px;font-weight:700;flex-shrink:0;margin-right:6px}"
        ".t{background:#C62828}.n{background:#999}"
        ".nm{font-size:14px;font-weight:700;margin-right:2px}"
        ".cd{font-size:11.5px;color:#aaa;margin-right:4px}"
        ".tg{font-size:10px;padding:2px 6px;border-radius:3px;margin-left:4px}"
        ".tg.p{background:#F3E5F5;color:#9C27B0}.tg.o{background:#FFF3E0;color:#FF9800}"
        ".sc{margin-left:auto;font-size:18px;font-weight:900;color:#E91E63;flex-shrink:0}"
        ".row{display:flex;border-top:1px solid #f5f5f5;border-bottom:1px solid #f5f5f5;padding:5px 0;font-size:11.5px}"
        ".row div{flex:1;text-align:center}.row i{display:block;color:#999;font-size:10px;font-style:normal}.row b{display:block;font-weight:700;font-size:12.5px}"
        ".ln{padding:3px 12px;font-size:11.5px;line-height:1.6;color:#444}.ln em{font-style:normal;margin-right:3px}.g{color:#2E7D32}"
        ".rk{display:inline-block;background:#FFEBEE;color:#C62828;font-size:10.5px;padding:2px 6px;border-radius:3px;margin-right:4px}"
        ".iv{display:inline-block;background:#FFF3E0;color:#E65100;font-size:10.5px;padding:2px 6px;border-radius:3px}"
        ".fn{padding:4px 12px 5px;border-top:1px dashed #eee;font-size:11px;color:#666}"
        ".bt{padding:4px 12px 6px;font-size:10.5px;color:#888;background:#fafafa;border-top:1px solid #f0f0f0}"
        ".pr{margin:6px 12px;padding:8px 11px;background:#FFF3E0;border-left:3px solid #FF9800;font-size:11.5px;line-height:1.6}"
        ".cc{margin:4px 12px;padding:7px 11px;background:#E3F2FD;border-left:3px solid #2196F3;font-size:11.5px;line-height:1.6;color:#444}"
        ".ds{margin:4px 12px;padding:5px 11px;font-size:10.5px;color:#bbb;background:#fafafa}"
        ".ft{text-align:center;font-size:10.5px;color:#bbb;padding:10px 0 12px;line-height:1.6}"
    )

    html_parts = ["<style>", CSS, "</style>",
                   '<div class=w>',
                   '<div class=hd><b>&#128200; AlphaSift 选股报告</b><br><span>' + st + "(" + ver + ") &middot; " + now + " &middot; " + str(n) + "只</span></div>"]
    if mv:
        html_parts.append('<div class=mv>' + esc(mv[:260]) + "</div>")
    if sl:
        html_parts.append('<div class=sl>&#128161; ' + esc(sl[:160]) + "</div>")
    html_parts.append('<div class=tt>&#128293; Top' + str(len(ps)) + " 推荐股票</div>")
    for idx, stock in enumerate(ps, 1):
        html_parts.append(card(stock, idx))
    if pr:
        html_parts.append('<div class=pr><b>&#9888;&#65039; 组合风险:</b> ' + esc(pr[:160]) + "</div>")
    if cc:
        html_parts.append('<div class=cc><b>&#128202; 板块集中度:</b><div style="margin-top:4px">' + fmt_concentration(cc) + "</div></div>")
    if src:
        html_parts.append('<div class=ds>' + '&#8505; ' + esc(str(src)[:130]) + "</div>")
    html_parts.append('<div class=ft>AlphaSift 自动生成 &middot; ' + now + "<br>仅供参考 不构成投资建议</div></div>")

    html = "".join(html_parts)
    return html

def push(title, content, tpl="html"):
    for attempt in range(3):
        try:
            r = requests.post("http://www.pushplus.plus/send",
                              json={"token": TOKEN, "title": title, "content": content, "template": tpl}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as ex:
            print(f"  [重试 {attempt+1}] {ex}")
            time.sleep(2)
    return None

def main():
    d = latest_json()
    ps = picks(d)
    st = d.get("strategy", "capital_heat")
    now = datetime.now().strftime("%Y%m%d_%H%M")
    if not ps:
        print("[ERROR] 无候选"); sys.exit(1)

    html = build_html(d)
    clen = len(html)
    print("[HTML] {} 字符 ({}只)".format(clen, len(ps)))

    if clen > 18500:
        print("[WARN] 超长！截断到18500...")
        html = html[:18500] + "<div class=ft>⚠️ 内容过长已截断</div></div>"
        clen = len(html)

    path = os.path.join(SDIR, "reports", "alphasift_html_{}.html".format(now))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("[保存] {}".format(path))

    title = "[AlphaSift] {} 信息图 {}".format(st, now[:8])
    print("[推送] ...")
    r = push(title, html, "html")
    print("[结果] {}".format(r))
    if r and r.get("code") == 200:
        print("✅ 完成！请查收微信")
    else:
        print("❌ 失败"); sys.exit(1)

if __name__ == "__main__":
    main()
