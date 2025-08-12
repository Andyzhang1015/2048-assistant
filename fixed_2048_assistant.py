import tkinter as tk
import copy

class Fixed2048Assistant:
    def __init__(self, root):
        self.root = root
        self.root.title("寻道大千合成AI工具 梵音海6服@真●嬴政")
        self.root.geometry("500x650")
        
        # 初始化游戏状态
        self.game_board = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        
        
        # AI相关
        self.directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        self.setup_ui()
        
    def setup_ui(self):
        
        # 控制按钮
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.ai_btn = tk.Button(control_frame, text="AI建议", command=self.get_ai_suggestion)
        self.ai_btn.pack(side=tk.LEFT, padx=5)
        
        # 游戏状态显示
        status_frame = tk.LabelFrame(self.root, text="游戏状态", padx=10, pady=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建4x4网格显示
        self.cell_labels = []
        self.cell_entries = []
        grid_frame = tk.Frame(status_frame)
        grid_frame.pack()
        
        for i in range(4):
            row_labels = []
            row_entries = []
            for j in range(4):
                # 显示单元格
                cell = tk.Label(grid_frame, text="0", width=6, height=3, 
                               relief="solid", borderwidth=1, 
                               font=("Arial", 12, "bold"))
                cell.grid(row=i, column=j, padx=2, pady=2)
                # 通过事件对象确定被点击的单元格
                cell.bind("<Double-Button-1>", self.handle_edit)
                # 将坐标信息存储在标签的属性中
                cell.row = i
                cell.col = j
                row_labels.append(cell)
                
                # 编辑单元格（每次重新创建以避免事件绑定问题）
                entry = self.create_entry(grid_frame, i, j)
                entry.grid_remove()
                row_entries.append(entry)
                
            self.cell_labels.append(row_labels)
            self.cell_entries.append(row_entries)
        
        # AI建议显示
        suggestion_frame = tk.LabelFrame(self.root, text="AI建议与手动控制", padx=10, pady=10)
        suggestion_frame.pack(fill="x", padx=10, pady=5)
        
        self.suggestion_label = tk.Label(suggestion_frame, text="尚未获取AI建议", font=("Arial", 14, "bold"))
        self.suggestion_label.pack()
        
        # 方向控制按钮
        control_frame2 = tk.Frame(suggestion_frame)
        control_frame2.pack(pady=10)
        
        self.up_btn = tk.Button(control_frame2, text="↑ 上", 
                               command=lambda: self.execute_move('UP'),
                               font=("Arial", 12, "bold"), width=8)
        self.up_btn.pack(side=tk.TOP, pady=5)
        
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
        
        self.down_btn = tk.Button(control_frame2, text="↓ 下", 
                                 command=lambda: self.execute_move('DOWN'),
                                 font=("Arial", 12, "bold"), width=8)
        self.down_btn.pack(side=tk.TOP, pady=5)
        
        # 调试信息显示
        self.debug_info = tk.Label(self.root, text="", fg="red")
        self.debug_info.pack(pady=5)

        # 初始化显示
        self.display_game_board()
        
    def create_entry(self, parent, i, j):
        """创建输入框"""
        entry = tk.Entry(parent, width=6, justify='center', font=("Arial", 12, "bold"))
        entry.grid(row=i, column=j, padx=2, pady=2)
        # 为每个输入框创建独立的事件处理函数
        entry.bind("<Return>", lambda e, i=i, j=j: self.handle_save(e, i, j))
        entry.bind("<FocusOut>", lambda e, i=i, j=j: self.handle_save(e, i, j))
        # 将坐标信息存储在输入框的属性中
        entry.row = i
        entry.col = j
        return entry
        
    def create_save_handler(self, i, j):
        """为指定坐标创建保存处理函数"""
        def save_handler(event):
            
            self.save_cell(i, j)
        return save_handler
        
    def handle_edit(self, event):
        """处理编辑事件，通过事件对象获取单元格坐标"""
        widget = event.widget
        i, j = widget.row, widget.col
        self.edit_cell(i, j)
        
    def handle_save(self, event, i, j):
        """处理保存事件"""
        self.save_cell(i, j)
        debug_text = f"保存单元格({i},{j}), widget类型: {type(event.widget).__name__}"
        self.debug_info.config(text=debug_text)

    def save_cell(self, i, j):
        """保存单元格"""
        try:
            value = self.cell_entries[i][j].get().strip()
            self.game_board[i][j] = int(value) if value.isdigit() else 0
        except Exception:
            pass  # 保持原值

        # 隐藏输入框，显示标签
        self.cell_entries[i][j].grid_remove()
        self.cell_labels[i][j].grid()
        self.display_game_board()

        # 自动执行AI建议
        self.root.after(100, self.get_ai_suggestion)
        
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
        """获取AI建议 - 使用高级Expectimax算法"""
        best_move = self.expectimax(
            tuple(tuple(row) for row in self.game_board), 3, True
        )[1]
        
        if best_move is None:
            # 如果没有有效移动，检查是否有有效移动
            valid_moves = self.get_valid_moves(self.game_board)
            if valid_moves:
                best_move = valid_moves[0]
            else:
                self.suggestion_label.config(text="游戏结束")
                return
                
        direction_text = {
            'UP': '上',
            'DOWN': '下',
            'LEFT': '左',
            'RIGHT': '右'
        }
        self.suggestion_label.config(text=f"建议方向: {direction_text[best_move]} ({best_move})")
        
    def expectimax(self, board, depth, is_max):
        """Expectimax算法实现"""
        # 转换为列表以便操作
        board_list = [list(row) for row in board]
        
        # 基本情况
        if depth == 0 or not self.get_valid_moves(board_list):
            return self.evaluate_board(board_list), None
            
        if is_max:
            # 最大化玩家（选择移动）
            max_score = -float('inf')
            best_move = None
            
            for direction in self.directions:
                new_board = self.move_board_direction(board_list, direction)
                if new_board != board_list:  # 如果移动有效
                    score, _ = self.expectimax(
                        tuple(tuple(row) for row in new_board), 
                        depth - 1, False
                    )
                    if score > max_score:
                        max_score = score
                        best_move = direction
                        
            return max_score, best_move
        else:
            # 机会节点（随机添加新方块）
            empty_cells = self.get_empty_cells(board_list)
            if not empty_cells:
                return self.evaluate_board(board_list), None
                
            expected_score = 0
            
            # 对每个空位置尝试放置1(90%概率)和2(10%概率)
            for i, j in empty_cells:
                for value, prob in [(1, 0.9), (2, 0.1)]:
                    new_board = [row[:] for row in board_list]
                    new_board[i][j] = value
                    score, _ = self.expectimax(
                        tuple(tuple(row) for row in new_board), 
                        depth - 1, True
                    )
                    expected_score += prob * score
                    
            return expected_score, None
            
    def get_empty_cells(self, board):
        """获取所有空单元格的位置"""
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty_cells.append((i, j))
        return empty_cells
        
    def evaluate_board(self, board):
        """评估棋盘得分 - 使用多种启发式方法"""
        score = 0
        
        # 1. 空格奖励
        empty_count = len(self.get_empty_cells(board))
        score += empty_count * 1000
        
        # 2. 最大值奖励
        max_tile = max(max(row) for row in board)
        score += max_tile * 10
        
        # 3. 单调性评估
        score += self.calculate_monotonicity(board) * 100
        
        # 4. 平滑度评估
        score -= self.calculate_smoothness(board) * 10
        
        # 5. 边角权重（鼓励将大数字放在角落）
        score += self.calculate_corner_weight(board) * 10000
        
        return score
        
    def calculate_monotonicity(self, board):
        """计算单调性"""
        # 水平单调性
        hori_monotonicity = 0
        for i in range(4):
            for j in range(3):
                if board[i][j] >= board[i][j+1]:
                    hori_monotonicity += board[i][j] - board[i][j+1]
                    
        # 垂直单调性
        vert_monotonicity = 0
        for j in range(4):
            for i in range(3):
                if board[i][j] >= board[i+1][j]:
                    vert_monotonicity += board[i][j] - board[i+1][j]
                    
        return hori_monotonicity + vert_monotonicity
        
    def calculate_smoothness(self, board):
        """计算平滑度"""
        smoothness = 0
        for i in range(4):
            for j in range(4):
                if board[i][j] != 0:
                    # 检查右边
                    if j < 3 and board[i][j+1] != 0:
                        smoothness += abs(board[i][j] - board[i][j+1])
                    # 检查下边
                    if i < 3 and board[i+1][j] != 0:
                        smoothness += abs(board[i][j] - board[i+1][j])
        return smoothness
        
    def calculate_corner_weight(self, board):
        """计算角落权重"""
        # 鼓励将最大值放在角落
        max_tile = max(max(row) for row in board)
        corner_score = 0
        
        # 检查四个角落
        corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
        for i, (x, y) in enumerate(corners):
            if board[x][y] == max_tile:
                corner_score += (4 - i) * max_tile  # 给不同角落不同的权重
                
        return corner_score
        
    def get_valid_moves(self, board):
        """获取所有有效的移动方向"""
        valid_moves = []
        for direction in self.directions:
            new_board = self.move_board_direction(board, direction)
            if new_board != board:
                valid_moves.append(direction)
        return valid_moves
        
    def move_board_direction(self, board, direction):
        """根据方向移动棋盘"""
        # 创建新棋盘的完整副本
        new_board = [[board[i][j] for j in range(4)] for i in range(4)]
        
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
        
    def execute_move(self, direction):
        """执行移动操作"""
        # 添加调试信息
        old_board = copy.deepcopy(self.game_board)
        # 计算新状态
        new_board = self.move_board_direction(self.game_board, direction)
        
        # 只有在移动有效时才更新状态
        if new_board != self.game_board:
            # 使用列表推导式创建完全独立的副本
            self.game_board = [[new_board[i][j] for j in range(4)] for i in range(4)]
            self.display_game_board()
            
            # 添加调试信息
            
            
            # 更新建议标签
            direction_text = {
                'UP': '上',
                'DOWN': '下',
                'LEFT': '左',
                'RIGHT': '右'
            }
            self.suggestion_label.config(
                text=f"已执行: {direction_text[direction]} ({direction})，请手动添加新数字"
            )
            
    def display_game_board(self):
        """显示游戏板"""
        # 重新创建所有输入框以避免事件绑定问题
        grid_frame = self.cell_labels[0][0].master  # 获取网格框架
        for i in range(4):
            for j in range(4):
                # 销毁旧的输入框
                self.cell_entries[i][j].destroy()
                # 创建新的输入框
                self.cell_entries[i][j] = self.create_entry(grid_frame, i, j)
                self.cell_entries[i][j].grid_remove()
        
        # 隐藏所有输入框，确保界面状态一致
        for i in range(4):
            for j in range(4):
                self.cell_labels[i][j].grid()
        
        # 添加调试信息
        
        for i in range(4):
            for j in range(4):
                value = self.game_board[i][j]
                text = str(value) if value != 0 else ""
                self.cell_labels[i][j].config(text=text)
                
                # 根据数值设置背景色
                bg_color = self.get_color_by_value(value)
                self.cell_labels[i][j].config(bg=bg_color, fg="black" if value < 8 else "white")
                
    def edit_cell(self, i, j):
        """编辑单元格"""
        #debug_text = f"编辑单元格({i},{j}), 当前值: {self.game_board[i][j]}"
        #self.debug_info.config(text=debug_text)
        
        # 隐藏所有其他输入框，确保只有一个输入框处于活动状态
        for x in range(4):
            for y in range(4):
                if self.cell_entries[x][y].winfo_viewable():
                    self.cell_entries[x][y].grid_remove()
                    self.cell_labels[x][y].grid()
        
        # 隐藏标签，显示输入框
        self.cell_labels[i][j].grid_remove()
        self.cell_entries[i][j].grid()
        self.cell_entries[i][j].delete(0, tk.END)
        # 确保从当前游戏状态获取正确的值
        self.cell_entries[i][j].insert(0, str(self.game_board[i][j]))
        self.cell_entries[i][j].select_range(0, tk.END)
        self.cell_entries[i][j].focus()
        
        # 绑定事件处理函数
        self.cell_entries[i][j].bind("<Return>", self.create_save_handler(i, j))
        self.cell_entries[i][j].bind("<FocusOut>", self.create_save_handler(i, j))
        
if __name__ == "__main__":
    root = tk.Tk()
    app = Fixed2048Assistant(root)
    root.mainloop()