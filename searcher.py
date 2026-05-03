# -*- coding: utf-8 -*-
"""
搜索引擎模块 v5.1 — 政府权威网站全面覆盖 + 省市卫健委 + 微信公众号 + 14源并发
───────────────────────────────────────────────────────────────────────────────
新增数据源（v5.1）：
  ⑧ 微信公众号（搜狗微信搜索 + 百度公众号搜索）
  ⑨ 省级卫健委（百度/Bing site:gov.cn 卫生法规，覆盖省市区卫健委）

保留数据源（v5.0）：
  国家卫健委、全国人大、中国政府网、司法部、市场监管总局、
  应急管理部、中国疾控中心、法律图书馆、北大法宝、
  百度gov站内、Bing全网、搜狗

核心特性：
  - 14源 ThreadPoolExecutor 并发，速度 3-6x
  - TTL=10分钟内存缓存
  - Jaccard 标题去重（阈值0.75）
  - 权威性评分排序（政府官网 > 省市卫健委 > 公众号 > 法律库 > 搜索引擎）
  - 智能关键词扩展（纯主题词自动追加"法律法规"）
  - 六层容灾内容获取（requests多UA + Playwright + 政府搜索 + 摘要兜底）
"""

import re
import sys
import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
import builtin_laws

# ─── 通用配置 ─────────────────────────────────
_UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
]

