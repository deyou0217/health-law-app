# -*- coding: utf-8 -*-
"""
卫健法律法规检索系统 - 主程序
暗色护眼 UI · 全网搜索 · 一键导出 Word（党政机关公文标准）
v4.0 — 14源并发 · 政府网站全面覆盖 · 省市卫健委 · 微信公众号
"""

import os
import sys
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import searcher
import doc_generator
import builtin_laws

# ==================== 配色方案（暗色护眼 · 简洁稳重） ====================
C = {
    "bg": "#1a1a2e",          # 主背景（深蓝黑）
    "card": "#16213e",        # 卡片背景
    "input_bg": "#0f3460",    # 输入框
    "list_bg": "#1a1a2e",     # 列表
    "hover": "#1f3050",       # 悬停
    "selected": "#264f78",    # 选中
    "fg": "#e0e0e0",          # 主文字
    "fg2": "#a0a0b0",         # 辅助文字
    "fg3": "#707080",         # 弱文字
    "accent": "#2196F3",      # 主题蓝
    "accent2": "#1976D2",     # 主题深蓝
    "green": "#4CAF50",       # 成功
    "orange": "#FF9800",      # 警告
    "red": "#f44336",         # 危险
    "border": "#2a2a4a",      # 边框
    "scroll": "#3a3a5a",      # 滚动条
}

# 字体配置（加大版）
FONT = {
    "title": ("Microsoft YaHei UI", 20, "bold"),
    "subtitle": ("Microsoft YaHei UI", 14, "bold"),
    "section": ("Microsoft YaHei UI", 13, "bold"),
    "normal": ("Microsoft YaHei UI", 12),
    "normal_bold": ("Microsoft YaHei UI", 12, "bold"),
    "small": ("Microsoft YaHei UI", 11),
    "tiny": ("Microsoft YaHei UI", 10),
    "preview_title": ("Microsoft YaHei UI", 16, "bold"),
    "preview_body": ("Microsoft YaHei UI", 12),
    "preview_info": ("Microsoft YaHei UI", 11),
    "preview_warn": ("Microsoft YaHei UI", 11),
}

# ==================== 工具函数 ====================
def _make_button(parent, text, cmd, bg="#2196F3", fg="white",
                  font=FONT["normal_bold"], padx=18, pady=6, **kw):
    """快捷创建扁平按钮"""
    return tk.Button(parent, text=text, command=cmd,
                    font=font, bg=bg, fg=fg,
                    relief=tk.FLAT, padx=padx, pady=pady,
                    activebackground=C["accent2"], activeforeground="white",
                    cursor="hand2", **kw)


class LawSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("卫健法律法规检索系统 v4.0")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1280, 800)

        # 窗口居中
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"1280x800+{(sw-1280)//2}+{(sh-800)//2}")

        # 数据
        self.search_results = []
        self.selected_indices = set()
        self.check_vars = {}
        self.is_searching = False
        self.cat_var = tk.StringVar(value="")

        self._build_ui()
        self.root.bind("<Control-Return>", lambda e: self.do_search())
        self.root.bind("<Escape>", lambda e: self.clear_all())
        self._show_welcome()

    # ============================ UI 构建 ============================

    def _build_ui(self):
        # ===== 顶部标题 =====
        top = tk.Frame(self.root, bg=C["bg"])
        top.pack(fill=tk.X, padx=24, pady=(18, 6))

        tk.Label(top, text="卫健法律法规检索系统",
                font=FONT["title"], bg=C["bg"], fg=C["accent"]).pack(side=tk.LEFT)

        tk.Label(top, text="v4.0  ·  黄州区疾病预防控制中心",
                font=FONT["small"], bg=C["bg"], fg=C["fg3"]).pack(
                side=tk.LEFT, padx=(14, 0), pady=(8, 0))

        # ===== 搜索栏 =====
        search_card = tk.Frame(self.root, bg=C["card"],
                              highlightbackground=C["border"], highlightthickness=1)
        search_card.pack(fill=tk.X, padx=24, pady=(4, 0))

        sr = tk.Frame(search_card, bg=C["card"], padx=18, pady=14)
        sr.pack(fill=tk.X)

        # 搜索行
        row1 = tk.Frame(sr, bg=C["card"])
        row1.pack(fill=tk.X)

        tk.Label(row1, text="关键词：", font=FONT["normal_bold"],
                bg=C["card"], fg=C["fg"]).pack(side=tk.LEFT)

        self.entry = tk.Entry(row1, font=("Microsoft YaHei UI", 13),
                              bg=C["input_bg"], fg=C["fg"],
                              insertbackground=C["accent"],
                              relief=tk.FLAT, bd=10, highlightthickness=0)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 10))
        self.entry.bind("<Return>", lambda e: self.do_search())
        self.entry.focus_set()

        self.s_btn = _make_button(row1, " 搜  索 ", self.do_search,
                                  bg=C["accent"], font=FONT["normal_bold"], padx=24)
        self.s_btn.pack(side=tk.RIGHT)

        # 过滤行
        row2 = tk.Frame(sr, bg=C["card"])
        row2.pack(fill=tk.X, pady=(8, 0))

        tk.Label(row2, text="分类筛选：", font=FONT["small"],
                bg=C["card"], fg=C["fg2"]).pack(side=tk.LEFT)

        cats = ["全部"] + builtin_laws.get_categories()
        self.cat_combo = ttk.Combobox(row2, textvariable=self.cat_var,
                                      values=cats, state="readonly",
                                      width=14, font=FONT["small"])
        self.cat_combo.current(0)
        self.cat_combo.pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(row2, text="提示：输入法规名称 / 文号 / 关键词，按 Enter 搜索  |  勾选后导出 Word",
                font=FONT["tiny"], bg=C["card"], fg=C["fg3"]).pack(side=tk.RIGHT)

        # ===== 主区域 =====
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=(8, 6))

        # ----- 左侧：结果列表 -----
        left = tk.Frame(body, bg=C["card"],
                       highlightbackground=C["border"], highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left.pack_propagate(False)
        left.configure(width=420)

        # 列表标题
        lh = tk.Frame(left, bg=C["card"])
        lh.pack(fill=tk.X, padx=14, pady=(12, 4))

        tk.Label(lh, text="搜索结果", font=FONT["section"],
                bg=C["card"], fg=C["fg"]).pack(side=tk.LEFT)

        self.count_lbl = tk.Label(lh, text="0 条", font=FONT["normal"],
                                  bg=C["card"], fg=C["fg2"])
        self.count_lbl.pack(side=tk.RIGHT)

        # 全选
        la = tk.Frame(left, bg=C["card"])
        la.pack(fill=tk.X, padx=14, pady=(0, 4))

        self.sel_all_var = tk.IntVar(value=0)
        self.sel_all_cb = tk.Checkbutton(la, text="全选", variable=self.sel_all_var,
                                        command=self._toggle_all,
                                        font=FONT["small"],
                                        bg=C["card"], fg=C["fg"],
                                        selectcolor=C["input_bg"],
                                        activebackground=C["card"],
                                        activeforeground=C["fg"])
        self.sel_all_cb.pack(side=tk.LEFT)

        # Canvas 列表
        lc = tk.Frame(left, bg=C["list_bg"])
        lc.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 10))

        self.canvas = tk.Canvas(lc, bg=C["list_bg"], highlightthickness=0, bd=0)
        self.scroll = tk.Scrollbar(lc, orient=tk.VERTICAL, command=self.canvas.yview,
                                   bg=C["scroll"], troughcolor=C["bg"])
        self.list_frame = tk.Frame(self.canvas, bg=C["list_bg"])

        self.list_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 滚轮
        def _mw(e):
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _mw, add="+")
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # ----- 右侧：预览 -----
        right = tk.Frame(body, bg=C["card"],
                        highlightbackground=C["border"], highlightthickness=1)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        rh = tk.Frame(right, bg=C["card"])
        rh.pack(fill=tk.X, padx=14, pady=(12, 4))

        tk.Label(rh, text="全文预览", font=FONT["section"],
                bg=C["card"], fg=C["fg"]).pack(side=tk.LEFT)

        self.src_lbl = tk.Label(rh, text="", font=FONT["small"],
                                bg=C["card"], fg=C["fg2"])
        self.src_lbl.pack(side=tk.RIGHT)

        # 预览文本框
        pv_cont = tk.Frame(right, bg=C["list_bg"])
        pv_cont.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 10))

        self.preview = tk.Text(pv_cont, wrap=tk.WORD,
                               font=FONT["preview_body"],
                               bg=C["list_bg"], fg=C["fg"],
                               insertbackground=C["accent"],
                               state=tk.DISABLED, relief=tk.FLAT,
                               padx=14, pady=14,
                               highlightthickness=0, bd=0)
        pv_scroll = tk.Scrollbar(pv_cont, orient=tk.VERTICAL,
                                 command=self.preview.yview,
                                 bg=C["scroll"], troughcolor=C["bg"])
        self.preview.configure(yscrollcommand=pv_scroll.set)
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pv_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 预览标签
        self.preview.tag_configure("title_tag", font=FONT["preview_title"],
                                   foreground=C["accent"], spacing1=8, spacing3=10)
        self.preview.tag_configure("info_tag", font=FONT["preview_info"],
                                   foreground=C["fg2"], spacing1=3, spacing3=3)
        self.preview.tag_configure("warn_tag", font=FONT["preview_warn"],
                                   foreground=C["orange"], spacing1=5, spacing3=5)
        self.preview.tag_configure("body_tag", font=FONT["preview_body"],
                                   foreground=C["fg"], spacing1=2, spacing3=2)
        self.preview.tag_configure("trace_tag", font=FONT["preview_info"],
                                   foreground=C["green"], spacing1=4, spacing3=4)
        self.preview.tag_configure("sep_tag", font=FONT["tiny"],
                                   foreground=C["fg3"], spacing1=2, spacing3=2)

        # ===== 底部操作栏 =====
        btm = tk.Frame(self.root, bg=C["bg"])
        btm.pack(fill=tk.X, padx=24, pady=(0, 14))

        self.progress = ttk.Progressbar(btm, mode="indeterminate",
                                        length=200, style="TProgressbar")
        ttk.Style().configure("TProgressbar", background=C["accent"],
                             troughcolor=C["input_bg"], borderwidth=0)

        self.status_lbl = tk.Label(btm, text="就绪，请输入关键词搜索",
                                   font=FONT["normal"], bg=C["bg"], fg=C["fg2"])
        self.status_lbl.pack(side=tk.LEFT)

        bgp = tk.Frame(btm, bg=C["bg"])
        bgp.pack(side=tk.RIGHT)

        self.clear_btn = _make_button(bgp, " 清空结果 ", self.clear_all,
                                      bg=C["card"], fg=C["fg"],
                                      font=FONT["normal"], padx=14, pady=4)
        self.clear_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.export_btn = _make_button(bgp, " 导出 Word 文档 ", self.export_word,
                                       bg=C["green"], font=FONT["normal_bold"],
                                       padx=20, pady=4)
        self.export_btn.pack(side=tk.RIGHT)

    # ============================ 功能方法 ============================

    def _show_welcome(self):
        self.preview.configure(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        msg = (
            "卫健法律法规检索系统\n\n"
            "━━━ 使用说明 ━━━\n\n"
            "1. 在搜索框输入关键词（法规名称、文号、主题等）\n"
            "2. 按 Enter 或点击「搜索」按钮开始检索\n"
            "3. 勾选需要的法规/案例\n"
            "4. 点击「导出 Word 文档」生成标准公文\n\n"
            "数据来源：内置 30+ 部核心法规 + 国家/省市卫健委 + 国家卫健委/人大/司法部/政府网/疾控/市监/应急 + 微信公众号 + 法律图书馆/北大法宝 + Bing/百度/搜狗 14源并发\n\n"
            "文档格式：党政机关公文标准（页眉 / 字体 / 行距 / 页边距 / 页码）\n"
            "溯源信息：每条法规均标注来源链接、文号、发布日期\n"
        )
        self.preview.insert(tk.END, msg, "body_tag")
        self.preview.configure(state=tk.DISABLED)

    def _toggle_all(self):
        checked = self.sel_all_var.get() == 1
        for v in self.check_vars.values():
            v.set(1 if checked else 0)
        self.selected_indices.clear()
        if checked:
            self.selected_indices = set(range(len(self.search_results)))
        self._update_status()

    def _on_check(self, idx):
        v = self.check_vars[idx]
        if v.get() == 1:
            self.selected_indices.add(idx)
        else:
            self.selected_indices.discard(idx)
            self.sel_all_var.set(0)
        self._update_status()

    def _on_click(self, idx):
        """点击结果项 — 获取全文并预览（多策略自动容灾 + 进度反馈）"""
        if idx < 0 or idx >= len(self.search_results):
            return
        r = self.search_results[idx]
        self._show_preview(r, loading=True)

        def fetch():
            content_data = {"title": r["title"], "content": "", "error": ""}

            # 提取法规名称
            law_title = re.sub(r'^\[.*?\]\s*', '', r["title"]).strip()

            # 更新状态：正在解析
            self.root.after(0, lambda: self.status_lbl.configure(
                text="正在获取全文内容（策略1/6: 解析链接...）"))

            # 使用多策略获取全文（传入snippet作为兜底）
            fetched = searcher.fetch_law_full_text(
                r.get("url", ""), law_title, r.get("snippet", ""))
            if fetched["success"]:
                content_data = fetched
                got_full = len(fetched["content"]) > 200
                self.root.after(0, lambda: self.status_lbl.configure(
                    text="全文获取完成" if got_full else "已获取摘要内容"))
            else:
                content_data["error"] = fetched.get("error", "")
                # 内置库结果 → 用完整摘要代替
                if r.get("source_type") == "builtin" and r.get("law_summary"):
                    content_data["content"] = r["law_summary"]
                elif r.get("snippet"):
                    content_data["content"] = r["snippet"]
                self.root.after(0, lambda: self.status_lbl.configure(
                    text="全文获取失败，可查看错误提示"))

            # 缓存正文供导出使用
            r["full_content"] = content_data["content"]
            r["full_content_fetched"] = len(content_data.get("content", "")) > 200

            self.root.after(0, lambda: self._show_preview(r, content_data))

        threading.Thread(target=fetch, daemon=True).start()

    def _show_preview(self, result, data=None, loading=False):
        """展示预览内容"""
        self.preview.configure(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)

        if loading:
            self.preview.insert(tk.END, "正在获取全文内容，请稍候...\n\n", "warn_tag")
            self.preview.insert(tk.END, "当前正在：\n", "body_tag")
            self.preview.insert(tk.END, "1. 解析搜索结果链接\n", "body_tag")
            self.preview.insert(tk.END, "2. 尝试多策略获取原文\n", "body_tag")
            self.preview.insert(tk.END, "3. 提取正文内容\n\n", "body_tag")
            self.preview.insert(tk.END, "摘要信息：\n", "body_tag")
            self.preview.insert(tk.END, result.get("snippet", ""), "body_tag")
            self.preview.configure(state=tk.DISABLED)
            return

        title = data.get("title", result["title"])
        content = data.get("content", "")
        error = data.get("error", "")
        got_full = result.get("full_content_fetched", False)

        # 标题
        self.preview.insert(tk.END, title + "\n", "title_tag")

        # 溯源信息区块（仅保留来源、链接、全文状态、检索日期）
        trace_parts = []
        if result.get("source"):
            trace_parts.append(f"来源：{result['source']}")
        if result.get("url"):
            trace_parts.append(f"链接：{result['url']}")

        for t in trace_parts:
            self.preview.insert(tk.END, t + "\n", "trace_tag")

        # 全文获取状态
        if got_full:
            self.preview.insert(tk.END, "全文状态：✅ 已获取完整正文\n", "trace_tag")
            self.src_lbl.configure(text="已获全文  ✅", fg=C["green"])
        else:
            self.preview.insert(tk.END, "全文状态：⚠ 未能自动获取全文\n", "warn_tag")
            self.src_lbl.configure(text="摘要预览  ⚠", fg=C["orange"])

        # 检索日期
        from datetime import datetime
        now_str = datetime.now().strftime("%Y年%m月%d日")
        self.preview.insert(tk.END, f"检索日期：{now_str}\n", "trace_tag")

        # 错误详情（如果有）
        if error and not got_full:
            self.preview.insert(tk.END, "\n【错误信息】\n", "warn_tag")
            self.preview.insert(tk.END, error + "\n", "warn_tag")
            if result.get("url"):
                self.preview.insert(tk.END,
                    "提示：请复制上方「链接」在浏览器中手动打开查看原文。\n",
                    "warn_tag")

        # 分隔
        self.preview.insert(tk.END, "\n" + "━" * 40 + "\n\n", "sep_tag")

        # 正文
        if content:
            clean = re.sub(r'\n{4,}', '\n\n', content)
            self.preview.insert(tk.END, clean, "body_tag")
            if not got_full:
                self.preview.insert(tk.END,
                    "\n\n——— 以上为摘要内容 ———\n如需完整全文，请在浏览器中打开原文链接。",
                    "warn_tag")
            result["full_content"] = content
        else:
            self.preview.insert(tk.END, "[暂未获取到正文内容]\n", "warn_tag")
            if result.get("url"):
                self.preview.insert(tk.END,
                    "请复制上方「链接」在浏览器中手动打开查看原文。\n",
                    "body_tag")
            else:
                self.preview.insert(tk.END,
                    "该搜索结果无可用链接。\n",
                    "body_tag")

        self.preview.configure(state=tk.DISABLED)

    def _build_list(self):
        """构建搜索结果列表"""
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.check_vars = {}
        self.selected_indices.clear()
        self.sel_all_var.set(0)
        self.count_lbl.configure(text=f"{len(self.search_results)} 条")

        if not self.search_results:
            tk.Label(self.list_frame,
                    text="\n\n暂无搜索结果\n\n请输入关键词搜索",
                    font=FONT["normal"], bg=C["list_bg"],
                    fg=C["fg3"]).pack(expand=True, fill=tk.BOTH)
            return

        for idx, r in enumerate(self.search_results):
            self._make_item(idx, r)

        # 自动选中前5条
        n = min(5, len(self.search_results))
        for i in range(n):
            self.check_vars[i].set(1)
            self.selected_indices.add(i)
        self._update_status()

    def _make_item(self, idx, r):
        """创建单个列表项（加大字体、含全文状态标记）"""
        frm = tk.Frame(self.list_frame, bg=C["list_bg"])
        frm.pack(fill=tk.X, padx=4, pady=(2, 0))

        # 复选框
        var = tk.IntVar(value=0)
        self.check_vars[idx] = var
        cb = tk.Checkbutton(frm, variable=var,
                           command=lambda i=idx: self._on_check(i),
                           bg=C["list_bg"], fg=C["fg"],
                           selectcolor=C["input_bg"],
                           activebackground=C["list_bg"],
                           activeforeground=C["fg"], bd=0, padx=4)
        cb.pack(side=tk.LEFT, fill=tk.NONE)

        # 文本区
        tf = tk.Frame(frm, bg=C["list_bg"], cursor="hand2")
        tf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=5)
        tf.bind("<Button-1>", lambda e, i=idx: self._on_click(i))

        # 标题行（含来源标记）
        src_type = r.get("source_type", "")
        if src_type == "builtin":
            tag = " [库]"
            tag_color = C["green"]
        else:
            tag = " [网]"
            tag_color = C["accent"]

        title_text = r["title"]
        if len(title_text) > 50:
            title_text = title_text[:47] + "..."

        tl = tk.Label(tf, text=title_text,
                     font=FONT["small"], bg=C["list_bg"],
                     fg=C["fg"], anchor=tk.W, cursor="hand2")
        tl.pack(fill=tk.X)
        tl.bind("<Button-1>", lambda e, i=idx: self._on_click(i))
        # 加来源标签
        tag_lbl = tk.Label(tf, text=tag, font=("Microsoft YaHei UI", 9),
                          bg=C["list_bg"], fg=tag_color,
                          anchor=tk.W, cursor="hand2")
        tag_lbl.pack(anchor=tk.W)
        tag_lbl.bind("<Button-1>", lambda e, i=idx: self._on_click(i))

        # 摘要行
        src_name = r.get("source", "")
        snippet = r.get("snippet", "")
        if snippet and len(snippet) > 90:
            snippet = snippet[:87] + "..."

        st = f"[{src_name}] {snippet}" if snippet else f"[{src_name}]"
        si = tk.Label(tf, text=st, font=FONT["tiny"],
                     bg=C["list_bg"], fg=C["fg3"],
                     anchor=tk.W, cursor="hand2", wraplength=360)
        si.pack(fill=tk.X)
        si.bind("<Button-1>", lambda e, i=idx: self._on_click(i))

        # 分隔线
        tk.Frame(self.list_frame, height=1, bg=C["border"]).pack(fill=tk.X, padx=6)

    # ============================ 搜索 ============================

    def do_search(self):
        kw = self.entry.get().strip()
        if not kw:
            messagebox.showinfo("提示", "请输入搜索关键词")
            return
        if self.is_searching:
            return

        self.is_searching = True
        self.s_btn.configure(state=tk.DISABLED, text=" 搜索中... ")
        self.progress.pack(side=tk.LEFT, padx=(10, 0))
        self.progress.start()
        self.status_lbl.configure(text="正在14源并发搜索（卫健委/人大/司法部/政府网/省市卫健委/公众号/市监/应急/法律库...）")

        cat = self.cat_var.get()
        if cat == "全部":
            cat = ""

        def thread():
            try:
                res = searcher.search_all(kw, cat)
                self.root.after(0, lambda: self._on_search_done(res, kw))
            except Exception as e:
                self.root.after(0, lambda: self._on_search_err(str(e)))

        threading.Thread(target=thread, daemon=True).start()

    def _on_search_done(self, results, kw):
        self.is_searching = False
        self.progress.stop()
        self.progress.pack_forget()
        self.s_btn.configure(state=tk.NORMAL, text=" 搜  索 ")

        self.search_results = results
        self._build_list()
        self.status_lbl.configure(text=f"搜索完成，共找到 {len(results)} 条结果")

        if results:
            self._on_click(0)
        else:
            self.preview.configure(state=tk.NORMAL)
            self.preview.delete(1.0, tk.END)
            self.preview.insert(tk.END,
                f"未找到与「{kw}」相关的结果\n\n"
                "建议：\n"
                "• 尝试使用更简短的关键词\n"
                "• 检查网络连接是否正常\n"
                "• 可先在内置数据库中选择分类筛选", "body_tag")
            self.preview.configure(state=tk.DISABLED)

    def _on_search_err(self, msg):
        self.is_searching = False
        self.progress.stop()
        self.progress.pack_forget()
        self.s_btn.configure(state=tk.NORMAL, text=" 搜  索 ")
        self.status_lbl.configure(text="搜索出错")
        messagebox.showerror("搜索出错", f"搜索过程中出现错误：\n{msg}")

    # ============================ 导出 Word ============================

    def export_word(self):
        """导出 — 确保每项都尝试获取全文后再生成文档"""
        if not self.selected_indices:
            messagebox.showinfo("提示", "请先勾选要导出的法规/案例（至少选择1项）")
            return

        self.export_btn.configure(state=tk.DISABLED, text=" 导出中... ")
        self.status_lbl.configure(text="正在获取全文并生成 Word 文档，请稍候...")

        def export_thread():
            try:
                selected = []
                for idx in sorted(self.selected_indices):
                    if idx >= len(self.search_results):
                        continue
                    item = self.search_results[idx]

                    # 获取全文（优先使用已缓存的，没有则实时多策略抓取）
                    content = item.get("full_content", "")
                    got_full = item.get("full_content_fetched", False)

                    if not content or not got_full:
                        law_title = re.sub(r'^\[.*?\]\s*', '', item["title"]).strip()
                        fetched = searcher.fetch_law_full_text(
                            item.get("url", ""), law_title, item.get("snippet", ""))
                        if fetched["success"]:
                            content = fetched["content"]
                            got_full = len(content) > 200
                        else:
                            content = content or item.get("snippet", "")

                    selected.append({
                        "title": item["title"],
                        "content": content,
                        "url": item.get("url", ""),
                        "source": item.get("source", ""),
                        "full_content_fetched": got_full,
                    })

                # 生成文档
                if len(selected) == 1:
                    si = {
                        "source": selected[0].get("source", ""),
                        "url": selected[0].get("url", ""),
                    }
                    path = doc_generator.create_document(
                        selected[0]["title"],
                        selected[0]["content"],
                        source_info=si,
                        full_content_fetched=selected[0].get("full_content_fetched", False),
                    )
                else:
                    path = doc_generator.create_batch_document(
                        selected,
                    )

                self.root.after(0, lambda: self._on_export_done(path, len(selected)))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("导出失败",
                    f"Word 文档导出失败：{str(e)}"))

        threading.Thread(target=export_thread, daemon=True).start()

    def _on_export_done(self, path, count):
        self.export_btn.configure(state=tk.NORMAL, text=" 导出 Word 文档 ")
        self.status_lbl.configure(text=f"已成功导出 {count} 篇文档至桌面")
        ok = messagebox.askyesno("导出成功",
            f"已成功生成 Word 文档！\n\n保存位置：{path}\n\n是否立即打开查看？")
        if ok:
            try:
                os.startfile(path)
            except Exception:
                messagebox.showinfo("提示", f"文件已保存至：{path}")
        self._update_status()

    def clear_all(self):
        self.search_results = []
        self.check_vars = {}
        self.selected_indices.clear()
        self.sel_all_var.set(0)

        for w in self.list_frame.winfo_children():
            w.destroy()
        self.count_lbl.configure(text="0 条")
        self.src_lbl.configure(text="")

        self.preview.configure(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.configure(state=tk.DISABLED)

        self._show_welcome()
        self.status_lbl.configure(text="已清空，请输入关键词搜索")
        self.entry.focus_set()

    def _update_status(self):
        n = len(self.selected_indices)
        total = len(self.search_results)
        if n > 0:
            self.status_lbl.configure(text=f"已选择 {n} 项 / 共 {total} 项，可点击「导出 Word 文档」")
        else:
            self.status_lbl.configure(text="请勾选要导出的法规/案例")


def main():
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = LawSearchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
