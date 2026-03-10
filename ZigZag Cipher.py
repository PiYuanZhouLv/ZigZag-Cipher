import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
from PIL import Image, ImageTk
import os
import threading
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# 深色主题颜色方案
# ──────────────────────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#0f1117",
    "surface": "#1a1d27",
    "surface2": "#22263a",
    "border": "#2e3350",
    "accent": "#5b6af0",
    "accent_hover": "#7b8af8",
    "accent_dim": "#2d3473",
    "success": "#3ecf8e",
    "warning": "#f0a05b",
    "danger": "#f06b6b",
    "text": "#e8eaf6",
    "text_dim": "#8b91b8",
    "text_muted": "#555b7e",
    "panel_bg": "#141720",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 9),
    "badge": ("Segoe UI", 8, "bold"),
}

# ──────────────────────────────────────────────────────────────────────────────
# 加密 / 解密核心
# ──────────────────────────────────────────────────────────────────────────────


class ZigzagCipher:

    # ── public: encrypt ───────────────────────────────────────────────────────

    def zigzag_encrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._zigzag_encrypt_2d, channels)

    def zigzag_encrypt_reverse(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._zigzag_encrypt_reverse_2d, channels)

    def outer_spiral_encrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._outer_spiral_encrypt_2d, channels)

    def diagonal_encrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._diagonal_encrypt_2d, channels)

    # ── 新增的加密变种 ───────────────────────────────────────────────────────

    def multi_zigzag_encrypt(self, matrix, levels=3, channels=None):
        """多级Zigzag加密 - 对图像进行多次Zigzag变换"""
        result = matrix.copy()
        for _ in range(levels):
            result = self._apply_2d_channels(result, self._zigzag_encrypt_2d, channels)
        return result

    def block_zigzag_encrypt(self, matrix, block_size=8, channels=None):
        """分块Zigzag加密 - 将图像分块后每块独立进行Zigzag变换"""
        if matrix.ndim == 3:
            result = matrix.copy()
            for c in range(matrix.shape[2]):
                if channels is None or c in channels:
                    result[:, :, c] = self._block_zigzag_encrypt_2d(matrix[:, :, c], block_size)
            return result
        return self._block_zigzag_encrypt_2d(matrix, block_size)

    def snake_encrypt(self, matrix, channels=None):
        """蛇形加密 - 按行来回扫描（S形）"""
        return self._apply_2d_channels(matrix, self._snake_encrypt_2d, channels)

    def inner_spiral_encrypt(self, matrix, channels=None):
        """内螺旋加密 - 从内向外螺旋"""
        return self._apply_2d_channels(matrix, self._inner_spiral_encrypt_2d, channels)

    def xor_zigzag_encrypt(self, matrix, key=42, channels=None):
        """结合XOR的Zigzag加密 - 先Zigzag置乱，再与密钥XOR"""
        # 先Zigzag置乱
        scrambled = self._apply_2d_channels(matrix, self._zigzag_encrypt_2d, channels)
        # 再XOR加密（只对选中的通道进行XOR）
        if matrix.ndim == 3:
            result = scrambled.copy()
            for c in range(matrix.shape[2]):
                if channels is None or c in channels:
                    result[:, :, c] = np.bitwise_xor(scrambled[:, :, c], key)
            return result
        return np.bitwise_xor(scrambled, key)

    def row_column_zigzag_encrypt(self, matrix, channels=None):
        """行-列Zigzag加密 - 先对行做Zigzag，再对列做Zigzag"""
        # 先对行方向做Zigzag
        row_scrambled = self._apply_2d_channels(matrix, self._zigzag_encrypt_2d, channels)
        # 转置后对列方向做Zigzag
        if matrix.ndim == 3:
            transposed = row_scrambled.transpose(1, 0, 2)
            col_scrambled = self._apply_2d_channels(transposed, self._zigzag_encrypt_2d, channels)
            return col_scrambled.transpose(1, 0, 2)
        else:
            transposed = row_scrambled.T
            col_scrambled = self._apply_2d_channels(transposed, self._zigzag_encrypt_2d, channels)
            return col_scrambled.T

    # ── public: decrypt ───────────────────────────────────────────────────────

    def zigzag_decrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._zigzag_decrypt_2d, channels)

    def zigzag_decrypt_reverse(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._zigzag_decrypt_reverse_2d, channels)

    def outer_spiral_decrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._outer_spiral_decrypt_2d, channels)

    def diagonal_decrypt(self, matrix, channels=None):
        return self._apply_2d_channels(matrix, self._diagonal_decrypt_2d, channels)

    # ── 新增的解密变种 ───────────────────────────────────────────────────────

    def multi_zigzag_decrypt(self, matrix, levels=3, channels=None):
        """多级Zigzag解密"""
        result = matrix.copy()
        for _ in range(levels):
            result = self._apply_2d_channels(result, self._zigzag_decrypt_2d, channels)
        return result

    def block_zigzag_decrypt(self, matrix, block_size=8, channels=None):
        """分块Zigzag解密"""
        if matrix.ndim == 3:
            result = matrix.copy()
            for c in range(matrix.shape[2]):
                if channels is None or c in channels:
                    result[:, :, c] = self._block_zigzag_decrypt_2d(matrix[:, :, c], block_size)
            return result
        return self._block_zigzag_decrypt_2d(matrix, block_size)

    def snake_decrypt(self, matrix, channels=None):
        """蛇形解密"""
        return self._apply_2d_channels(matrix, self._snake_decrypt_2d, channels)

    def inner_spiral_decrypt(self, matrix, channels=None):
        """内螺旋解密"""
        return self._apply_2d_channels(matrix, self._inner_spiral_decrypt_2d, channels)

    def xor_zigzag_decrypt(self, matrix, key=42, channels=None):
        """结合XOR的Zigzag解密 - 先XOR解密，再Zigzag还原"""
        # 先XOR解密（只对选中的通道进行XOR）
        if matrix.ndim == 3:
            xored = matrix.copy()
            for c in range(matrix.shape[2]):
                if channels is None or c in channels:
                    xored[:, :, c] = np.bitwise_xor(matrix[:, :, c], key)
        else:
            xored = np.bitwise_xor(matrix, key)
        # 再Zigzag还原
        return self._apply_2d_channels(xored, self._zigzag_decrypt_2d, channels)

    def row_column_zigzag_decrypt(self, matrix, channels=None):
        """行-列Zigzag解密"""
        # 先对列方向解密
        if matrix.ndim == 3:
            transposed = matrix.transpose(1, 0, 2)
            col_descrambled = self._apply_2d_channels(transposed, self._zigzag_decrypt_2d, channels)
            row_descrambled = self._apply_2d_channels(col_descrambled.transpose(1, 0, 2), 
                                                      self._zigzag_decrypt_2d, channels)
        else:
            transposed = matrix.T
            col_descrambled = self._apply_2d_channels(transposed, self._zigzag_decrypt_2d, channels)
            row_descrambled = self._apply_2d_channels(col_descrambled.T, self._zigzag_decrypt_2d, channels)
        return row_descrambled

    # ── helper ─────────────────────────────────────────────────────────────────

    def _apply_2d_channels(self, matrix, fn, channels=None):
        """对指定的通道应用2D变换"""
        if matrix.ndim == 3:
            result = matrix.copy()
            # 如果channels为空列表，表示不处理任何通道
            if channels is not None and len(channels) == 0:
                return result  # 直接返回原图
            for c in range(matrix.shape[2]):
                if channels is None or c in channels:
                    result[:, :, c] = fn(matrix[:, :, c])
            return result
        return fn(matrix)

    # ── 2-D encrypt（打乱：按 zigzag 顺序读取像素，按行写回）──────────────────

    def _zigzag_encrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._zigzag_idx(h, w)):
            result[i // w, i % w] = m[r, c]
        return result

    def _zigzag_encrypt_reverse_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(reversed(self._zigzag_idx(h, w))):
            result[i // w, i % w] = m[r, c]
        return result

    def _outer_spiral_encrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._spiral_idx(h, w)):
            result[i // w, i % w] = m[r, c]
        return result

    def _diagonal_encrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._diagonal_idx(h, w)):
            result[i // w, i % w] = m[r, c]
        return result

    # ── 2-D decrypt（还原：按行读取像素，按 zigzag 顺序写回）────────────────

    def _zigzag_decrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._zigzag_idx(h, w)):
            result[r, c] = m.flat[i]
        return result

    def _zigzag_decrypt_reverse_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(reversed(self._zigzag_idx(h, w))):
            result[r, c] = m.flat[i]
        return result

    def _outer_spiral_decrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._spiral_idx(h, w)):
            result[r, c] = m.flat[i]
        return result

    def _diagonal_decrypt_2d(self, m):
        h, w = m.shape
        result = np.zeros((h, w))
        for i, (r, c) in enumerate(self._diagonal_idx(h, w)):
            result[r, c] = m.flat[i]
        return result

    # ── 新增的2D加密/解密方法 ─────────────────────────────────────────────────

    def _block_zigzag_encrypt_2d(self, m, block_size):
        """2D分块Zigzag加密"""
        h, w = m.shape
        result = np.zeros((h, w))
        
        # 计算块的数量
        blocks_h = (h + block_size - 1) // block_size
        blocks_w = (w + block_size - 1) // block_size
        
        for bh in range(blocks_h):
            for bw in range(blocks_w):
                # 获取当前块的区域
                h_start = bh * block_size
                h_end = min(h_start + block_size, h)
                w_start = bw * block_size
                w_end = min(w_start + block_size, w)
                
                block = m[h_start:h_end, w_start:w_end]
                
                # 对当前块做Zigzag加密
                block_encrypted = self._zigzag_encrypt_2d(block)
                result[h_start:h_end, w_start:w_end] = block_encrypted
        
        return result

    def _block_zigzag_decrypt_2d(self, m, block_size):
        """2D分块Zigzag解密"""
        h, w = m.shape
        result = np.zeros((h, w))
        
        blocks_h = (h + block_size - 1) // block_size
        blocks_w = (w + block_size - 1) // block_size
        
        for bh in range(blocks_h):
            for bw in range(blocks_w):
                h_start = bh * block_size
                h_end = min(h_start + block_size, h)
                w_start = bw * block_size
                w_end = min(w_start + block_size, w)
                
                block = m[h_start:h_end, w_start:w_end]
                
                # 对当前块做Zigzag解密
                block_decrypted = self._zigzag_decrypt_2d(block)
                result[h_start:h_end, w_start:w_end] = block_decrypted
        
        return result

    def _snake_encrypt_2d(self, m):
        """2D蛇形加密 - 按行来回扫描"""
        h, w = m.shape
        result = np.zeros((h, w))
        
        for i in range(h):
            if i % 2 == 0:
                # 偶数行从左到右
                result[i, :] = m[i, :]
            else:
                # 奇数行从右到左
                result[i, :] = m[i, ::-1]
        
        return result

    def _snake_decrypt_2d(self, m):
        """2D蛇形解密"""
        # 蛇形变换是对称的，再次应用即可还原
        return self._snake_encrypt_2d(m)

    def _inner_spiral_encrypt_2d(self, m):
        """2D内螺旋加密"""
        h, w = m.shape
        result = np.zeros((h, w))
        
        indices = self._inner_spiral_idx(h, w)
        for i, (r, c) in enumerate(indices):
            result[i // w, i % w] = m[r, c]
        
        return result

    def _inner_spiral_decrypt_2d(self, m):
        """2D内螺旋解密"""
        h, w = m.shape
        result = np.zeros((h, w))
        
        indices = self._inner_spiral_idx(h, w)
        for i, (r, c) in enumerate(indices):
            result[r, c] = m.flat[i]
        
        return result

    # ── index generators ───────────────────────────────────────────────────────

    def _zigzag_idx(self, rows, cols):
        indices = []
        for s in range(rows + cols - 1):
            if s % 2 == 0:
                i = min(s, rows - 1)
                j = s - i
                while i >= 0 and j < cols:
                    indices.append((i, j))
                    i -= 1
                    j += 1
            else:
                j = min(s, cols - 1)
                i = s - j
                while j >= 0 and i < rows:
                    indices.append((i, j))
                    i += 1
                    j -= 1
        return indices

    def _spiral_idx(self, rows, cols):
        indices = []
        top, bottom, left, right = 0, rows - 1, 0, cols - 1
        while top <= bottom and left <= right:
            for j in range(left, right + 1):
                indices.append((top, j))
            top += 1
            for i in range(top, bottom + 1):
                indices.append((i, right))
            right -= 1
            if top <= bottom:
                for j in range(right, left - 1, -1):
                    indices.append((bottom, j))
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1):
                    indices.append((i, left))
                left += 1
        return indices

    def _diagonal_idx(self, rows, cols):
        indices = []
        for d in range(rows + cols - 1):
            for i in range(max(0, d - cols + 1), min(rows, d + 1)):
                indices.append((i, d - i))
        return indices

    def _inner_spiral_idx(self, rows, cols):
        """生成内螺旋（从中心向外）的索引"""
        indices = []
        
        # 找到中心点
        center_r = rows // 2
        center_c = cols // 2
        
        # 从中心开始螺旋向外
        visited = set()
        r, c = center_r, center_c
        
        # 方向顺序：右、下、左、上、右...
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        direction_idx = 0
        step_size = 1
        step_count = 0
        
        while len(indices) < rows * cols:
            if 0 <= r < rows and 0 <= c < cols and (r, c) not in visited:
                indices.append((r, c))
                visited.add((r, c))
            
            # 移动到下一个位置
            dr, dc = directions[direction_idx]
            r += dr
            c += dc
            
            # 检查是否需要转向
            step_count += 1
            if step_count == step_size:
                step_count = 0
                direction_idx = (direction_idx + 1) % 4
                if direction_idx % 2 == 0:
                    step_size += 1
        
        return indices