def _make_headers(ua_index=0, mobile=False):
    ua = _UA_LIST[ua_index % len(_UA_LIST)]
    if mobile:
        return {
            "User-Agent": _UA_LIST[3],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

TIMEOUT_FAST   = 12
TIMEOUT_NORMAL = 25
MAX_RETRIES    = 3

# 会话池（用Session保持Cookie，模拟真实浏览器行为）
_http_session = None
_session_lock = threading.Lock()

def _get_session():
    global _http_session
    if _http_session is None:
        with _session_lock:
            if _http_session is None:
                _http_session = requests.Session()
                _http_session.headers.update(_make_headers(0))
                _http_session.verify = False
    return _http_session

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─── 底层网络请求 ─────────────────────────────
def _req(url, headers=None, retries=MAX_RETRIES, timeout=TIMEOUT_FAST, ua_idx=0):
    """快速请求，带重试 + 多UA轮换"""
    h = headers or _make_headers(ua_idx)
    session = _get_session()
    for i in range(retries):
        try:
            resp = session.get(url, headers=h, timeout=timeout,
                               verify=False, allow_redirects=True)
            resp.encoding = resp.apparent_encoding or "utf-8"
            if resp.status_code == 200:
                return resp
        except Exception:
            if i < retries - 1:
                time.sleep(0.5)
    return None


def _req_try_all(url, timeout=TIMEOUT_FAST):
    """依次尝试PC / 移动端UA，任一成功即返回"""
    for idx in range(len(_UA_LIST)):
        resp = _req(url, _make_headers(idx), retries=1, timeout=timeout, ua_idx=idx)
        if resp:
            return resp
    return None


# ─── 正文提取 ─────────────────────────────────
def _extract_page_title(soup):
    return soup.title.string.strip() if soup.title and soup.title.string else ""


def _extract_text_content(soup):
    for tag in soup(["script", "style", "meta", "noscript", "iframe", "nav",
                      "footer", ".sidebar", ".toolbar", ".header", ".menu",
                      ".nav", ".share", ".print", ".function", ".related",
                      "svg", "form", "aside"]):
        tag.decompose()

    selectors = [
        # ── 通用 ──
        "article", ".article", ".article-content",
        ".entry-content", ".post-content", ".field-item",
        ".detail", ".news_detail", ".text-content",
        ".detail_text", ".detail-content-text",
        # ── 政府/法律网站专用 ──
        ".TRS_Editor", ".Custom_UnionStyle", ".pages_content",
        ".con_text", ".news-content", ".detail-content",
        ".content-body", ".main-content", ".text-content",
        ".article-main", ".content-main", ".box-content",
        "#content", "#article-content", "#main-content",
        "#UCAP-CONTENT", "#zoom", "#news_content",
        ".law-content", ".law_text", ".law_detail",
        ".law_detail_con", ".law_content", ".detail_text",
        # ── flk.npc.gov.cn 全国人大 ──
        ".detail-main", ".law-detail", ".law-content-box",
        ".detail-content-box", ".detail-article",
        # ── gov.cn 中国政府网 ──
        ".newsbox", ".news_cont", ".article_con",
        ".xl_content", ".content_area", ".text_content",
        ".pages_content", ".article-content",
        # ── nhc.gov.cn 国家卫健委 ──
        ".cms-article", ".article-box", ".article-wrap",
        ".content-wrap", ".law-article", ".policy-content",
        ".detail-info", ".detail_info", ".main-detail",
        "#article_content", ".art_con", ".art-con",
        ".trs_editor", ".v_news_content",
        # ── moj.gov.cn 司法部 ──
        ".view-content", ".law-view", ".moj-content",
        ".lawnew-content", "#lawtext", ".law_show",
        # ── samr.gov.cn 市场监管总局 ──
        ".samr-content", ".content_text", ".normal-content",
        # ── mem.gov.cn 应急管理部 ──
        ".mem-content", ".yjgl-content", ".emergency-content",
        # ── court.gov.cn 最高法 ──
        ".detail-text", ".case-content", ".judgment",
        ".court-case", ".case-detail",
        # ── law-lib.com / pkulaw ──
        ".law_detail", ".law_main", ".law_text",
        ".pkulaw-content", ".law_content_box",
        # ── nhc.gov.cn 卫健委 ──
        ".list-content", ".article-content-area",
        ".content_wrap", ".info-content",
        # ── cdc / 疾控 ──
        ".news-content", ".detail_main", ".detail_main_box",
        # ── 其他常见 ──
        "#UCAP-CONTENT", "#ctrlfscont", "#zoomcon",
        "#ArticleContent", "#articleCon", "#mainText",
        ".body_text", ".article-body", ".article-text",
        ".view", ".view-content", ".node-content",
        ".field-name-body", ".field-item even",
        ".content_detail", ".detail_con", ".main_article",
    ]

    best, best_len = "", 0
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            t = el.get_text(separator="\n", strip=True)
            t = re.sub(r'[\r\n]+', '\n', t)
            if len(t) > best_len:
                best, best_len = t, len(t)

    if best_len >= 200:
        return _clean(best)

    body = soup.find("body")
    if body:
        for tag in body(["span.small", "span.info", ".time", ".source",
                          ".author", ".hits", ".publish-time"]):
            tag.decompose()
        t = body.get_text(separator="\n", strip=True)
        t = re.sub(r'[\r\n]+', '\n', t)
        if len(t) > best_len:
            best, best_len = t, len(t)

    return _clean(best) if best_len > 80 else ""


def _clean(t):
    t = re.sub(r'[\r\n]+', '\n', t)
    t = re.sub(r'[ \t]+', ' ', t)
    lines = [l.strip() for l in t.split('\n')]
    t = '\n'.join(lines)
    t = re.sub(r'\n{4,}', '\n\n', t)
    return t.strip()


def _resolve_baidu_url(baidu_url):
    """解析百度跳转链接，获取真实目标URL"""
    if not baidu_url:
        return ""
    if "baidu.com" not in baidu_url:
        return baidu_url

    # 方法1: 跟踪重定向
    try:
        session = _get_session()
        resp = session.get(baidu_url, timeout=8, verify=False, allow_redirects=True)
        if resp.url and "baidu.com" not in resp.url:
            return resp.url
    except Exception:
        pass

    # 方法2: 从参数中提取URL
    m = re.search(r'[?&]url=([^&]+)', baidu_url)
    if m:
        import urllib.parse
        decoded = urllib.parse.unquote(m.group(1))
        if decoded and "baidu.com" not in decoded and "javascript" not in decoded:
            return decoded

    m = re.search(r'[?&]wd=([^&]+)', baidu_url)
    if m:
        import urllib.parse
        decoded = urllib.parse.unquote(m.group(1))
        if decoded and len(decoded) > 5:
            return f"https://www.baidu.com/s?wd={quote_plus(decoded)}"

    return baidu_url


# ═══════════════════════════════════════════════
#  智能关键词扩展
# ═══════════════════════════════════════════════

_LAW_KEYWORDS = [
    "法律", "法规", "条例", "办法", "规定", "规范", "通知", "意见", "细则",
    "标准", "制度", "规章", "令", "法", "管理"
]

def _expand_query(query: str) -> str:
    """
    智能关键词扩展：
    - 如果查询词已包含法律类词汇 → 不修改
    - 否则追加"法律法规"提升搜索精度
    """
    q = query.strip()
    if any(kw in q for kw in _LAW_KEYWORDS):
        return q
    return f"{q} 法律法规"


def _expand_query_gov(query: str) -> str:
    """生成适合政府网站搜索的扩展词"""
    q = query.strip()
    if any(kw in q for kw in ["法律", "条例", "办法", "规定", "通知", "规范"]):
        return q
    return f"{q} 规定 办法"


# ═══════════════════════════════════════════════
#  搜索结果缓存（TTL=10分钟）
# ═══════════════════════════════════════════════

_search_cache: dict = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 600  # 秒

def _cache_get(key: str):
    with _cache_lock:
        entry = _search_cache.get(key)
        if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
            return entry["data"]
        return None

def _cache_set(key: str, data):
    with _cache_lock:
        _search_cache[key] = {"ts": time.time(), "data": data}
        if len(_search_cache) > 50:
            now = time.time()
            expired = [k for k, v in _search_cache.items()
                       if now - v["ts"] > _CACHE_TTL]
            for k in expired:
                del _search_cache[k]


# ═══════════════════════════════════════════════
#  通用搜索引擎
# ═══════════════════════════════════════════════

def search_baidu(query: str, top_n: int = 15) -> list:
    """百度搜索（国内可访问）"""
    results = []
    url = f"https://www.baidu.com/s?wd={quote_plus(query)}&ie=utf-8&rn={top_n}"
    resp = _req(url, _make_headers(0))
    if not resp:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select(".result,.c-container"):
        title_tag = item.select_one("h3 a") or item.select_one("h3")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "") if title_tag.name == "a" else ""
        if not link:
            link = item.get("mu", "") or item.get("href", "")
        real_url = _resolve_baidu_url(link)
        snippet_tag = item.select_one(".c-abstract") or item.select_one(".content-right_8Zs40")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        if title:
            results.append({
                "title": title, "url": real_url or link,
                "snippet": snippet[:400],
                "source": "百度搜索", "source_type": "online",
                "full_content": "",
            })
    return results[:top_n]


