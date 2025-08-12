import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading
import webbrowser
import json
import os
from urllib.parse import urljoin, urlparse

class MxideDocTool:
    def __init__(self, root):
        self.root = root
        self.root.title("55IDE文档查询工具")
        self.root.geometry("1200x800")
        
        # 数据库初始化
        self.db_name = "mxide_docs.db"
        self.init_database()
        
        # 创建界面
        self.create_widgets()
        
        # 加载数据
        self.load_documents()
        self.load_tags()
        self.load_favorites()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS documents
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      url TEXT UNIQUE NOT NULL,
                      content TEXT,
                      category TEXT,
                      favorite INTEGER DEFAULT 0,
                      tags TEXT)''')
        
        # 创建笔记表
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      doc_id INTEGER,
                      note_title TEXT NOT NULL,
                      note_content TEXT,
                      created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE)''')
        
        # 创建标签表
        c.execute('''CREATE TABLE IF NOT EXISTS tags
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      tag_name TEXT UNIQUE NOT NULL)''')
        
        # 创建文档标签关联表
        c.execute('''CREATE TABLE IF NOT EXISTS document_tags
                     (doc_id INTEGER,
                      tag_id INTEGER,
                      FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE,
                      FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                      PRIMARY KEY (doc_id, tag_id))''')
        
        conn.commit()
        conn.close()

    def create_widgets(self):
        """创建界面组件"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文档浏览页
        self.browse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browse_frame, text="文档浏览")
        
        # 收藏页
        self.favorite_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.favorite_frame, text="我的收藏")
        
        # 标签分类页
        self.tags_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tags_frame, text="标签分类")
        
        # 笔记页
        self.notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notes_frame, text="我的笔记")
        
        # 设置页
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="设置")
        
        # 构建各个页面
        self.create_browse_frame()
        self.create_favorite_frame()
        self.create_tags_frame()
        self.create_notes_frame()
        self.create_settings_frame()

    def create_browse_frame(self):
        """创建文档浏览界面"""
        # 搜索框
        search_frame = ttk.Frame(self.browse_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 收藏按钮
        self.favorite_btn = ttk.Button(search_frame, text="收藏选中", command=self.toggle_favorite)
        self.favorite_btn.pack(side=tk.RIGHT, padx=5)
        
        # 主框架分为左右两部分
        main_frame = ttk.Frame(self.browse_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧文档列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 列表框和滚动条
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.doc_listbox = tk.Listbox(list_frame)
        self.doc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.doc_listbox.bind('<<ListboxSelect>>', self.on_doc_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.doc_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.doc_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧详细信息
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 文档信息区域
        info_frame = ttk.LabelFrame(right_frame, text="文档信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 标签区域
        tag_frame = ttk.LabelFrame(right_frame, text="标签")
        tag_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.tag_listbox = tk.Listbox(tag_frame, height=4)
        self.tag_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加标签区域
        add_tag_frame = ttk.Frame(tag_frame)
        add_tag_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.tag_var = tk.StringVar()
        self.tag_entry = ttk.Entry(add_tag_frame, textvariable=self.tag_var)
        self.tag_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_tag_frame, text="添加标签", command=self.add_tag_to_doc).pack(side=tk.RIGHT)
        
        # 内容显示区域
        content_frame = ttk.LabelFrame(right_frame, text="文档内容")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.content_text = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=text_scrollbar.set)
        
        # 配置文档内容文本框的标签样式
        self.content_text.tag_config("heading", font=("微软雅黑", 14, "bold"), foreground="blue")
        self.content_text.tag_config("subheading", font=("微软雅黑", 12, "bold"), foreground="darkblue")
        self.content_text.tag_config("normal", font=("微软雅黑", 10))
        self.content_text.tag_config("list", font=("微软雅黑", 10), lmargin1=20, lmargin2=20)
        
        # 底部按钮
        button_frame = ttk.Frame(self.browse_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="抓取文档", command=self.start_crawling).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="在浏览器中打开", command=self.open_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.load_documents).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="添加笔记", command=self.add_note_to_doc).pack(side=tk.LEFT, padx=5)

    def create_favorite_frame(self):
        """创建收藏界面"""
        # 主框架分为左右两部分
        main_frame = ttk.Frame(self.favorite_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧收藏列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 收藏列表
        fav_list_frame = ttk.Frame(left_frame)
        fav_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fav_listbox = tk.Listbox(fav_list_frame)
        self.fav_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.fav_listbox.bind('<<ListboxSelect>>', self.on_fav_select)
        
        scrollbar = ttk.Scrollbar(fav_list_frame, orient=tk.VERTICAL, command=self.fav_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fav_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧详细信息
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 文档信息区域
        info_frame = ttk.LabelFrame(right_frame, text="文档信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.fav_info_text = tk.Text(info_frame, height=6, wrap=tk.WORD)
        self.fav_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 内容显示区域
        content_frame = ttk.LabelFrame(right_frame, text="文档内容")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fav_content_text = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.fav_content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.fav_content_text.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fav_content_text.config(yscrollcommand=text_scrollbar.set)
        
        # 配置文档内容文本框的标签样式
        self.fav_content_text.tag_config("heading", font=("微软雅黑", 14, "bold"), foreground="blue")
        self.fav_content_text.tag_config("subheading", font=("微软雅黑", 12, "bold"), foreground="darkblue")
        self.fav_content_text.tag_config("normal", font=("微软雅黑", 10))
        self.fav_content_text.tag_config("list", font=("微软雅黑", 10), lmargin1=20, lmargin2=20)
        
        # 底部按钮
        button_frame = ttk.Frame(self.favorite_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="取消收藏", command=self.remove_favorite).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="在浏览器中打开", command=self.open_fav_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.load_favorites).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="添加笔记", command=self.add_note_to_fav).pack(side=tk.LEFT, padx=5)

    def create_tags_frame(self):
        """创建标签分类界面"""
        # 主框架分为左右两部分
        main_frame = ttk.Frame(self.tags_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧标签列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tag_list_frame = ttk.LabelFrame(left_frame, text="标签列表")
        tag_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.all_tags_listbox = tk.Listbox(tag_list_frame)
        self.all_tags_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.all_tags_listbox.bind('<<ListboxSelect>>', self.on_tag_select)
        
        scrollbar = ttk.Scrollbar(tag_list_frame, orient=tk.VERTICAL, command=self.all_tags_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.all_tags_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧文档列表
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        doc_list_frame = ttk.LabelFrame(right_frame, text="标签下的文档")
        doc_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tag_docs_listbox = tk.Listbox(doc_list_frame)
        self.tag_docs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tag_docs_listbox.bind('<<ListboxSelect>>', self.on_tag_doc_select)
        
        scrollbar2 = ttk.Scrollbar(doc_list_frame, orient=tk.VERTICAL, command=self.tag_docs_listbox.yview)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_docs_listbox.config(yscrollcommand=scrollbar2.set)
        
        # 文档内容显示
        content_frame = ttk.LabelFrame(right_frame, text="文档内容")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tag_doc_content = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.tag_doc_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.tag_doc_content.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tag_doc_content.config(yscrollcommand=text_scrollbar.set)
        
        # 配置文档内容文本框的标签样式
        self.tag_doc_content.tag_config("heading", font=("微软雅黑", 14, "bold"), foreground="blue")
        self.tag_doc_content.tag_config("subheading", font=("微软雅黑", 12, "bold"), foreground="darkblue")
        self.tag_doc_content.tag_config("normal", font=("微软雅黑", 10))
        self.tag_doc_content.tag_config("list", font=("微软雅黑", 10), lmargin1=20, lmargin2=20)
        
        # 底部按钮
        button_frame = ttk.Frame(self.tags_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="刷新标签", command=self.load_tags).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="在浏览器中打开", command=self.open_tag_doc_in_browser).pack(side=tk.LEFT, padx=5)

    def create_notes_frame(self):
        """创建笔记界面"""
        # 主框架分为左右两部分
        main_frame = ttk.Frame(self.notes_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧笔记列表
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        notes_list_frame = ttk.LabelFrame(left_frame, text="笔记列表")
        notes_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notes_listbox = tk.Listbox(notes_list_frame)
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)
        
        scrollbar = ttk.Scrollbar(notes_list_frame, orient=tk.VERTICAL, command=self.notes_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_listbox.config(yscrollcommand=scrollbar.set)
        
        # 右侧笔记内容
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 笔记信息
        info_frame = ttk.LabelFrame(right_frame, text="笔记信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.note_info_text = tk.Text(info_frame, height=4, wrap=tk.WORD)
        self.note_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 笔记内容
        content_frame = ttk.LabelFrame(right_frame, text="笔记内容")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.note_content_text = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.note_content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.note_content_text.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.note_content_text.config(yscrollcommand=text_scrollbar.set)
        
        # 配置笔记内容文本框的标签样式
        self.note_content_text.tag_config("heading", font=("微软雅黑", 14, "bold"), foreground="blue")
        self.note_content_text.tag_config("subheading", font=("微软雅黑", 12, "bold"), foreground="darkblue")
        self.note_content_text.tag_config("normal", font=("微软雅黑", 10))
        
        # 底部按钮
        button_frame = ttk.Frame(self.notes_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="新建笔记", command=self.create_new_note).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="编辑笔记", command=self.edit_selected_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除笔记", command=self.delete_selected_note).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="刷新列表", command=self.load_notes).pack(side=tk.LEFT, padx=5)

    def create_settings_frame(self):
        """创建设置界面"""
        # 数据库信息
        db_frame = ttk.LabelFrame(self.settings_frame, text="数据库")
        db_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(db_frame, text="导出数据", command=self.export_data).pack(pady=5)
        ttk.Button(db_frame, text="导入数据", command=self.import_data).pack(pady=5)
        ttk.Button(db_frame, text="清空数据库", command=self.clear_database).pack(pady=5)
        
        # 关于信息
        about_frame = ttk.LabelFrame(self.settings_frame, text="关于")
        about_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(about_frame, text="55IDE文档查询工具 v1.0").pack(anchor=tk.W)
        ttk.Label(about_frame, text="帮助你在开发游戏时快速查询相关文档").pack(anchor=tk.W)
        
        ttk.Button(about_frame, text="访问55IDE官网", command=lambda: webbrowser.open("http://doc.mxide.com/")).pack(pady=5)

    def load_documents(self):
        """加载文档列表"""
        self.doc_listbox.delete(0, tk.END)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        search_term = self.search_var.get()
        if search_term:
            c.execute("SELECT id, title FROM documents WHERE title LIKE ? ORDER BY title", (f"%{search_term}%",))
        else:
            c.execute("SELECT id, title FROM documents ORDER BY title")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            self.doc_listbox.insert(tk.END, row[1])

    def load_favorites(self):
        """加载收藏列表"""
        self.fav_listbox.delete(0, tk.END)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT id, title FROM documents WHERE favorite=1 ORDER BY title")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            self.fav_listbox.insert(tk.END, row[1])

    def load_tags(self):
        """加载所有标签"""
        self.all_tags_listbox.delete(0, tk.END)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT tag_name FROM tags ORDER BY tag_name")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            self.all_tags_listbox.insert(tk.END, row[0])

    def load_notes(self):
        """加载笔记列表"""
        self.notes_listbox.delete(0, tk.END)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""SELECT n.id, n.note_title, d.title 
                     FROM notes n 
                     LEFT JOIN documents d ON n.doc_id = d.id 
                     ORDER BY n.created_time DESC""")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            doc_title = row[2] if row[2] else "无关联文档"
            display_text = f"{row[1]} ({doc_title})"
            self.notes_listbox.insert(tk.END, display_text)

    def on_search_change(self, *args):
        """搜索框内容变化时触发"""
        self.load_documents()

    def on_doc_select(self, event):
        """文档列表选择事件"""
        selection = self.doc_listbox.curselection()
        if selection:
            index = selection[0]
            title = self.doc_listbox.get(index)
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT id, content, url, tags FROM documents WHERE title=?", (title,))
            row = c.fetchone()
            conn.close()
            
            if row:
                # 显示文档内容并美化格式
                self.content_text.delete(1.0, tk.END)
                self.format_and_display_content(self.content_text, row[1] if row[1] else "")
                
                # 显示文档信息
                self.info_text.delete(1.0, tk.END)
                info = f"标题: {title}\nURL: {row[2]}\n标签: {row[3] if row[3] else '无'}"
                self.info_text.insert(tk.END, info)
                
                # 加载标签
                self.load_doc_tags(row[0])

    def on_fav_select(self, event):
        """收藏列表选择事件"""
        selection = self.fav_listbox.curselection()
        if selection:
            index = selection[0]
            title = self.fav_listbox.get(index)
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT id, content, url, tags FROM documents WHERE title=?", (title,))
            row = c.fetchone()
            conn.close()
            
            if row:
                # 显示文档内容并美化格式
                self.fav_content_text.delete(1.0, tk.END)
                self.format_and_display_content(self.fav_content_text, row[1] if row[1] else "")
                
                # 显示文档信息
                self.fav_info_text.delete(1.0, tk.END)
                info = f"标题: {title}\nURL: {row[2]}\n标签: {row[3] if row[3] else '无'}"
                self.fav_info_text.insert(tk.END, info)

    def on_tag_select(self, event):
        """标签选择事件"""
        selection = self.all_tags_listbox.curselection()
        if selection:
            index = selection[0]
            tag_name = self.all_tags_listbox.get(index)
            
            # 清空文档列表
            self.tag_docs_listbox.delete(0, tk.END)
            
            # 查询该标签下的文档
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""SELECT d.id, d.title 
                         FROM documents d
                         JOIN document_tags dt ON d.id = dt.doc_id
                         JOIN tags t ON dt.tag_id = t.id
                         WHERE t.tag_name = ?
                         ORDER BY d.title""", (tag_name,))
            rows = c.fetchall()
            conn.close()
            
            for row in rows:
                self.tag_docs_listbox.insert(tk.END, row[1])

    def on_tag_doc_select(self, event):
        """标签下文档选择事件"""
        selection = self.tag_docs_listbox.curselection()
        if selection:
            index = selection[0]
            title = self.tag_docs_listbox.get(index)
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT content FROM documents WHERE title=?", (title,))
            row = c.fetchone()
            conn.close()
            
            if row:
                self.tag_doc_content.delete(1.0, tk.END)
                self.format_and_display_content(self.tag_doc_content, row[0] if row[0] else "")

    def on_note_select(self, event):
        """笔记选择事件"""
        selection = self.notes_listbox.curselection()
        if selection:
            index = selection[0]
            # 从显示文本中提取笔记标题
            display_text = self.notes_listbox.get(index)
            note_title = display_text.split(" (")[0]  # 提取笔记标题部分
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""SELECT n.id, n.note_title, n.note_content, n.created_time, d.title 
                         FROM notes n 
                         LEFT JOIN documents d ON n.doc_id = d.id 
                         WHERE n.note_title = ?""", (note_title,))
            row = c.fetchone()
            conn.close()
            
            if row:
                # 显示笔记信息
                self.note_info_text.delete(1.0, tk.END)
                doc_title = row[4] if row[4] else "无关联文档"
                info = f"标题: {row[1]}\n关联文档: {doc_title}\n创建时间: {row[3]}"
                self.note_info_text.insert(tk.END, info)
                
                # 显示笔记内容并美化格式
                self.note_content_text.delete(1.0, tk.END)
                self.format_and_display_content(self.note_content_text, row[2] if row[2] else "")

    def format_and_display_content(self, text_widget, content):
        """
        格式化并显示内容，提高可读性
        """
        # 清空文本框
        text_widget.delete(1.0, tk.END)
        
        if not content:
            return
        
        # 按行处理内容
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 根据行内容判断样式
            if line.startswith('# ') or (len(line) < 50 and line.isupper()):
                # 大标题
                text_widget.insert(tk.END, line + '\n', "heading")
            elif line.startswith('## ') or (len(line) < 80 and line.isupper()):
                # 小标题
                text_widget.insert(tk.END, line + '\n', "subheading")
            elif line.startswith(('-', '*', '•', '·')) or (':' in line and len(line) < 100):
                # 列表项
                text_widget.insert(tk.END, line + '\n', "list")
            else:
                # 普通文本
                text_widget.insert(tk.END, line + '\n', "normal")
        
        # 确保至少添加一些内容
        if not text_widget.get(1.0, tk.END).strip():
            text_widget.insert(tk.END, content, "normal")

    def load_doc_tags(self, doc_id):
        """加载文档的标签"""
        self.tag_listbox.delete(0, tk.END)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""SELECT t.tag_name 
                     FROM tags t
                     JOIN document_tags dt ON t.id = dt.tag_id
                     WHERE dt.doc_id = ?""", (doc_id,))
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            self.tag_listbox.insert(tk.END, row[0])

    def add_tag_to_doc(self):
        """为选中的文档添加标签"""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        tag_name = self.tag_var.get().strip()
        if not tag_name:
            messagebox.showwarning("警告", "请输入标签名称")
            return
            
        index = selection[0]
        title = self.doc_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # 检查标签是否已存在，不存在则创建
        c.execute("SELECT id FROM tags WHERE tag_name=?", (tag_name,))
        tag_row = c.fetchone()
        if not tag_row:
            c.execute("INSERT INTO tags (tag_name) VALUES (?)", (tag_name,))
            tag_id = c.lastrowid
        else:
            tag_id = tag_row[0]
        
        # 获取文档ID
        c.execute("SELECT id FROM documents WHERE title=?", (title,))
        doc_row = c.fetchone()
        if doc_row:
            doc_id = doc_row[0]
            
            # 检查文档是否已有该标签
            c.execute("SELECT * FROM document_tags WHERE doc_id=? AND tag_id=?", (doc_id, tag_id))
            if not c.fetchone():
                c.execute("INSERT INTO document_tags (doc_id, tag_id) VALUES (?, ?)", (doc_id, tag_id))
                conn.commit()
                messagebox.showinfo("成功", f"已为文档添加标签: {tag_name}")
                self.tag_var.set("")  # 清空输入框
                self.load_doc_tags(doc_id)  # 刷新标签列表
                self.load_tags()  # 刷新所有标签列表
            else:
                messagebox.showwarning("警告", "该文档已包含此标签")
        conn.close()

    def toggle_favorite(self):
        """切换选中文档的收藏状态"""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.doc_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT favorite FROM documents WHERE title=?", (title,))
        row = c.fetchone()
        if row:
            new_favorite = 0 if row[0] == 1 else 1
            c.execute("UPDATE documents SET favorite=? WHERE title=?", (new_favorite, title))
            conn.commit()
            status = "已收藏" if new_favorite == 1 else "已取消收藏"
            messagebox.showinfo("提示", f"文档{status}")
        conn.close()
        self.load_favorites()

    def remove_favorite(self):
        """取消收藏"""
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.fav_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("UPDATE documents SET favorite=0 WHERE title=?", (title,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("提示", "已取消收藏")
        self.load_favorites()

    def open_in_browser(self):
        """在浏览器中打开选中的文档"""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.doc_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT url FROM documents WHERE title=?", (title,))
        row = c.fetchone()
        conn.close()
        
        if row:
            webbrowser.open(row[0])

    def open_fav_in_browser(self):
        """在浏览器中打开选中的收藏文档"""
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.fav_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT url FROM documents WHERE title=?", (title,))
        row = c.fetchone()
        conn.close()
        
        if row:
            webbrowser.open(row[0])

    def open_tag_doc_in_browser(self):
        """在浏览器中打开标签下的选中文档"""
        selection = self.tag_docs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.tag_docs_listbox.get(index)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT url FROM documents WHERE title=?", (title,))
        row = c.fetchone()
        conn.close()
        
        if row:
            webbrowser.open(row[0])

    def add_note_to_doc(self):
        """为选中的文档添加笔记"""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.doc_listbox.get(index)
        
        # 创建笔记对话框
        self.create_note_dialog(title)

    def add_note_to_fav(self):
        """为选中的收藏文档添加笔记"""
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文档")
            return
            
        index = selection[0]
        title = self.fav_listbox.get(index)
        
        # 创建笔记对话框
        self.create_note_dialog(title)

    def create_note_dialog(self, doc_title):
        """创建笔记对话框"""
        # 创建顶层窗口
        dialog = tk.Toplevel(self.root)
        dialog.title(f"为文档 '{doc_title}' 添加笔记")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 获取文档ID
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT id FROM documents WHERE title=?", (doc_title,))
        doc_row = c.fetchone()
        doc_id = doc_row[0] if doc_row else None
        conn.close()
        
        # 笔记标题
        ttk.Label(dialog, text="笔记标题:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var)
        title_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # 笔记内容
        ttk.Label(dialog, text="笔记内容:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        content_text = tk.Text(dialog, wrap=tk.WORD, font=("微软雅黑", 10))
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(content_text, orient=tk.VERTICAL, command=content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_note():
            note_title = title_var.get().strip()
            note_content = content_text.get(1.0, tk.END).strip()
            
            if not note_title:
                messagebox.showwarning("警告", "请输入笔记标题")
                return
                
            if not note_content:
                messagebox.showwarning("警告", "请输入笔记内容")
                return
                
            # 保存笔记
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO notes (doc_id, note_title, note_content) VALUES (?, ?, ?)",
                         (doc_id, note_title, note_content))
                conn.commit()
                messagebox.showinfo("成功", "笔记保存成功")
                dialog.destroy()
                self.load_notes()  # 刷新笔记列表
            except Exception as e:
                messagebox.showerror("错误", f"保存笔记时出错: {str(e)}")
            finally:
                conn.close()
        
        ttk.Button(button_frame, text="保存", command=save_note).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def create_new_note(self):
        """创建新笔记（不关联任何文档）"""
        # 创建顶层窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("创建新笔记")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 笔记标题
        ttk.Label(dialog, text="笔记标题:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var)
        title_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # 笔记内容
        ttk.Label(dialog, text="笔记内容:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        content_text = tk.Text(dialog, wrap=tk.WORD, font=("微软雅黑", 10))
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(content_text, orient=tk.VERTICAL, command=content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_note():
            note_title = title_var.get().strip()
            note_content = content_text.get(1.0, tk.END).strip()
            
            if not note_title:
                messagebox.showwarning("警告", "请输入笔记标题")
                return
                
            if not note_content:
                messagebox.showwarning("警告", "请输入笔记内容")
                return
                
            # 保存笔记
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO notes (doc_id, note_title, note_content) VALUES (?, ?, ?)",
                         (None, note_title, note_content))
                conn.commit()
                messagebox.showinfo("成功", "笔记保存成功")
                dialog.destroy()
                self.load_notes()  # 刷新笔记列表
            except Exception as e:
                messagebox.showerror("错误", f"保存笔记时出错: {str(e)}")
            finally:
                conn.close()
        
        ttk.Button(button_frame, text="保存", command=save_note).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def edit_selected_note(self):
        """编辑选中的笔记"""
        selection = self.notes_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个笔记")
            return
            
        index = selection[0]
        display_text = self.notes_listbox.get(index)
        note_title = display_text.split(" (")[0]
        
        # 获取笔记详细信息
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""SELECT n.id, n.note_title, n.note_content, n.created_time, d.title 
                     FROM notes n 
                     LEFT JOIN documents d ON n.doc_id = d.id 
                     WHERE n.note_title = ?""", (note_title,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            messagebox.showerror("错误", "无法找到选中的笔记")
            return
            
        note_id, old_title, old_content, created_time, doc_title = row
        
        # 创建编辑对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑笔记: {old_title}")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 笔记标题
        ttk.Label(dialog, text="笔记标题:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        title_var = tk.StringVar(value=old_title)
        title_entry = ttk.Entry(dialog, textvariable=title_var)
        title_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # 笔记内容
        ttk.Label(dialog, text="笔记内容:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        content_text = tk.Text(dialog, wrap=tk.WORD, font=("微软雅黑", 10))
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        content_text.insert(tk.END, old_content)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(content_text, orient=tk.VERTICAL, command=content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_note():
            new_title = title_var.get().strip()
            new_content = content_text.get(1.0, tk.END).strip()
            
            if not new_title:
                messagebox.showwarning("警告", "请输入笔记标题")
                return
                
            if not new_content:
                messagebox.showwarning("警告", "请输入笔记内容")
                return
                
            # 更新笔记
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            try:
                c.execute("UPDATE notes SET note_title=?, note_content=? WHERE id=?",
                         (new_title, new_content, note_id))
                conn.commit()
                messagebox.showinfo("成功", "笔记更新成功")
                dialog.destroy()
                self.load_notes()  # 刷新笔记列表
            except Exception as e:
                messagebox.showerror("错误", f"更新笔记时出错: {str(e)}")
            finally:
                conn.close()
        
        ttk.Button(button_frame, text="保存", command=save_note).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def delete_selected_note(self):
        """删除选中的笔记"""
        selection = self.notes_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个笔记")
            return
            
        if not messagebox.askyesno("确认", "确定要删除选中的笔记吗？此操作不可恢复。"):
            return
            
        index = selection[0]
        display_text = self.notes_listbox.get(index)
        note_title = display_text.split(" (")[0]
        
        # 删除笔记
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute("DELETE FROM notes WHERE note_title=?", (note_title,))
            conn.commit()
            messagebox.showinfo("成功", "笔记删除成功")
            self.load_notes()  # 刷新笔记列表
        except Exception as e:
            messagebox.showerror("错误", f"删除笔记时出错: {str(e)}")
        finally:
            conn.close()

    def start_crawling(self):
        """开始抓取文档"""
        threading.Thread(target=self.crawl_documents, daemon=True).start()
        messagebox.showinfo("提示", "开始抓取文档，这可能需要一些时间...")

    def crawl_documents(self):
        """抓取文档"""
        try:
            # 这里我们模拟抓取几个主要页面
            urls = [
                "http://doc.mxide.com/",
                "http://doc.mxide.com/tech/",
                "http://doc.mxide.com/demo/"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 获取页面标题
                    title = soup.title.string if soup.title else url
                    
                    # 获取页面内容
                    content = ""
                    for paragraph in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                        content += paragraph.get_text() + "\n"
                    
                    # 保存到数据库
                    self.save_document(title, url, content)
                    
                except Exception as e:
                    print(f"抓取 {url} 时出错: {e}")
            
            # 在主线程中更新UI
            self.root.after(0, self.load_documents)
            self.root.after(0, lambda: messagebox.showinfo("完成", "文档抓取完成"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"抓取文档时出错: {str(e)}"))

    def save_document(self, title, url, content):
        """保存文档到数据库"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute("INSERT OR REPLACE INTO documents (title, url, content) VALUES (?, ?, ?)",
                     (title, url, content))
            conn.commit()
        except Exception as e:
            print(f"保存文档 {title} 时出错: {e}")
        finally:
            conn.close()

    def export_data(self):
        """导出数据"""
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not file_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # 导出文档
            c.execute("SELECT * FROM documents")
            doc_rows = c.fetchall()
            documents = []
            for row in doc_rows:
                documents.append({
                    'id': row[0],
                    'title': row[1],
                    'url': row[2],
                    'content': row[3],
                    'category': row[4],
                    'favorite': row[5],
                    'tags': row[6]
                })
            
            # 导出笔记
            c.execute("SELECT * FROM notes")
            note_rows = c.fetchall()
            notes = []
            for row in note_rows:
                notes.append({
                    'id': row[0],
                    'doc_id': row[1],
                    'note_title': row[2],
                    'note_content': row[3],
                    'created_time': row[4]
                })
            
            # 导出标签
            c.execute("SELECT * FROM tags")
            tag_rows = c.fetchall()
            tags = []
            for row in tag_rows:
                tags.append({
                    'id': row[0],
                    'tag_name': row[1]
                })
            
            # 导出文档标签关联
            c.execute("SELECT * FROM document_tags")
            doc_tag_rows = c.fetchall()
            document_tags = []
            for row in doc_tag_rows:
                document_tags.append({
                    'doc_id': row[0],
                    'tag_id': row[1]
                })
            
            conn.close()
            
            data = {
                'documents': documents,
                'notes': notes,
                'tags': tags,
                'document_tags': document_tags
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            messagebox.showinfo("成功", "数据导出成功")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据时出错: {str(e)}")

    def import_data(self):
        """导入数据"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # 导入文档
            if 'documents' in data:
                for item in data['documents']:
                    c.execute("""INSERT OR REPLACE INTO documents 
                                (id, title, url, content, category, favorite, tags) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                             (item['id'], item['title'], item['url'], item['content'], 
                              item['category'], item['favorite'], item['tags']))
            
            # 导入笔记
            if 'notes' in data:
                for item in data['notes']:
                    c.execute("""INSERT OR REPLACE INTO notes 
                                (id, doc_id, note_title, note_content, created_time) 
                                VALUES (?, ?, ?, ?, ?)""",
                             (item['id'], item['doc_id'], item['note_title'], 
                              item['note_content'], item['created_time']))
            
            # 导入标签
            if 'tags' in data:
                for item in data['tags']:
                    c.execute("INSERT OR REPLACE INTO tags (id, tag_name) VALUES (?, ?)",
                             (item['id'], item['tag_name']))
            
            # 导入文档标签关联
            if 'document_tags' in data:
                for item in data['document_tags']:
                    c.execute("INSERT OR REPLACE INTO document_tags (doc_id, tag_id) VALUES (?, ?)",
                             (item['doc_id'], item['tag_id']))
            
            conn.commit()
            conn.close()
            
            self.load_documents()
            self.load_favorites()
            self.load_tags()
            self.load_notes()
            messagebox.showinfo("成功", "数据导入成功")
        except Exception as e:
            messagebox.showerror("错误", f"导入数据时出错: {str(e)}")

    def clear_database(self):
        """清空数据库"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？此操作不可恢复。"):
            try:
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute("DELETE FROM documents")
                c.execute("DELETE FROM notes")
                c.execute("DELETE FROM tags")
                c.execute("DELETE FROM document_tags")
                conn.commit()
                conn.close()
                
                self.load_documents()
                self.load_favorites()
                self.load_tags()
                self.load_notes()
                messagebox.showinfo("成功", "数据库已清空")
            except Exception as e:
                messagebox.showerror("错误", f"清空数据库时出错: {str(e)}")


def main():
    root = tk.Tk()
    app = MxideDocTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()