# ──────────────────────────────────────────────────────────────────────────────
# 自定义 Tkinter 控件（深色风格）
# ──────────────────────────────────────────────────────────────────────────────


class DarkButton(tk.Button):
    def __init__(self, parent, text, command=None, accent=False, width=130,
                 height=36, **kw):
        self._bg_normal = COLORS["accent"] if accent else COLORS["surface2"]
        self._bg_hover = COLORS["accent_hover"] if accent else COLORS["border"]
        fg = COLORS["text"] if accent else COLORS["text_dim"]
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self._bg_normal,
            fg=fg,
            activebackground=self._bg_hover,
            activeforeground=COLORS["text"],
            font=FONTS["body"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=14,
            pady=7,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
        )
        self.bind("<Enter>", lambda e: self.config(bg=self._bg_hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg_normal))


class Separator(tk.Frame):
    def __init__(self, parent, orient="horizontal", **kw):
        super().__init__(
            parent,
            bg=COLORS["border"],
            height=1 if orient == "horizontal" else 0,
            width=0 if orient == "horizontal" else 1,
            **kw
        )


class ImageCard(tk.Frame):
    """图片预览卡片"""

    def __init__(self, parent, title, badge_text, badge_color, **kw):
        super().__init__(parent, bg=COLORS["surface"], **kw)
        self._build_header(title, badge_text, badge_color)
        self._build_body()

    def _build_header(self, title, badge_text, badge_color):
        hdr = tk.Frame(self, bg=COLORS["surface"])
        hdr.pack(fill=tk.X, padx=14, pady=(12, 0))
        tk.Label(
            hdr,
            text=title,
            font=FONTS["heading"],
            fg=COLORS["text"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT)
        self.badge_label = tk.Label(
            hdr,
            text=badge_text,
            font=FONTS["badge"],
            fg=badge_color,
            bg=COLORS["accent_dim"],
            padx=8,
            pady=2
        )
        self.badge_label.pack(side=tk.RIGHT)

    def _build_body(self):
        Separator(self).pack(fill=tk.X, padx=14, pady=8)
        self.img_frame = tk.Frame(
            self,
            bg=COLORS["panel_bg"],
            width=380,
            height=280
        )
        self.img_frame.pack(padx=14, pady=(0, 8))
        self.img_frame.pack_propagate(False)
        self.img_label = tk.Label(
            self.img_frame,
            bg=COLORS["panel_bg"],
            text="点击加载图片",
            fg=COLORS["text_muted"],
            font=FONTS["body"]
        )
        self.img_label.place(relx=0.5, rely=0.5, anchor="center")
        self.info_label = tk.Label(
            self,
            text="— 暂无图片 —",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["surface"]
        )
        self.info_label.pack(padx=14, pady=(0, 12))


# ──────────────────────────────────────────────────────────────────────────────
# 主 GUI
# ──────────────────────────────────────────────────────────────────────────────

# 更新算法列表
ALGORITHMS = [
    "标准 Zigzag", 
    "反向 Zigzag", 
    "外螺旋", 
    "内螺旋",
    "对角线",
    "多级 Zigzag",
    "分块 Zigzag",
    "蛇形",
    "XOR-Zigzag",
    "行列 Zigzag"
]

# 更新加密映射
ALGO_ENCRYPT = {
    "标准 Zigzag": "zigzag_encrypt",
    "反向 Zigzag": "zigzag_encrypt_reverse",
    "外螺旋": "outer_spiral_encrypt",
    "内螺旋": "inner_spiral_encrypt",
    "对角线": "diagonal_encrypt",
    "多级 Zigzag": "multi_zigzag_encrypt",
    "分块 Zigzag": "block_zigzag_encrypt",
    "蛇形": "snake_encrypt",
    "XOR-Zigzag": "xor_zigzag_encrypt",
    "行列 Zigzag": "row_column_zigzag_encrypt"
}

# 更新解密映射
ALGO_DECRYPT = {
    "标准 Zigzag": "zigzag_decrypt",
    "反向 Zigzag": "zigzag_decrypt_reverse",
    "外螺旋": "outer_spiral_decrypt",
    "内螺旋": "inner_spiral_decrypt",
    "对角线": "diagonal_decrypt",
    "多级 Zigzag": "multi_zigzag_decrypt",
    "分块 Zigzag": "block_zigzag_decrypt",
    "蛇形": "snake_decrypt",
    "XOR-Zigzag": "xor_zigzag_decrypt",
    "行列 Zigzag": "row_column_zigzag_decrypt"
}


class ZigzagGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("ZigZag 图片加密工具")
        try:
            img = ImageTk.PhotoImage(Image.open('ZigZag Cipher.png'))
            self.root.iconphoto(True, img)
        except Exception as e:
            print("未找到图标文件，使用默认图标")
        self.root.geometry("1380x950")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)
        self.root.overrideredirect(True)  # 隐藏系统标题栏

        self._drag_x = 0
        self._drag_y = 0
        self._maximized = False
        self._normal_geometry = "1380x950"

        self.cipher = ZigzagCipher()
        self.original_image = None
        self.result_image = None

        self._mode = tk.StringVar(value="encrypt")
        self._algo = tk.StringVar(value="标准 Zigzag")
        
        # 参数变量
        self._multi_levels = tk.IntVar(value=3)
        self._block_size = tk.IntVar(value=8)
        self._xor_key = tk.IntVar(value=42)
        
        # 通道选择变量
        self._channel_vars = []
        self._channel_all_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.root.wm_attributes("-topmost", True)

    # ── UI 构建 ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_titlebar()
        self._build_controls()
        Separator(self.root).pack(fill=tk.X, padx=20, pady=0)
        self._build_params()  # 参数面板
        self._build_channel_panel()  # 新增通道选择面板
        self._build_workspace()
        self._build_log()
        
        # 初始隐藏所有参数
        self._update_params_visibility()

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(fill=tk.X, padx=24, pady=(18, 10))

        tk.Label(
            bar,
            text="⬡",
            font=("Segoe UI", 24),
            fg=COLORS["accent"],
            bg=COLORS["bg"]
        ).pack(side=tk.LEFT)
        tk.Label(
            bar,
            text=" ZigZag Cipher",
            font=FONTS["title"],
            fg=COLORS["text"],
            bg=COLORS["bg"]
        ).pack(side=tk.LEFT)
        tk.Label(
            bar,
            text="v1.0",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg"]
        ).pack(side=tk.LEFT, padx=(6, 0), pady=8)
        
        # 版权信息
        tk.Label(
            bar,
            text="Copyright by Cr9flm1nd",
            font=FONTS["small"],
            fg=COLORS["accent"],
            bg=COLORS["bg"]
        ).pack(side=tk.LEFT, padx=(20, 0), pady=8)

        # 右侧窗口控制按钮
        tk.Button(
            bar,
            text="✕",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            bd=0,
            font=("Segoe UI", 13),
            cursor="hand2",
            activebackground=COLORS["danger"],
            activeforeground="white",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=2)

        self._max_btn = tk.Button(
            bar,
            text="⬜",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            bd=0,
            font=("Segoe UI", 13),
            cursor="hand2",
            activebackground=COLORS["surface2"],
            activeforeground=COLORS["text"],
            command=self._toggle_maximize
        )
        self._max_btn.pack(side=tk.RIGHT, padx=2)

        tk.Button(
            bar,
            text="─",
            bg=COLORS["bg"],
            fg=COLORS["text_muted"],
            bd=0,
            font=("Segoe UI", 13),
            cursor="hand2",
            activebackground=COLORS["surface2"],
            activeforeground=COLORS["text"],
            command=self._minimize
        ).pack(side=tk.RIGHT, padx=2)

        # 拖动窗口
        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_move)

    def _build_controls(self):
        ctrl = tk.Frame(self.root, bg=COLORS["bg"])
        ctrl.pack(fill=tk.X, padx=24, pady=(0, 14))

        # ─ 模式切换 ─
        mode_frame = tk.Frame(ctrl, bg=COLORS["surface"], bd=0)
        mode_frame.pack(side=tk.LEFT)

        self._mode_btns = {}
        for mode, label, icon in [("encrypt", "加密", "🔒"),
                                  ("decrypt", "解密", "🔓")]:
            b = tk.Label(
                mode_frame,
                text=f"{icon} {label}",
                font=FONTS["body"],
                cursor="hand2",
                padx=18,
                pady=8
            )
            b.pack(side=tk.LEFT)
            b.bind("<Button-1>", lambda e, m=mode: self._set_mode(m))
            self._mode_btns[mode] = b
        self._update_mode_ui()

        # ─ 算法选择 ─
        tk.Label(
            ctrl,
            text="算法：",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg"]
        ).pack(side=tk.LEFT, padx=(20, 4))

        algo_frame = tk.Frame(
            ctrl,
            bg=COLORS["surface2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        algo_frame.pack(side=tk.LEFT)

        self._algo_menu = tk.OptionMenu(
            algo_frame,
            self._algo,
            *ALGORITHMS,
            command=self._on_algo_change
        )
        self._algo_menu.config(
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["text"],
            bd=0,
            highlightthickness=0,
            font=FONTS["body"],
            relief=tk.FLAT,
            indicatoron=True
        )
        self._algo_menu["menu"].config(
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            activebackground=COLORS["accent"],
            activeforeground="white",
            bd=0,
            font=FONTS["body"]
        )
        self._algo_menu.pack()

        # ─ 操作按钮 ─
        btn_frame = tk.Frame(ctrl, bg=COLORS["bg"])
        btn_frame.pack(side=tk.LEFT, padx=(20, 0))

        DarkButton(
            btn_frame,
            "📂 打开图片",
            command=self.open_image,
            width=120,
            height=34
        ).pack(side=tk.LEFT, padx=4)
        DarkButton(
            btn_frame,
            "▶ 执行",
            command=self.execute,
            accent=True,
            width=100,
            height=34
        ).pack(side=tk.LEFT, padx=4)
        DarkButton(
            btn_frame,
            "💾 保存结果",
            command=self.save_result,
            width=120,
            height=34
        ).pack(side=tk.LEFT, padx=4)

    def _build_params(self):
        """参数设置面板"""
        self.params_frame = tk.Frame(self.root, bg=COLORS["surface"], height=50)
        self.params_frame.pack(fill=tk.X, padx=24, pady=(0, 16))
        self.params_frame.pack_propagate(False)
        
        # 多级Zigzag参数
        self.multi_frame = tk.Frame(self.params_frame, bg=COLORS["surface"])
        self.multi_frame.pack(side=tk.LEFT, padx=(20, 30))
        
        tk.Label(
            self.multi_frame,
            text="多级次数(1~20):",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT)
        
        tk.Spinbox(
            self.multi_frame,
            from_=1,
            to=20,
            textvariable=self._multi_levels,
            width=5,
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            bd=0,
            font=FONTS["body"],
            buttonbackground=COLORS["surface2"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # 分块大小参数
        self.block_frame = tk.Frame(self.params_frame, bg=COLORS["surface"])
        self.block_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(
            self.block_frame,
            text="块大小(2~64):",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT)
        
        tk.Spinbox(
            self.block_frame,
            from_=2,
            to=64,
            textvariable=self._block_size,
            width=5,
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            bd=0,
            font=FONTS["body"],
            buttonbackground=COLORS["surface2"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # XOR密钥参数
        self.xor_frame = tk.Frame(self.params_frame, bg=COLORS["surface"])
        self.xor_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(
            self.xor_frame,
            text="XOR密钥(0~255):",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT)
        
        tk.Spinbox(
            self.xor_frame,
            from_=0,
            to=255,
            textvariable=self._xor_key,
            width=5,
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            bd=0,
            font=FONTS["body"],
            buttonbackground=COLORS["surface2"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _build_channel_panel(self):
        """通道选择面板"""
        channel_frame = tk.Frame(self.root, bg=COLORS["surface"], height=50)
        channel_frame.pack(fill=tk.X, padx=24, pady=(0, 16))
        channel_frame.pack_propagate(False)
        
        # 标题
        tk.Label(
            channel_frame,
            text="通道选择:",
            font=FONTS["heading"],
            fg=COLORS["text"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, padx=(20, 15))
        
        # 全选/全不选按钮
        self._channel_all_cb = tk.Checkbutton(
            channel_frame,
            text="全部通道",
            variable=self._channel_all_var,
            command=self._toggle_all_channels,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            selectcolor=COLORS["surface2"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["accent"],
            font=FONTS["body"]
        )
        self._channel_all_cb.pack(side=tk.LEFT, padx=(0, 20))
        
        # 通道复选框容器
        self.channel_check_frame = tk.Frame(channel_frame, bg=COLORS["surface"])
        self.channel_check_frame.pack(side=tk.LEFT)
        
        # 通道标签和颜色
        channel_names = ["R (红)", "G (绿)", "B (蓝)", "A (透明度)"]
        channel_colors = ["#ff6b6b", "#6bff6b", "#6b6bff", "#ffffff"]
        
        for i, (name, color) in enumerate(zip(channel_names, channel_colors)):
            var = tk.BooleanVar(value=True)
            self._channel_vars.append(var)
            
            cb = tk.Checkbutton(
                self.channel_check_frame,
                text=name,
                variable=var,
                command=self._update_channel_all,
                bg=COLORS["surface"],
                fg=color,
                selectcolor=COLORS["surface2"],
                activebackground=COLORS["surface"],
                activeforeground=color,
                font=FONTS["body"]
            )
            cb.pack(side=tk.LEFT, padx=10)
        
        # 状态提示
        tk.Label(
            channel_frame,
            text="(不选任何通道则不处理)",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["surface"]
        ).pack(side=tk.RIGHT, padx=20)

    def _toggle_all_channels(self):
        """全选/全不选通道"""
        value = self._channel_all_var.get()
        for var in self._channel_vars:
            var.set(value)

    def _update_channel_all(self):
        """更新全选状态"""
        all_selected = all(var.get() for var in self._channel_vars)
        self._channel_all_var.set(all_selected)

    def _get_selected_channels(self):
        """获取选中的通道索引"""
        if self.original_image is None:
            return None
            
        # 如果是灰度图，忽略通道选择
        if self.original_image.mode == 'L':
            return None
            
        selected = []
        for i, var in enumerate(self._channel_vars):
            if var.get():
                selected.append(i)
        
        # 直接返回selected，可能是空列表
        return selected

    def _update_params_visibility(self):
        """根据选择的算法更新参数控件的可见性"""
        algo = self._algo.get()
        
        # 默认全部隐藏
        self.multi_frame.pack_forget()
        self.block_frame.pack_forget()
        self.xor_frame.pack_forget()
        
        # 根据算法显示对应的参数
        if algo == "多级 Zigzag":
            self.multi_frame.pack(side=tk.LEFT, padx=(20, 30))
        elif algo == "分块 Zigzag":
            self.block_frame.pack(side=tk.LEFT, padx=(0, 30))
        elif algo == "XOR-Zigzag":
            self.xor_frame.pack(side=tk.LEFT, padx=(0, 30))

    def _build_workspace(self):
        ws = tk.Frame(self.root, bg=COLORS["bg"])
        ws.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        ws.columnconfigure(0, weight=1)
        ws.columnconfigure(1, weight=0)
        ws.columnconfigure(2, weight=1)
        ws.rowconfigure(0, weight=1)

        self._card_in = ImageCard(
            ws,
            "输入图片",
            "原图",
            COLORS["text_dim"]
        )
        self._card_in.grid(row=0, column=0, sticky="nsew")

        # 中间箭头
        mid = tk.Frame(ws, bg=COLORS["bg"], width=60)
        mid.grid(row=0, column=1, sticky="ns")
        mid.pack_propagate(False)
        self._arrow_label = tk.Label(
            mid,
            text="→",
            font=("Segoe UI", 28),
            fg=COLORS["accent"],
            bg=COLORS["bg"]
        )
        self._arrow_label.place(relx=0.5, rely=0.5, anchor="center")

        self._card_out = ImageCard(
            ws,
            "输出结果",
            "待处理",
            COLORS["text_muted"]
        )
        self._card_out.grid(row=0, column=2, sticky="nsew")

        # 修改：第一个图片展示区显示"点击添加图片"
        self._card_in.img_frame.bind("<Button-1>", lambda e: self.open_image())
        self._card_in.img_label.bind("<Button-1>", lambda e: self.open_image())
        self._card_in.img_label.config(text="点击添加图片")  # 修改这里

        # 修改：第二个图片展示区显示"结果在这里"
        self._card_out.img_label.config(text="结果在这里")  # 修改这里

    def _build_log(self):
        log_outer = tk.Frame(
            self.root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        log_outer.pack(fill=tk.X, padx=24, pady=(0, 16))

        hdr = tk.Frame(log_outer, bg=COLORS["surface"])
        hdr.pack(fill=tk.X, padx=12, pady=(8, 4))

        tk.Label(
            hdr,
            text="操作日志",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT)

        tk.Button(
            hdr,
            text="清空",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["surface"],
            bd=0,
            cursor="hand2",
            activebackground=COLORS["surface"],
            activeforeground=COLORS["accent"],
            command=lambda: self._log.delete("1.0", tk.END)
        ).pack(side=tk.RIGHT)

        self._log = tk.Text(
            log_outer,
            height=4,
            bg=COLORS["panel_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["mono"],
            bd=0,
            relief=tk.FLAT,
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent_dim"]
        )
        self._log.pack(fill=tk.X, padx=12, pady=(0, 10))

        # 状态栏
        self._status = tk.Label(
            self.root,
            text="就绪",
            font=FONTS["small"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg"],
            anchor="w"
        )
        self._status.pack(fill=tk.X, padx=26, pady=(0, 10))

    # ── 模式切换 ─────────────────────────────────────────────────────────────

    def _set_mode(self, mode):
        self._mode.set(mode)
        self._update_mode_ui()
        label = "加密" if mode == "encrypt" else "解密"
        self._log_msg(f"切换到{label}模式")
        self.result_image = None
        self._clear_output()

    def _update_mode_ui(self):
        mode = self._mode.get()
        for m, b in self._mode_btns.items():
            if m == mode:
                b.config(bg=COLORS["accent"], fg="white")
            else:
                b.config(bg=COLORS["surface"], fg=COLORS["text_dim"])

        if not hasattr(self, "_card_out"):
            return

        if mode == "encrypt":
            self._card_out.badge_label.config(text="待加密",
                                              fg=COLORS["warning"])
        else:
            self._card_out.badge_label.config(text="待解密",
                                              fg=COLORS["accent"])

    def _on_algo_change(self, val):
        self._log_msg(f"已选择算法：{val}")
        self._update_params_visibility()  # 算法改变时更新参数显示

    # ── 图片操作 ─────────────────────────────────────────────────────────────

    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                       ("所有文件", "*.*")]
        )
        if not path:
            return

        try:
            self.original_image = Image.open(path)
            self._show_image(self.original_image, self._card_in)
            name = os.path.basename(path)
            w, h = self.original_image.size
            
            # 更新通道选择状态
            mode = self.original_image.mode
            channel_count = len(mode)
            
            # 根据图片模式启用/禁用通道复选框
            for i, var in enumerate(self._channel_vars):
                if i < channel_count:
                    # 启用并设置为默认选中
                    var.set(True)
                else:
                    # 禁用并取消选中
                    var.set(False)
            
            self._card_in.info_label.config(
                text=f"{name} · {w}×{h} · {mode} ({channel_count}通道)",
                fg=COLORS["text_dim"]
            )
            self._log_msg(f"已打开：{name} ({w}×{h} · {mode})")
            self._status.config(text=f"已加载 {name}")
            self.result_image = None
            self._clear_output()
            
            # 更新全选状态
            self._update_channel_all()
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")

    def _minimize(self):
        """用 withdraw 隐藏窗口，在任务栏注册一个临时顶层作为还原入口"""
        self.root.withdraw()
        # 创建一个普通窗口作为任务栏占位，点击即可还原
        self._taskbar_win = tk.Toplevel()
        self._taskbar_win.title("ZigZag Cipher （点击还原）")
        self._taskbar_win.geometry("1x1+0+0")
        self._taskbar_win.iconify()
        self._taskbar_win.protocol("WM_DELETE_WINDOW", self._on_restore)
        self._taskbar_win.bind("<Map>", lambda e: self._on_restore())

    def _on_restore(self):
        if hasattr(self, "_taskbar_win"):
            try:
                self._taskbar_win.destroy()
            except Exception:
                pass
            del self._taskbar_win
        self.root.deiconify()

    def _toggle_maximize(self):
        if self._maximized:
            self.root.geometry(self._normal_geometry)
            self._maximized = False
            self._max_btn.config(text="⬜")
        else:
            self._normal_geometry = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._maximized = True
            self._max_btn.config(text="❐")

    def _drag_start(self, event):
        if self._maximized:
            # 记录鼠标在全屏宽度中的比例，还原后按比例折算为新窗口内偏移
            ratio = event.x_root / self.root.winfo_screenwidth()
            self._toggle_maximize()
            self.root.update_idletasks()
            restored_w = self.root.winfo_width()
            self._drag_x = int(restored_w * ratio)
            self._drag_y = event.y - 10  # 在标题栏内的 y 偏移固定居中即可
            # 立即把窗口移到鼠标下方正确位置
            self.root.geometry(
                f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}"
            )
        else:
            self._drag_x = event.x_root - self.root.winfo_x()
            self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        self.root.geometry(
            f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}"
        )

    def execute(self):
        if self.original_image is None:
            messagebox.showwarning("提示", "请先打开一张图片")
            return

        mode = self._mode.get()
        algo = self._algo.get()
        label = "加密" if mode == "encrypt" else "解密"

        # 参数验证
        if algo == "多级 Zigzag":
            levels = self._multi_levels.get()
            if levels > 20:
                result = messagebox.askyesno(
                    "警告", 
                    f"多级次数设置为 {levels} 次，次数过多可能导致处理时间较长且图像失真严重。\n\n是否继续？",
                    icon="warning"
                )
                if not result:
                    self._log_msg(f"✗ 多级Zigzag操作已取消 (次数={levels})")
                    return
            elif levels < 1:
                messagebox.showerror("错误", "多级次数不能小于1")
                return
                
        elif algo == "XOR-Zigzag":
            key = self._xor_key.get()
            if key < 0 or key > 255:
                messagebox.showerror("错误", "XOR密钥必须在0-255之间")
                return
                
        elif algo == "分块 Zigzag":
            block_size = self._block_size.get()
            if block_size < 2 or block_size > 64:
                messagebox.showerror("错误", "块大小必须在2-64之间")
                return

        self._status.config(text=f"正在{label}（{algo}）…")
        self.root.update_idletasks()

        try:
            arr = np.array(self.original_image)
            
            # 获取选中的通道
            channels = self._get_selected_channels()
            
            # 记录通道信息
            if channels is not None:
                if not channels:  # 空列表表示没有选中任何通道
                    self._log_msg("⚠ 未选中任何通道，将保持原图不变")
                    # 直接返回原图
                    self.result_image = self.original_image.copy()
                    self._show_image(self.result_image, self._card_out)
                    
                    w, h = self.result_image.size
                    badge_text = "未处理 ⚠"
                    self._card_out.badge_label.config(text=badge_text,
                                                      fg=COLORS["warning"])
                    self._card_out.info_label.config(
                        text=f"{w}×{h} · {self.result_image.mode}",
                        fg=COLORS["warning"]
                    )
                    
                    self._log_msg(f"{label}未执行：未选中任何通道")
                    self._status.config(text="未选中任何通道")
                    return
                else:
                    channel_names = ["R", "G", "B", "A"]
                    selected_names = [channel_names[i] for i in channels]
                    self._log_msg(f"选中通道: {', '.join(selected_names)}")

            if mode == "encrypt":
                fn = getattr(self.cipher, ALGO_ENCRYPT[algo])
                # 根据算法类型传递不同的参数
                if algo == "多级 Zigzag":
                    levels = self._multi_levels.get()
                    result_arr = fn(arr, levels=levels, channels=channels)
                    self._log_msg(f"使用参数：多级次数={levels}")
                elif algo == "分块 Zigzag":
                    block_size = self._block_size.get()
                    result_arr = fn(arr, block_size=block_size, channels=channels)
                    self._log_msg(f"使用参数：块大小={block_size}")
                elif algo == "XOR-Zigzag":
                    key = self._xor_key.get()
                    result_arr = fn(arr, key=key, channels=channels)
                    self._log_msg(f"使用参数：XOR密钥={key}")
                else:
                    result_arr = fn(arr, channels=channels)
            else:
                fn = getattr(self.cipher, ALGO_DECRYPT[algo])
                # 根据算法类型传递不同的参数
                if algo == "多级 Zigzag":
                    levels = self._multi_levels.get()
                    result_arr = fn(arr, levels=levels, channels=channels)
                    self._log_msg(f"使用参数：多级次数={levels}")
                elif algo == "分块 Zigzag":
                    block_size = self._block_size.get()
                    result_arr = fn(arr, block_size=block_size, channels=channels)
                    self._log_msg(f"使用参数：块大小={block_size}")
                elif algo == "XOR-Zigzag":
                    key = self._xor_key.get()
                    result_arr = fn(arr, key=key, channels=channels)
                    self._log_msg(f"使用参数：XOR密钥={key}")
                else:
                    result_arr = fn(arr, channels=channels)

            self.result_image = Image.fromarray(result_arr.astype("uint8"))
            self._show_image(self.result_image, self._card_out)

            w, h = self.result_image.size
            badge_text = "已加密 🔒" if mode == "encrypt" else "已解密 🔓"
            self._card_out.badge_label.config(text=badge_text,
                                              fg=COLORS["success"])
            self._card_out.info_label.config(
                text=f"{w}×{h} · {self.result_image.mode}",
                fg=COLORS["success"]
            )

            self._log_msg(f"{label}完成 算法={algo} 尺寸={w}×{h}")
            self._status.config(text=f"{label}完成")

        except Exception as e:
            messagebox.showerror("错误", f"{label}失败：{e}")
            self._status.config(text=f"{label}失败")
            self._log_msg(f"✗ {label}失败：{e}")

    def save_result(self):
        if self.result_image is None:
            messagebox.showwarning("提示", "没有可保存的结果")
            return

        mode = self._mode.get()
        default = "encrypted_image.png" if mode == "encrypt" else "decrypted_image.png"

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                       ("BMP", "*.bmp"), ("所有文件", "*.*")]
        )
        if path:
            try:
                self.result_image.save(path)
                self._log_msg(f"已保存：{os.path.basename(path)}")
                self._status.config(text="保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

    # ── 显示辅助 ─────────────────────────────────────────────────────────────

    def _show_image(self, img, card):
        frame = card.img_frame
        fw = frame.winfo_width() or 380
        fh = frame.winfo_height() or 280

        thumb = img.copy()
        thumb.thumbnail((fw - 8, fh - 8), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(thumb)

        card.img_label.config(image=photo, text="")
        card.img_label.image = photo

    def _clear_output(self):
        self._card_out.img_label.config(
            image="",
            text="结果在这里",  # 修改这里
            fg=COLORS["text_muted"]
        )
        self._card_out.img_label.image = None
        self._card_out.info_label.config(text="— 暂无结果 —",
                                        fg=COLORS["text_muted"])

        mode = self._mode.get()
        self._card_out.badge_label.config(
            text="待加密" if mode == "encrypt" else "待解密",
            fg=COLORS["warning"] if mode == "encrypt" else COLORS["accent"]
        )

    def _log_msg(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.insert(tk.END, f"[{ts}] {msg}\n")
        self._log.see(tk.END)


# ──────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = ZigzagGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()