import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageGrab
import time
import threading
from collections import deque
import random

class Game2048Assistant:
    def __init__(self, root):
        self.root = root
        self.root.title("寻道大千合成辅助工具 @仙●嬴政")
        self.root.geometry("600x700")
        
        # 游戏区域坐标
        self.top_left = None
        self.bottom_right = None
        self.game_region = None
        
        # 游戏状态
        self.game_board = [[0 for _ in range(4)] for _ in range(4)]
        self.is_running = False
        self.is_auto_mode = False
        
        # AI相关
        self.directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        self.setup_ui()
        
    def setup_ui(self):

        
        # 操作说明
        instruction_frame = tk.LabelFrame(self.root, text="操作说明", padx=10, pady=10)
        instruction_frame.pack(fill="x", padx=10, pady=5)
        
        instructions = """
        1. 启动2048游戏程序
        2. 点击"选择游戏区域"按钮，在弹出窗口时切换到游戏界面
        3. 按住鼠标左键拖拽选择游戏区域(4x4网格)
        4. 点击"开始识别"获取当前游戏状态
        5. 点击"AI建议"获取下一步操作建议
        6. 可启用"自动模式"让AI自动玩游戏
        """
        instruction_label = tk.Label(instruction_frame, text=instructions, justify=tk.LEFT)
        instruction_label.pack()
        
        # 控制按钮
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.select_area_btn = tk.Button(control_frame, text="选择游戏区域", command=self.select_game_area)
        self.select_area_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = tk.Button(control_frame, text="开始识别", command=self.start_recognition, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.ai_btn = tk.Button(control_frame, text="AI建议", command=self.get_ai_suggestion, state=tk.DISABLED)
        self.ai_btn.pack(side=tk.LEFT, padx=5)
        
        self.auto_btn = tk.Button(control_frame, text="自动模式", command=self.toggle_auto_mode)
        self.auto_btn.pack(side=tk.LEFT, padx=5)
        
        # 坐标显示
        coord_frame = tk.LabelFrame(self.root, text="游戏区域坐标", padx=10, pady=10)
        coord_frame.pack(fill="x", padx=10, pady=5)
        
        self.coord_label = tk.Label(coord_frame, text="尚未选择游戏区域")
        self.coord_label.pack()
        
        # 游戏状态显示
        status_frame = tk.LabelFrame(self.root, text="游戏状态", padx=10, pady=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建4x4网格显示
        self.cell_labels = []
        grid_frame = tk.Frame(status_frame)
        grid_frame.pack()
        
        for i in range(4):
            row = []
            for j in range(4):
                cell = tk.Label(grid_frame, text="0", width=6, height=3, 
                               relief="solid", borderwidth=1, 
                               font=("Arial", 12, "bold"))
                cell.grid(row=i, column=j, padx=2, pady=2)
                row.append(cell)
            self.cell_labels.append(row)
        
        # AI建议显示
        suggestion_frame = tk.LabelFrame(self.root, text="AI建议", padx=10, pady=10)
        suggestion_frame.pack(fill="x", padx=10, pady=5)
        
        self.suggestion_label = tk.Label(suggestion_frame, text="尚未获取AI建议", font=("Arial", 14, "bold"))
        self.suggestion_label.pack()
        
        # 日志显示
        log_frame = tk.LabelFrame(self.root, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8)
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def select_game_area(self):
        """选择游戏区域"""
        # 提示用户切换到游戏窗口
        messagebox.showinfo("提示", "请切换到2048游戏窗口，然后按确定开始选择区域")
        
        # 隐藏主窗口
        self.root.withdraw()
        time.sleep(1)
        
        # 获取屏幕截图
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        
        # 显示选择窗口
        selector = RegionSelector(self.root, screenshot)
        self.root.wait_window(selector.top)
        
        # 恢复主窗口
        self.root.deiconify()
        
        if selector.top_left and selector.bottom_right:
            self.top_left = selector.top_left
            self.bottom_right = selector.bottom_right
            self.game_region = (self.top_left[0], self.top_left[1], 
                               self.bottom_right[0], self.bottom_right[1])
            
            self.coord_label.config(
                text=f"左上角: ({self.top_left[0]}, {self.top_left[1]})  "
                     f"右下角: ({self.bottom_right[0]}, {self.bottom_right[1]})"
            )
            
            self.start_btn.config(state=tk.NORMAL)
            self.log(f"已选择游戏区域: {self.game_region}")
        else:
            self.log("未选择有效区域")
            
    def start_recognition(self):
        """开始识别游戏状态"""
        if not self.game_region:
            messagebox.showerror("错误", "请先选择游戏区域")
            return
            
        try:
            self.recognize_game_board()
            self.display_game_board()
            self.ai_btn.config(state=tk.NORMAL)
            self.log("游戏状态识别完成")
        except Exception as e:
            self.log(f"识别失败: {str(e)}")
            
    def recognize_game_board(self):
        """通过OCR识别游戏板"""
        # 截取游戏区域
        screenshot = ImageGrab.grab(bbox=self.game_region)
        screenshot = screenshot.convert('L')  # 转为灰度图
        screenshot = screenshot.point(lambda x: 0 if x < 128 else 255, '1')  # 二值化
        
        width, height = screenshot.size
        cell_width = width // 4
        cell_height = height // 4
        
        # 识别每个单元格
        for i in range(4):
            for j in range(4):
                # 计算单元格区域
                left = j * cell_width + 10
                top = i * cell_height + 10
                right = (j + 1) * cell_width - 10
                bottom = (i + 1) * cell_height - 10
                
                # 裁剪单元格
                cell_image = screenshot.crop((left, top, right, bottom))
                
                # OCR识别
                text = pytesseract.image_to_string(cell_image, config='--psm 10')
                # 清理识别结果
                text = text.strip().replace('\n', '')
                
                # 转换为数字
                try:
                    value = int(text) if text.isdigit() else 0
                except:
                    value = 0
                    
                self.game_board[i][j] = value
                
    def display_game_board(self):
        """显示游戏板"""
        for i in range(4):
            for j in range(4):
                value = self.game_board[i][j]
                text = str(value) if value != 0 else ""
                self.cell_labels[i][j].config(text=text)
                
                # 根据数值设置背景色
                bg_color = self.get_color_by_value(value)
                self.cell_labels[i][j].config(bg=bg_color, fg="black" if value < 8 else "white")
                
    def get_color_by_value(self, value):
        """根据数值获取颜色"""
        colors = {
            0: "#CDC1B4",
            2: "#EEE4DA",
            4: "#EDE0C8",
            8: "#F2B179",
            16: "#F59563",
            32: "#F67C5F",
            64: "#F65E3B",
            128: "#EDCF72",
            256: "#EDCC61",
            512: "#EDC850",
            1024: "#EDC53F",
            2048: "#EDC22E"
        }
        return colors.get(value, "#3C3A32")
        
    def get_ai_suggestion(self):
        """获取AI建议"""
        best_move = self.get_best_move()
        direction_text = {
            'UP': '上',
            'DOWN': '下',
            'LEFT': '左',
            'RIGHT': '右'
        }
        
        self.suggestion_label.config(text=f"建议方向: {direction_text[best_move]} ({best_move})")
        self.log(f"AI建议: {best_move}")
        
    def get_best_move(self):
        """使用期望最小化算法获取最佳移动方向"""
        best_score = -1
        best_move = None
        
        for direction in self.directions:
            score = self.evaluate_move(direction)
            if score > best_score:
                best_score = score
                best_move = direction
                
        return best_move if best_move else random.choice(self.directions)
        
    def evaluate_move(self, direction):
        """评估移动方向的得分"""
        # 这里使用简单的评估方法
        # 实际应用中可以使用更复杂的评估函数
        moved_board = self.move_board(direction)
        if moved_board == self.game_board:
            return -1  # 不能移动，返回负分
            
        # 计算空格数量
        empty_count = sum(row.count(0) for row in moved_board)
        
        # 计算平滑度 (相邻数字的差值)
        smoothness = self.calculate_smoothness(moved_board)
        
        # 计算单调性
        monotonicity = self.calculate_monotonicity(moved_board)
        
        # 计算最大数的位置权重
        max_tile_weight = self.calculate_max_tile_weight(moved_board)
        
        # 综合评分
        score = empty_count * 100 + smoothness * 2 + monotonicity * 2 + max_tile_weight * 10
        return score
        
    def move_board(self, direction):
        """模拟移动"""
        # 创建副本
        new_board = [row[:] for row in self.game_board]
        
        # 简化的移动逻辑，实际2048逻辑更复杂
        if direction == 'LEFT':
            for i in range(4):
                # 移除0并合并相同数字
                row = [x for x in new_board[i] if x != 0]
                for j in range(len(row)-1):
                    if row[j] == row[j+1]:
                        row[j] *= 2
                        row[j+1] = 0
                row = [x for x in row if x != 0]
                # 补齐0
                row += [0] * (4 - len(row))
                new_board[i] = row
        elif direction == 'RIGHT':
            for i in range(4):
                row = [x for x in new_board[i] if x != 0]
                for j in range(len(row)-1, 0, -1):
                    if row[j] == row[j-1]:
                        row[j] *= 2
                        row[j-1] = 0
                row = [x for x in row if x != 0]
                row = [0] * (4 - len(row)) + row
                new_board[i] = row
        elif direction == 'UP':
            for j in range(4):
                col = [new_board[i][j] for i in range(4) if new_board[i][j] != 0]
                for i in range(len(col)-1):
                    if col[i] == col[i+1]:
                        col[i] *= 2
                        col[i+1] = 0
                col = [x for x in col if x != 0]
                col += [0] * (4 - len(col))
                for i in range(4):
                    new_board[i][j] = col[i]
        elif direction == 'DOWN':
            for j in range(4):
                col = [new_board[i][j] for i in range(4) if new_board[i][j] != 0]
                for i in range(len(col)-1, 0, -1):
                    if col[i] == col[i-1]:
                        col[i] *= 2
                        col[i-1] = 0
                col = [x for x in col if x != 0]
                col = [0] * (4 - len(col)) + col
                for i in range(4):
                    new_board[i][j] = col[i]
                    
        return new_board
        
    def calculate_smoothness(self, board):
        """计算平滑度"""
        smoothness = 0
        for i in range(4):
            for j in range(4):
                if board[i][j] != 0:
                    # 检查右边
                    if j < 3 and board[i][j+1] != 0:
                        smoothness -= abs(board[i][j] - board[i][j+1])
                    # 检查下边
                    if i < 3 and board[i+1][j] != 0:
                        smoothness -= abs(board[i][j] - board[i+1][j])
        return smoothness
        
    def calculate_monotonicity(self, board):
        """计算单调性"""
        # 水平单调性
        hori_monotonicity = 0
        for i in range(4):
            for j in range(3):
                if board[i][j] >= board[i][j+1]:
                    hori_monotonicity += 1
                    
        # 垂直单调性
        vert_monotonicity = 0
        for j in range(4):
            for i in range(3):
                if board[i][j] >= board[i+1][j]:
                    vert_monotonicity += 1
                    
        return hori_monotonicity + vert_monotonicity
        
    def calculate_max_tile_weight(self, board):
        """计算最大数位置权重"""
        max_tile = max(max(row) for row in board)
        for i in range(4):
            for j in range(4):
                if board[i][j] == max_tile:
                    # 鼓励最大数在角落
                    if (i == 0 and j == 0) or (i == 0 and j == 3) or (i == 3 and j == 0) or (i == 3 and j == 3):
                        return 10
                    # 在边缘也比较好
                    elif i == 0 or i == 3 or j == 0 or j == 3:
                        return 5
                    # 在中间不好
                    else:
                        return 0
        return 0
        
    def toggle_auto_mode(self):
        """切换自动模式"""
        self.is_auto_mode = not self.is_auto_mode
        if self.is_auto_mode:
            self.auto_btn.config(text="停止自动")
            self.log("启动自动模式")
            self.auto_play()
        else:
            self.auto_btn.config(text="自动模式")
            self.log("停止自动模式")
            
    def auto_play(self):
        """自动游戏"""
        if not self.is_auto_mode:
            return
            
        try:
            # 识别当前状态
            self.recognize_game_board()
            self.display_game_board()
            
            # 获取最佳移动
            best_move = self.get_best_move()
            
            # 显示建议
            direction_keys = {
                'UP': 'up',
                'DOWN': 'down',
                'LEFT': 'left',
                'RIGHT': 'right'
            }
            
            self.suggestion_label.config(text=f"执行操作: {best_move}")
            self.log(f"自动执行: {best_move}")
            
            # 发送按键（需要游戏窗口处于激活状态）
            pyautogui.press(direction_keys[best_move])
            
            # 等待游戏更新
            time.sleep(0.5)
            
            # 继续自动游戏
            if self.is_auto_mode:
                self.root.after(1000, self.auto_play)
        except Exception as e:
            self.log(f"自动游戏出错: {str(e)}")
            self.is_auto_mode = False
            self.auto_btn.config(text="自动模式")

class RegionSelector:
    def __init__(self, parent, screenshot):
        self.parent = parent
        self.screenshot = screenshot
        self.top_left = None
        self.bottom_right = None
        
        # 创建选择窗口
        self.top = tk.Toplevel(parent)
        self.top.title("选择游戏区域")
        self.top.geometry("800x600")
        
        # 转换图像
        self.photo = ImageTk.PhotoImage(screenshot)
        
        # 创建画布
        self.canvas = tk.Canvas(self.top, width=self.photo.width(), height=self.photo.height())
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.rect = None
        self.start_x = None
        self.start_y = None
        
        # 提示标签
        tip_label = tk.Label(self.top, text="按住鼠标左键拖拽选择游戏区域(4x4网格)")
        tip_label.pack()
        
    def on_mouse_down(self, event):
        # 记录起始点
        self.start_x = event.x
        self.start_y = event.y
        
        # 删除之前的矩形
        if self.rect:
            self.canvas.delete(self.rect)
            
    def on_mouse_drag(self, event):
        # 拖拽时实时绘制矩形
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, 
            outline='red', width=2
        )
        
    def on_mouse_up(self, event):
        # 记录结束点
        end_x = event.x
        end_y = event.y
        
        # 确保坐标正确（左上到右下）
        self.top_left = (min(self.start_x, end_x), min(self.start_y, end_y))
        self.bottom_right = (max(self.start_x, end_x), max(self.start_y, end_y))
        
        # 关闭窗口
        self.top.destroy()

# 尝试导入所需库
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import pyautogui
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image, ImageGrab, ImageTk
    import time
    import threading
    from collections import deque
    import random
except ImportError as e:
    print(f"缺少必要的库: {e}")
    print("请安装所需库:")
    print("pip install pyautogui opencv-python pytesseract pillow numpy")
    exit(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = Game2048Assistant(root)
    root.mainloop()