def search_sogou(query: str, top_n: int = 15) -> list:
    """搜狗搜索（国内备用）"""
    results = []
    base_url = f"https://www.sogou.com/web?query={quote_plus(query)}&num={top_n}"
    resp = _req(base_url, _make_headers(1))
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select(".vrwrap,.rb"):
        title_tag = item.select_one(".vr-title a") or item.select_one("h3 a") or item.select_one("a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "")
        if link.startswith("/"):
            link = "https://www.sogou.com" + link
        snippet_tag = item.select_one(".star-wiki") or item.select_one(".str-text")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        if title and link and link != "https://www.sogou.com/":
            results.append({
                "title": title, "url": link,
                "snippet": snippet[:400],
                "source": "搜狗搜索", "source_type": "online",
                "full_content": "",
            })
    return results[:top_n]


def search_bing(query: str, top_n: int = 15) -> list:
    """Bing 搜索"""
    results = []
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count={top_n}&setlang=zh-cn"
    resp = _req(url, _make_headers(0))
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("li.b_algo"):
        title_tag = item.select_one("h2 a")
        snippet_tag = item.select_one(".b_caption p")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and link:
                results.append({
                    "title": title, "url": link,
                    "snippet": snippet[:400],
                    "source": "Bing搜索", "source_type": "online",
                    "full_content": "",
                })
    return results[:top_n]


# ═══════════════════════════════════════════════
#  Bing 站内搜索（site: 语法精准覆盖政府网站）
# ═══════════════════════════════════════════════

def _bing_site_search(site_domain: str, query: str, source_label: str,
                      top_n: int = 8) -> list:
    """
    通用 Bing 站内搜索：site:domain query
    用于无法直接爬取但可通过 Bing 索引访问的政府网站
    """
    results = []
    q = f"site:{site_domain} {query}"
    url = f"https://www.bing.com/search?q={quote_plus(q)}&count={top_n}&setlang=zh-cn"
    resp = _req(url, _make_headers(0), timeout=TIMEOUT_FAST)
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("li.b_algo"):
        title_tag = item.select_one("h2 a")
        snippet_tag = item.select_one(".b_caption p")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and link and site_domain in link:
                results.append({
                    "title": title, "url": link,
                    "snippet": snippet[:400],
                    "source": source_label, "source_type": "online",
                    "full_content": "",
                })
    return results[:top_n]


def search_bing_gov(query: str, top_n: int = 8) -> list:
    """Bing 站内搜索：中国政府网 www.gov.cn"""
    return _bing_site_search("www.gov.cn", _expand_query_gov(query), "中国政府网", top_n)


def search_bing_nhc(query: str, top_n: int = 8) -> list:
    """Bing 站内搜索：国家卫健委 nhc.gov.cn"""
    return _bing_site_search("nhc.gov.cn", _expand_query_gov(query), "国家卫健委", top_n)


def search_bing_npc(query: str, top_n: int = 8) -> list:
    """Bing 站内搜索：全国人大法律数据库 flk.npc.gov.cn"""
    return _bing_site_search("flk.npc.gov.cn", query, "全国人大", top_n)


def search_bing_moj(query: str, top_n: int = 8) -> list:
    """Bing 站内搜索：司法部 moj.gov.cn"""
    return _bing_site_search("moj.gov.cn", _expand_query_gov(query), "司法部", top_n)


def search_bing_samr(query: str, top_n: int = 6) -> list:
    """Bing 站内搜索：市场监管总局 samr.gov.cn"""
    return _bing_site_search("samr.gov.cn", _expand_query_gov(query), "市场监管总局", top_n)


def search_bing_mem(query: str, top_n: int = 6) -> list:
    """Bing 站内搜索：应急管理部 mem.gov.cn"""
    return _bing_site_search("mem.gov.cn", _expand_query_gov(query), "应急管理部", top_n)


# ═══════════════════════════════════════════════
#  定向法律/政府数据库（直连爬取）
# ═══════════════════════════════════════════════

def search_lawlib(query: str, top_n: int = 10) -> list:
    """法律图书馆（law-lib.com）"""
    results = []
    url = f"https://www.law-lib.com/sz/search.asp?keyword={quote_plus(query)}"
    resp = _req(url)
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("a[href*='law_view']"):
        title = item.get_text(strip=True)
        link = item.get("href", "")
        if not title or len(title) < 4:
            continue
        results.append({
            "title": title, "url": urljoin(url, link),
            "snippet": f"法律图书馆 - {title}",
            "source": "法律图书馆", "source_type": "online", "full_content": "",
        })
        if len(results) >= top_n:
            break
    return results


def search_npc(query: str, top_n: int = 10) -> list:
    """全国人大法律数据库（flk.npc.gov.cn）"""
    results = []
    search_url = f"https://flk.npc.gov.cn/search.html?key={quote_plus(query)}"
    resp = _req(search_url)
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("a[href*='detail']"):
        title = item.get_text(strip=True)
        link = item.get("href", "")
        if not title or len(title) < 4:
            continue
        results.append({
            "title": title, "url": urljoin(search_url, link),
            "snippet": f"全国人大法律法规库 - {title}",
            "source": "全国人大", "source_type": "online", "full_content": "",
        })
        if len(results) >= top_n:
            break
    return results


def search_gov(query: str, top_n: int = 10) -> list:
    """中国政府网（gov.cn）直连搜索"""
    results = []
    search_url = f"https://www.gov.cn/search/?q={quote_plus(query)}"
    resp = _req(search_url)
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("a[href*='.gov.cn'],.list-item a"):
        title = item.get_text(strip=True)
        link = item.get("href", "")
        if not title or len(title) < 4:
            continue
        full_url = urljoin(search_url, link) if link.startswith("/") else link
        results.append({
            "title": title, "url": full_url,
            "snippet": f"中国政府网 - {title}",
            "source": "中国政府网", "source_type": "online", "full_content": "",
        })
        if len(results) >= top_n:
            break
    return results


def search_nhc(query: str, top_n: int = 10) -> list:
    """
    国家卫健委专项搜索（nhc.gov.cn）
    - 卫生健康政策法规、规范性文件的最权威来源
    - 通道1：官网搜索接口  通道2：Bing站内兜底
    """
    results = []

    # 通道1：卫健委官网搜索接口
    search_url = f"https://www.nhc.gov.cn/wjw/search/result.shtml?keyword={quote_plus(query)}"
    resp = _req(search_url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".search-list li, .result-list li, li.result-item"):
            title_tag = item.select_one("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if not title or len(title) < 4:
                continue
            if link.startswith("/"):
                link = "https://www.nhc.gov.cn" + link
            snippet_tag = item.select_one(".des, .desc, .summary, p")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else f"国家卫健委 - {title}"
            results.append({
                "title": title, "url": link,
                "snippet": snippet[:400],
                "source": "国家卫健委", "source_type": "online", "full_content": "",
            })
            if len(results) >= top_n:
                return results

    # 通道2：Bing 站内搜索兜底
    if len(results) < 3:
        site_query = f"site:nhc.gov.cn {_expand_query_gov(query)}"
        url2 = f"https://www.bing.com/search?q={quote_plus(site_query)}&count={top_n}&setlang=zh-cn"
        resp2 = _req(url2, _make_headers(0), timeout=TIMEOUT_FAST)
        if resp2:
            soup2 = BeautifulSoup(resp2.text, "html.parser")
            for item in soup2.select("li.b_algo"):
                title_tag = item.select_one("h2 a")
                snippet_tag = item.select_one(".b_caption p")
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "")
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    if title and link and "nhc.gov.cn" in link:
                        results.append({
                            "title": title, "url": link,
                            "snippet": snippet[:400],
                            "source": "国家卫健委", "source_type": "online",
                            "full_content": "",
                        })
                        if len(results) >= top_n:
                            break

    return results[:top_n]


def search_moj(query: str, top_n: int = 8) -> list:
    """
    司法部国家法规数据库（lawnew.moj.gov.cn）
    - 收录部门规章、地方性法规、规范性文件
    - 通道1: 直连搜索  通道2: Bing站内
    """
    results = []

    # 通道1：司法部法规数据库直连
    search_url = f"https://lawnew.moj.gov.cn/search?searchWord={quote_plus(query)}"
    resp = _req(search_url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        # 尝试多种选择器
        for item in soup.select(".result-item, .law-item, li a, .list-item"):
            title_tag = item if item.name == "a" else item.select_one("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if not title or len(title) < 4:
                continue
            if link.startswith("/"):
                link = "https://lawnew.moj.gov.cn" + link
            results.append({
                "title": title, "url": link,
                "snippet": f"司法部法规数据库 - {title}",
                "source": "司法部", "source_type": "online", "full_content": "",
            })
            if len(results) >= top_n:
                return results

    # 通道2：司法部官网 moj.gov.cn
    if len(results) < 2:
        url2 = f"https://www.moj.gov.cn/search/?q={quote_plus(_expand_query_gov(query))}"
        resp2 = _req(url2, _make_headers(0), timeout=TIMEOUT_FAST)
        if resp2:
            soup2 = BeautifulSoup(resp2.text, "html.parser")
            for item in soup2.select("a[href*='moj.gov.cn'], .result a, .list a"):
                title = item.get_text(strip=True)
                link = item.get("href", "")
                if not title or len(title) < 4:
                    continue
                if link.startswith("/"):
                    link = "https://www.moj.gov.cn" + link
                results.append({
                    "title": title, "url": link,
                    "snippet": f"司法部 - {title}",
                    "source": "司法部", "source_type": "online", "full_content": "",
                })
                if len(results) >= top_n:
                    break

    return results[:top_n]


def search_samr(query: str, top_n: int = 8) -> list:
    """
    国家市场监管总局（samr.gov.cn）
    - 食品、药品、医疗器械、特种设备等监管法规
    """
    results = []
    search_url = f"https://www.samr.gov.cn/search/?q={quote_plus(_expand_query_gov(query))}"
    resp = _req(search_url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("a[href*='samr.gov.cn'], .list-item a, .result a"):
            title = item.get_text(strip=True)
            link = item.get("href", "")
            if not title or len(title) < 4:
                continue
            if link.startswith("/"):
                link = "https://www.samr.gov.cn" + link
            results.append({
                "title": title, "url": link,
                "snippet": f"市场监管总局 - {title}",
                "source": "市场监管总局", "source_type": "online", "full_content": "",
            })
            if len(results) >= top_n:
                break

    # 兜底：Bing站内搜索
    if len(results) < 2:
        results += search_bing_samr(query, top_n - len(results))

    return results[:top_n]


def search_mem(query: str, top_n: int = 6) -> list:
    """
    应急管理部（mem.gov.cn）
    - 安全生产、突发事件应对、职业卫生法规
    """
    results = []
    search_url = f"https://www.mem.gov.cn/search/?q={quote_plus(_expand_query_gov(query))}"
    resp = _req(search_url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("a[href*='mem.gov.cn'], .list-item a, .result a"):
            title = item.get_text(strip=True)
            link = item.get("href", "")
            if not title or len(title) < 4:
                continue
            if link.startswith("/"):
                link = "https://www.mem.gov.cn" + link
            results.append({
                "title": title, "url": link,
                "snippet": f"应急管理部 - {title}",
                "source": "应急管理部", "source_type": "online", "full_content": "",
            })
            if len(results) >= top_n:
                break

    # 兜底：Bing站内搜索
    if len(results) < 2:
        results += search_bing_mem(query, top_n - len(results))

    return results[:top_n]


def search_cdc(query: str, top_n: int = 6) -> list:
    """
    中国疾控中心（chinacdc.cn）
    - 传染病防控、疫苗、公共卫生规范
    - 通道1: 直连  通道2: Bing站内
    """
    results = []
    search_url = f"https://www.chinacdc.cn/search?keywords={quote_plus(query)}"
    resp = _req(search_url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("a[href*='chinacdc.cn'], .search-result a, .list a"):
            title = item.get_text(strip=True)
            link = item.get("href", "")
            if not title or len(title) < 4:
                continue
            if link.startswith("/"):
                link = "https://www.chinacdc.cn" + link
            results.append({
                "title": title, "url": link,
                "snippet": f"中国疾控中心 - {title}",
                "source": "中国疾控中心", "source_type": "online", "full_content": "",
            })
            if len(results) >= top_n:
                break

    # 兜底：Bing站内
    if len(results) < 2:
        bing_cdc = _bing_site_search("chinacdc.cn", query, "中国疾控中心", top_n)
        results += bing_cdc

    return results[:top_n]


def search_wechat(query: str, top_n: int = 8) -> list:
    """
    搜狗微信搜索 — 覆盖微信公众号发布的卫生法规、政策解读、官方通知
    """
    results = []
    url = f"https://weixin.sogou.com/weixin?type=2&query={quote_plus(query)}&ie=utf8"
    resp = _req(url, _make_headers(1), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".weixin-article, .news-box .txt-box"):
            title_tag = item.select_one("h3 a") or item.select_one("a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet_tag = item.select_one(".txt-info") or item.select_one("p")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and link:
                results.append({
                    "title": title, "url": link,
                    "snippet": (snippet or f"微信公众号 - {title}")[:400],
                    "source": "微信公众号", "source_type": "online", "full_content": "",
                })
        if results:
            return results[:top_n]

    # 兜底：百度搜索微信公众号
    q = f"{query} 微信公众号 卫生 法规 通知"
    url2 = f"https://www.baidu.com/s?wd={quote_plus(q)}&ie=utf-8&rn={top_n}"
    resp2 = _req(url2, _make_headers(0))
    if resp2:
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        for item in soup2.select(".result,.c-container"):
            title_tag = item.select_one("h3 a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = item.get("mu", "") or item.get("href", "")
            if not title:
                continue
            real_url = _resolve_baidu_url(link)
            snippet_tag = item.select_one(".c-abstract")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else f"微信公众号 - {title}"
            results.append({
                "title": title, "url": real_url or link,
                "snippet": snippet[:400],
                "source": "微信公众号", "source_type": "online", "full_content": "",
            })
    return results[:top_n]


def _search_province_cdc(query: str, province: str, top_n: int = 4) -> list:
    """
    省市 CDC / 卫健委子站 Bing 站内搜索
    """
    results = []
    patterns = [
        (f"wsjkw.{province}.gov.cn", f"{province}卫健委"),
        (f"wst.{province}.gov.cn",    f"{province}卫健委"),
        (f"wsjkw.hubei.gov.cn",        "湖北省卫健委"),
        (f"cdc.hubei.gov.cn",          "湖北省疾控中心"),
        (f"hubei.gov.cn",              "湖北省卫健委"),
    ]
    for domain, label in patterns:
        bing_res = _bing_site_search(domain, query, label, top_n)
        results.extend(bing_res)
    return results


def search_provincial_gov(query: str, top_n: int = 8) -> list:
    """
    各省/市卫生行政主管部门专项搜索
    覆盖：省卫健委、市卫健委、区县卫健局、CDC
    """
    results = []

    # ── 百度：site:gov.cn 卫生法规 ──
    q = f"site:gov.cn 卫生 {_expand_query_gov(query)}"
    url = f"https://www.baidu.com/s?wd={quote_plus(q)}&ie=utf-8&rn={top_n}"
    resp = _req(url, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".result,.c-container"):
            title_tag = item.select_one("h3 a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = item.get("mu", "") or item.get("href", "")
            real_url = _resolve_baidu_url(link)
            snippet_tag = item.select_one(".c-abstract")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and real_url and "gov.cn" in real_url:
                # 智能判断来源标签
                src = "省级卫健委"
                if "nhc.gov.cn" in real_url or "chinacdc.cn" in real_url:
                    src = "国家卫健委"
                elif "npc.gov.cn" in real_url or "flk.npc.gov.cn" in real_url:
                    src = "全国人大"
                elif "moj.gov.cn" in real_url:
                    src = "司法部"
                elif "wuhan" in real_url:
                    src = "武汉市卫健委"
                elif "hubei" in real_url:
                    src = "湖北省卫健委"
                elif "xiaogan" in real_url or "ezhou" in real_url:
                    src = "地级市卫健委"
                results.append({
                    "title": title, "url": real_url,
                    "snippet": snippet[:400] or f"{src} - {title}",
                    "source": src, "source_type": "online", "full_content": "",
                })

    # ── Bing：site:gov.cn 卫生法规 ──
    q2 = f"site:gov.cn 卫生 法规 {_expand_query_gov(query)}"
    url2 = f"https://www.bing.com/search?q={quote_plus(q2)}&count={top_n}&setlang=zh-cn"
    resp2 = _req(url2, _make_headers(0), timeout=TIMEOUT_FAST)
    if resp2:
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        for item in soup2.select("li.b_algo"):
            title_tag = item.select_one("h2 a")
            snippet_tag = item.select_one(".b_caption p")
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                if title and link and "gov.cn" in link:
                    results.append({
                        "title": title, "url": link,
                        "snippet": snippet[:400],
                        "source": "省级卫健委", "source_type": "online",
                        "full_content": "",
                    })

    return results[:top_n]


def search_pkulaw(query: str, top_n: int = 8) -> list:
    """
    北大法宝（pkulaw.com）
    - 全面的法律法规数据库，含卫生健康专题
    """
    results = []
    # 使用 Bing 站内搜索（直连需登录）
    q = f"site:pkulaw.com {query}"
    url = f"https://www.bing.com/search?q={quote_plus(q)}&count={top_n}&setlang=zh-cn"
    resp = _req(url, _make_headers(0), timeout=TIMEOUT_FAST)
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select("li.b_algo"):
        title_tag = item.select_one("h2 a")
        snippet_tag = item.select_one(".b_caption p")
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and link and "pkulaw.com" in link:
                results.append({
                    "title": title, "url": link,
                    "snippet": snippet[:400],
                    "source": "北大法宝", "source_type": "online",
                    "full_content": "",
                })
    return results[:top_n]


def search_baidu_gov(query: str, top_n: int = 10) -> list:
    """
    百度站内搜索政府网站（site:gov.cn）
    - 覆盖全部 .gov.cn 子域
    """
    results = []
    q = f"site:gov.cn {_expand_query_gov(query)}"
    url = f"https://www.baidu.com/s?wd={quote_plus(q)}&ie=utf-8&rn={top_n}"
    resp = _req(url, _make_headers(0))
    if not resp:
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for item in soup.select(".result,.c-container"):
        title_tag = item.select_one("h3 a") or item.select_one("h3")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "") if title_tag.name == "a" else ""
        if not link:
            link = item.get("mu", "") or item.get("href", "")
        real_url = _resolve_baidu_url(link)
        snippet_tag = item.select_one(".c-abstract") or item.select_one(".content-right_8Zs40")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        if title and real_url and ".gov.cn" in real_url:
            # 根据域名判断来源标签
            src_label = "中国政府网"
            if "nhc.gov.cn" in real_url:
                src_label = "国家卫健委"
            elif "npc.gov.cn" in real_url:
                src_label = "全国人大"
            elif "moj.gov.cn" in real_url:
                src_label = "司法部"
            elif "samr.gov.cn" in real_url:
                src_label = "市场监管总局"
            elif "mem.gov.cn" in real_url:
                src_label = "应急管理部"
            elif "chinacdc.cn" in real_url:
                src_label = "中国疾控中心"
            results.append({
                "title": title, "url": real_url,
                "snippet": snippet[:400],
                "source": src_label, "source_type": "online",
                "full_content": "",
            })
    return results[:top_n]


# ═══════════════════════════════════════════════
#  内容获取（快速容灾 + 浏览器引擎）
# ═══════════════════════════════════════════════

_playwright_available = None

def _is_playwright_available():
    global _playwright_available
    if _playwright_available is not None:
        return _playwright_available
    try:
        import playwright
        import glob
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
            chrome_dirs = [
                os.path.join(base, "_playwright_browser", "chrome-win64"),
                os.path.join(base, "_playwright_browser", "chrome-win"),
            ]
            _playwright_available = any(os.path.isdir(d) for d in chrome_dirs)
            if not _playwright_available:
                bundled = os.path.join(base, "_playwright_browser", "chromium-*")
                _playwright_available = len(glob.glob(bundled)) > 0
        else:
            pw_home = os.path.join(os.environ.get("USERPROFILE", "~"),
                                   "AppData", "Local", "ms-playwright")
            _playwright_available = len(glob.glob(
                os.path.join(pw_home, "chromium-*"))) > 0
            if not _playwright_available:
                _playwright_available = len(glob.glob(
                    os.path.join(pw_home, "chrome-*"))) > 0
    except ImportError:
        _playwright_available = False
    return _playwright_available


def _find_playwright_browser_path():
    if not getattr(sys, 'frozen', False):
        return None
    base = os.path.dirname(sys.executable)
    for candidate in [
        os.path.join(base, "_playwright_browser", "chrome-win64", "chrome.exe"),
        os.path.join(base, "_playwright_browser", "chrome-win", "chrome.exe"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    import glob
    matches = glob.glob(os.path.join(base, "_playwright_browser", "chromium-*", "chrome.exe"))
    if matches:
        return matches[0]
    return None


def _fetch_with_playwright(url, timeout=30):
    if not _is_playwright_available():
        return {"title": "", "content": "", "success": False, "error": "Playwright不可用"}

    import asyncio

    if getattr(sys, 'frozen', False):
        browser_path = _find_playwright_browser_path()
        if browser_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.dirname(
                os.path.dirname(browser_path))

    from playwright.async_api import async_playwright

    async def _render():
        async with async_playwright() as p:
            launch_opts = {
                "headless": True,
                "args": ["--no-sandbox", "--disable-setuid-sandbox",
                         "--disable-dev-shm-usage", "--disable-gpu"]
            }
            browser_path = _find_playwright_browser_path()
            if browser_path:
                launch_opts["executable_path"] = browser_path
            try:
                browser = await p.chromium.launch(**launch_opts)
                page = await browser.new_page()
                await page.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9"})
                await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
                for _ in range(4):
                    await page.wait_for_timeout(2000)
                html = await page.content()
                title = await page.title()
                from bs4 import BeautifulSoup as BS
                soup = BS(html, "html.parser")
                content = _extract_text_content(soup)
                await browser.close()
                if content and len(content) > 150:
                    return {"title": title, "content": content, "success": True, "error": ""}
                return {"title": title, "content": content, "success": False,
                        "error": "浏览器渲染后未获取到有效正文"}
            except Exception as e:
                try:
                    await browser.close()
                except Exception:
                    pass
                return {"title": "", "content": "", "success": False,
                        "error": f"浏览器渲染失败: {str(e)[:80]}"}

    return asyncio.run(_render())


def fetch_content(url: str) -> dict:
    """单URL内容获取"""
    resolved = _resolve_baidu_url(url)
    if not resolved or "baidu.com" in resolved:
        resolved = url
    resp = _req_try_all(resolved, timeout=TIMEOUT_NORMAL)
    if not resp:
        return {"title": "", "content": "", "success": False,
                "error": "无法访问该链接（所有UA均失败）"}
    soup = BeautifulSoup(resp.text, "html.parser")
    title = _extract_page_title(soup)
    content = _extract_text_content(soup)
    if not content or len(content) < 80:
        return {"title": title, "content": "", "success": False,
                "error": "未能自动获取到正文（页面结构不匹配）"}
    return {"title": title, "content": content, "success": True, "error": ""}


def _try_alt_urls(law_title, snippet):
    if not law_title:
        return None, None
    clean = law_title.strip()
    if not clean or len(clean) < 4:
        return None, None
    gov_keywords = ["中华人民共和国", "办法", "条例", "规定", "规范", "通知", "细则", "标准"]
    if not any(k in clean for k in gov_keywords):
        return None, None
    kw = quote_plus(clean + " 全文 国务院")
    try:
        resp = _req(f"https://www.gov.cn/search/?q={kw}", timeout=8)
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link_tag in soup.select("a[href]"):
                href = link_tag.get("href", "")
                text = link_tag.get_text(strip=True)
                if clean[:8] in text and ".gov.cn" in href:
                    full_url = urljoin("https://www.gov.cn", href)
                    content_resp = _req_try_all(full_url, timeout=TIMEOUT_FAST)
                    if content_resp:
                        csoup = BeautifulSoup(content_resp.text, "html.parser")
                        c = _extract_text_content(csoup)
                        if c and len(c) > 200:
                            return full_url, c
    except Exception:
        pass
    return None, None


def fetch_law_full_text(url: str, law_title: str = "", snippet: str = "") -> dict:
    """
    增强版法规全文获取 — 六层容灾
    策略A:   requests 多UA轮换请求
    策略A1:  直接请求原URL（跳转解析失败时的兜底）
    策略A2:  Playwright 浏览器引擎渲染（处理JS SPA站点）
    策略A3:  根据法规名猜测政府网站原文链接
    策略B:   搜索摘要兜底
    策略C:   返回带URL的提示信息
    """
    clean_title = re.sub(r'^\[.*?\]\s*', '', law_title).strip() if law_title else ""

    if url:
        resolved = _resolve_baidu_url(url)
        if resolved and "baidu.com" not in resolved:
            resp = _req_try_all(resolved, timeout=TIMEOUT_FAST)
            if resp:
                soup = BeautifulSoup(resp.text, "html.parser")
                content = _extract_text_content(soup)
                if content and len(content) > 200:
                    return {"title": _extract_page_title(soup) or clean_title,
                            "content": content, "success": True, "error": ""}
            pw = _fetch_with_playwright(resolved)
            if pw["success"] and len(pw["content"]) > 200:
                return pw

    if url and "baidu.com" not in url:
        resp = _req_try_all(url, timeout=TIMEOUT_FAST)
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            content = _extract_text_content(soup)
            if content and len(content) > 200:
                return {"title": _extract_page_title(soup) or clean_title,
                        "content": content, "success": True, "error": ""}

    if url and url.strip():
        pw_url = _resolve_baidu_url(url)
        if "baidu.com" in pw_url:
            pw_url = url
        pw_result = _fetch_with_playwright(pw_url)
        if pw_result["success"] and len(pw_result["content"]) > 200:
            return pw_result

    alt_url, alt_content = _try_alt_urls(law_title, snippet)
    if alt_content and len(alt_content) > 200:
        return {"title": clean_title, "content": alt_content, "success": True, "error": ""}

    if snippet and len(snippet) > 50:
        return {"title": clean_title or "未命名", "content": f"{snippet}",
                "success": True, "error": ""}

    error_msg = "无法自动获取全文"
    if url:
        error_msg += f"\n\n如需查看原文，请复制以下链接在浏览器中打开：\n{url}"
    return {"title": clean_title, "content": "", "success": False, "error": error_msg}


# ═══════════════════════════════════════════════
#  智能去重：标题相似度过滤
# ═══════════════════════════════════════════════

def _title_tokens(title: str) -> set:
    title = re.sub(r'[\[\]【】（）()《》\s]', '', title)
    if len(title) < 2:
        return set(title)
    return {title[i:i+2] for i in range(len(title) - 1)}

def _jaccard(a: str, b: str) -> float:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union > 0 else 0.0

def _dedup_by_title(results: list, threshold: float = 0.75) -> list:
    kept = []
    for r in results:
        title = r.get("title", "")
        is_dup = False
        for kr in kept:
            if _jaccard(title, kr.get("title", "")) >= threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(r)
    return kept


# ═══════════════════════════════════════════════
#  结果排序：权威源优先（v5.0 扩展）
# ═══════════════════════════════════════════════

_SOURCE_PRIORITY = {
    "内置数据库":   0,   # 最高优先级
    "国家卫健委":   1,   # 卫生健康领域最权威
    "全国人大":     2,   # 国家立法机关
    "司法部":       3,   # 法规备案/解释权威
    "中国政府网":   4,   # 国务院/国家级政策
    "市场监管总局": 5,   # 食品药品/医疗器械监管
    "应急管理部":   6,   # 安全生产/职业卫生
    "中国疾控中心": 7,   # 传染病/公共卫生技术规范
    "省级卫健委":   8,   # 各省市区卫生行政主管部门
    "微信公众号":   9,   # 官方公众号政策解读
    "法律图书馆":   10,  # 权威法律数据库
    "北大法宝":     11,  # 权威法律数据库
    "百度搜索":     12,
    "Bing搜索":     13,
    "搜狗搜索":     14,
}

_GOV_DOMAIN_BOOST = [
    "nhc.gov.cn", "flk.npc.gov.cn", "npc.gov.cn", "gov.cn",
    "moj.gov.cn", "lawnew.moj.gov.cn",
    "samr.gov.cn", "mem.gov.cn", "chinacdc.cn",
    "court.gov.cn", "moh.gov.cn", "mca.gov.cn",
    "hubei.gov.cn", "wuhan.gov.cn",
]

def _result_score(r: dict) -> int:
    src = r.get("source", "")
    url = r.get("url", "")
    score = _SOURCE_PRIORITY.get(src, 15)
    for domain in _GOV_DOMAIN_BOOST:
        if domain in url:
            score = max(0, score - 1)
            break
    return score


# ═══════════════════════════════════════════════
#  综合搜索（12源并发 v5.0）
# ═══════════════════════════════════════════════

def search_all(query: str, category: str = "") -> list:
    """
    综合全网搜索 v5.1 — 14源并发 + 政府网站全面覆盖 + 省市卫健委 + 微信公众号

    数据源清单（14个）：
      政府权威（直连）：国家卫健委、全国人大、中国政府网、司法部、市场监管总局、应急管理部、中国疾控中心
      省市卫健委：省级卫健委（含湖北省/武汉市/黄冈市等）
      公众号：微信公众号政策解读
      专项数据库：法律图书馆、北大法宝
      搜索引擎：百度gov站内、Bing全网、搜狗
      兜底补充：搜狗微信

    排序策略：内置库 > 政府官网 > 省市卫健委 > 公众号 > 权威法律库 > 通用搜索引擎
    """
    cache_key = f"{query}|{category}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    q_law = _expand_query(query)   # 法律扩展词（百度/Bing用）
    q_gov  = _expand_query_gov(query)  # 政府网站扩展词

    merged = []
    seen_urls = set()

    def _add(r, source_label, source_type="online"):
        key = r.get("url") or r.get("title", "")
        if key and key not in seen_urls:
            seen_urls.add(key)
            r["source"] = source_label
            r["source_type"] = source_type
            r.setdefault("full_content", "")
            merged.append(r)

    # ── 1. 内置库（同步，最高优先级）──
    for law in builtin_laws.search_builtin(query, category):
        _add({
            "title": f"[{law['category']}] {law['title']}",
            "url": law.get("source_url", ""),
            "snippet": f"文号: {law['doc_number']} | 发布: {law['publish_date']} | {law['summary'][:150]}",
            "doc_number": law.get("doc_number", ""),
            "publish_date": law.get("publish_date", ""),
            "law_summary": law.get("summary", ""),
        }, "内置数据库", "builtin")

    # ── 2. 14源并发搜索 ──
    tasks = {
        # 政府权威直连（7源）
        "国家卫健委":   (search_nhc,    query,   10),
        "全国人大":     (search_npc,    query,    8),
        "中国政府网":   (search_gov,    query,    8),
        "司法部":       (search_moj,    query,    8),
        "市场监管总局": (search_samr,   query,    6),
        "应急管理部":   (search_mem,    query,    6),
        "中国疾控中心": (search_cdc,    query,    6),
        # 省市卫健委（1源）
        "省级卫健委":   (search_provincial_gov, query, 8),
        # 微信公众号（1源）
        "微信公众号":   (search_wechat, query,    8),
        # 专项法律数据库（2源）
        "法律图书馆":   (search_lawlib, query,    8),
        "北大法宝":     (search_pkulaw, q_law,    8),
        # 搜索引擎（3源）
        "百度gov站内":  (search_baidu_gov, query, 10),
        "Bing搜索":     (search_bing,   q_law,   15),
        "搜狗搜索":     (search_sogou,  q_law,   10),
    }

    online_results: dict = {}

    with ThreadPoolExecutor(max_workers=14) as executor:
        future_map = {}
        for label, (fn, q, n) in tasks.items():
            future = executor.submit(fn, q, n)
            future_map[future] = label

        for future in as_completed(future_map, timeout=25):
            label = future_map[future]
            try:
                res = future.result(timeout=2)
                online_results[label] = res or []
            except Exception:
                online_results[label] = []

    # ── 3. 按权威性顺序合并网络结果 ──
    ordered_sources = [
        "国家卫健委", "全国人大", "司法部", "中国政府网",
        "市场监管总局", "应急管理部", "中国疾控中心",
        "省级卫健委", "微信公众号",
        "法律图书馆", "北大法宝",
        "百度gov站内", "Bing搜索", "搜狗搜索",
    ]
    for src in ordered_sources:
        for r in online_results.get(src, []):
            # 百度gov站内搜索返回的结果，source_label 已经在函数里设了细分标签
            # 保持函数内已分配的 source 字段
            _add(r, r.get("source", src))

    # ── 4. 标题去重（Jaccard相似度）──
    merged = _dedup_by_title(merged, threshold=0.75)

    # ── 5. 排序（内置库最前，然后按权威性）──
    builtin_items = [r for r in merged if r.get("source_type") == "builtin"]
    online_items  = [r for r in merged if r.get("source_type") != "builtin"]
    online_items.sort(key=_result_score)
    final = builtin_items + online_items

    # ── 6. 写入缓存 ──
    _cache_set(cache_key, final)

    return final
