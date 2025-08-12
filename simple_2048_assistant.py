import tkinter as tk
from tkinter import ttk, messagebox
import time
import random

class Game2048Assistant:
    def __init__(self, root):
        self.root = root
        self.root.title("寻道大千合成辅助工具 @仙●嬴政")
        self.root.geometry("500x600")
        
        # 游戏状态
        self.game_board = [[0 for _ in range(4)] for _ in range(4)]
        
        # AI相关
        self.directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        self.setup_ui()
        
    def setup_ui(self):
        
        # 控制按钮
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.ai_btn = tk.Button(control_frame, text="AI建议", command=self.get_ai_suggestion, state=tk.NORMAL)
        self.ai_btn.pack(side=tk.LEFT, padx=5)
        
        # 游戏状态显示
        status_frame = tk.LabelFrame(self.root, text="游戏状态", padx=10, pady=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建4x4网格显示
        self.cell_labels = []
        self.cell_entries = []  # 用于编辑的输入框
        grid_frame = tk.Frame(status_frame)
        grid_frame.pack()
        
        for i in range(4):
            row_labels = []
            row_entries = []
            for j in range(4):
                cell = tk.Label(grid_frame, text="0", width=6, height=3, 
                               relief="solid", borderwidth=1, 
                               font=("Arial", 12, "bold"))
                cell.grid(row=i, column=j, padx=2, pady=2)
                
                # 绑定双击事件
                cell.bind("<Double-Button-1>", lambda e, x=i, y=j: self.edit_cell(x, y))
                
                row_labels.append(cell)
                
                # 创建输入框（默认隐藏）
                entry = tk.Entry(grid_frame, width=6, justify='center', font=("Arial", 12, "bold"))
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.bind("<Return>", lambda e, x=i, y=j: self.save_cell(x, y))
                entry.bind("<FocusOut>", lambda e, x=i, y=j: self.save_cell(x, y))
                entry.grid_remove()  # 隐藏输入框
                row_entries.append(entry)
                
            self.cell_labels.append(row_labels)
            self.cell_entries.append(row_entries)
        
        # AI建议显示和手动执行按钮
        suggestion_frame = tk.LabelFrame(self.root, text="AI建议与手动控制", padx=10, pady=10)
        suggestion_frame.pack(fill="x", padx=10, pady=5)
        
        # AI建议显示
        self.suggestion_label = tk.Label(suggestion_frame, text="尚未获取AI建议", font=("Arial", 14, "bold"))
        self.suggestion_label.pack()
        
        # 手动控制按钮
        control_frame2 = tk.Frame(suggestion_frame)
        control_frame2.pack(pady=10)
        
        # 上方向按钮
        self.up_btn = tk.Button(control_frame2, text="↑ 上", 
                               command=lambda: self.execute_move('UP'),
                               font=("Arial", 12, "bold"), width=8)
        self.up_btn.pack(side=tk.TOP, pady=5)
        
        # 左右方向按钮
        lr_frame = tk.Frame(control_frame2)
        lr_frame.pack()
        
        self.left_btn = tk.Button(lr_frame, text="← 左", 
                                 command=lambda: self.execute_move('LEFT'),
                                 font=("Arial", 12, "bold"), width=8)
        self.left_btn.pack(side=tk.LEFT, padx=5)
        
        self.right_btn = tk.Button(lr_frame, text="右 →", 
                                  command=lambda: self.execute_move('RIGHT'),
                                  font=("Arial", 12, "bold"), width=8)
        self.right_btn.pack(side=tk.LEFT, padx=5)
        
        # 下方向按钮
        self.down_btn = tk.Button(control_frame2, text="↓ 下", 
                                 command=lambda: self.execute_move('DOWN'),
                                 font=("Arial", 12, "bold"), width=8)
        self.down_btn.pack(side=tk.TOP, pady=5)
        
        # 初始化显示
        self.display_game_board()
        
    def edit_cell(self, i, j):
        """编辑单元格"""
        # 隐藏标签，显示输入框
        self.cell_labels[i][j].grid_remove()
        self.cell_entries[i][j].grid()
        self.cell_entries[i][j].delete(0, tk.END)
        self.cell_entries[i][j].insert(0, str(self.game_board[i][j]))
        self.cell_entries[i][j].select_range(0, tk.END)  # 自动全选
        self.cell_entries[i][j].focus()
        
    def save_cell(self, i, j):
        """保存单元格"""
        try:
            value = self.cell_entries[i][j].get().strip()
            self.game_board[i][j] = int(value) if value.isdigit() else 0
        except:
            self.game_board[i][j] = 0
            
        # 隐藏输入框，显示标签
        self.cell_entries[i][j].grid_remove()
        self.cell_labels[i][j].grid()
        self.display_game_board()
        
        # 自动执行AI建议
        self.root.after(100, self.get_ai_suggestion)
        
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
        """模拟移动，但不生成新数字"""
        # 创建副本，确保不修改原始棋盘
        new_board = [[self.game_board[i][j] for j in range(4)] for i in range(4)]
        
        # 移动逻辑，但不生成新数字
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
            
    def execute_move(self, direction):
        """执行移动操作"""
        # 更新游戏板
        new_board = self.move_board(direction)
        # 修复引用问题，确保正确复制数组
        self.game_board = [row[:] for row in new_board]
        
        # 更新显示
        self.display_game_board()
        
        # 更新建议标签
        direction_text = {
            'UP': '上',
            'DOWN': '下',
            'LEFT': '左',
            'RIGHT': '右'
        }
        
        self.suggestion_label.config(text=f"已执行: {direction_text[direction]} ({direction})，请手动添加新数字")

# 尝试导入所需库
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import time
    import random
except ImportError as e:
    print(f"缺少必要的库: {e}")
    exit(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = Game2048Assistant(root)
    root.mainloop()