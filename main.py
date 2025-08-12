from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.text import LabelBase
import copy
import os

# 尝试注册中文字体
font_files = [
    'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
    'C:/Windows/Fonts/simsun.ttc',  # 宋体
    'C:/Windows/Fonts/simhei.ttf',  # 黑体
]

chinese_font_registered = False
for font_file in font_files:
    if os.path.exists(font_file):
        LabelBase.register(name='Chinese', fn_regular=font_file)
        chinese_font_registered = True
        break

class GameCell(Widget):
    def __init__(self, row, col, **kwargs):
        super(GameCell, self).__init__(**kwargs)
        self.row = row
        self.col = col
        self.value = 0
        
        # 创建标签但不立即添加到widget中
        self.label = Label(text='', font_size=dp(24), bold=True, halign='center', valign='middle')
        if chinese_font_registered:
            self.label.font_name = 'Chinese'
        self.label.bind(size=self.label.setter('text_size'))  # 确保文字居中
        
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        # 初始化时调用一次更新
        self.update_graphics()
        
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 根据数值设置背景色
            color = self.get_color_by_value(self.value)
            Color(*color)
            Rectangle(pos=self.pos, size=self.size)
            
        # 确保标签在最上层并正确设置
        if self.label not in self.children:
            self.add_widget(self.label)
            
        # 更新标签位置和大小
        self.label.size = self.size
        self.label.pos = self.pos
        self.label.text = str(self.value) if self.value != 0 else ""
        self.label.color = (0, 0, 0, 1) if self.value < 8 else (1, 1, 1, 1)
        
        # 根据数值大小调整字体大小
        if self.value < 100:
            self.label.font_size = dp(24)
        elif self.value < 1000:
            self.label.font_size = dp(20)
        else:
            self.label.font_size = dp(16)
        
    def get_color_by_value(self, value):
        """根据数值获取颜色"""
        colors = {
            0: (0.804, 0.757, 0.706, 1),      # #CDC1B4
            2: (0.933, 0.894, 0.855, 1),      # #EEE4DA
            4: (0.929, 0.878, 0.784, 1),      # #EDE0C8
            8: (0.949, 0.694, 0.475, 1),      # #F2B179
            16: (0.961, 0.584, 0.388, 1),     # #F59563
            32: (0.965, 0.486, 0.235, 1),     # #F67C5F
            64: (0.965, 0.369, 0.231, 1),     # #F65E3B
            128: (0.929, 0.812, 0.447, 1),    # #EDCF72
            256: (0.925, 0.800, 0.380, 1),    # #EDCC61
            512: (0.925, 0.784, 0.314, 1),    # #EDC850
            1024: (0.925, 0.773, 0.247, 1),   # #EDC53F
            2048: (0.925, 0.761, 0.180, 1)    # #EDC22E
        }
        color = colors.get(value, (0.235, 0.227, 0.196, 1))  # #3C3A32
        return color

class Android2048Assistant(App):
    def __init__(self, **kwargs):
        super(Android2048Assistant, self).__init__(**kwargs)
        # 初始化游戏状态
        self.game_board = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        
        # AI相关
        self.directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
    def build(self):
        self.title = '寻道大千AI合成'
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        
        # 控制按钮
        control_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.ai_btn = Button(text='AI建议', font_size=dp(18))
        if chinese_font_registered:
            self.ai_btn.font_name = 'Chinese'
        self.ai_btn.bind(on_press=self.get_ai_suggestion)
        control_layout.add_widget(self.ai_btn)
        main_layout.add_widget(control_layout)
        
        # 游戏状态显示
        game_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        game_title = Label(text='游戏状态', font_size=dp(20), bold=True, size_hint_y=None, height=dp(30))
        if chinese_font_registered:
            game_title.font_name = 'Chinese'
        game_layout.add_widget(game_title)
        
        # 创建4x4网格显示
        self.grid_layout = GridLayout(cols=4, rows=4, spacing=dp(5))
        self.cells = []
        
        for i in range(4):
            row_cells = []
            for j in range(4):
                cell = GameCell(i, j, size_hint=(1, 1))
                # 修复双击单元格编辑功能
                cell.bind(on_touch_down=self.create_cell_handler(i, j))
                self.grid_layout.add_widget(cell)
                row_cells.append(cell)
            self.cells.append(row_cells)
            
        game_layout.add_widget(self.grid_layout)
        main_layout.add_widget(game_layout)
        
        # AI建议显示
        suggestion_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(120))
        suggestion_title = Label(text='AI建议与手动控制', font_size=dp(20), bold=True, size_hint_y=None, height=dp(30))
        if chinese_font_registered:
            suggestion_title.font_name = 'Chinese'
        suggestion_layout.add_widget(suggestion_title)
        
        self.suggestion_label = Label(text='尚未获取AI建议', font_size=dp(18), bold=True)
        if chinese_font_registered:
            self.suggestion_label.font_name = 'Chinese'
        suggestion_layout.add_widget(self.suggestion_label)
        
        # 方向控制按钮 - 重新设计布局
        # 创建一个3x3的网格布局，方向按钮放在对应位置
        direction_grid = GridLayout(cols=3, rows=3, size_hint_y=None, height=dp(90), spacing=dp(5))
        
        # 第一行
        direction_grid.add_widget(Widget())  # 空白
        self.up_btn = Button(text='↑ 上', font_size=dp(18), bold=True)
        if chinese_font_registered:
            self.up_btn.font_name = 'Chinese'
        self.up_btn.bind(on_press=lambda x: self.execute_move('UP'))
        direction_grid.add_widget(self.up_btn)
        direction_grid.add_widget(Widget())  # 空白
        
        # 第二行
        self.left_btn = Button(text='← 左', font_size=dp(18), bold=True)
        if chinese_font_registered:
            self.left_btn.font_name = 'Chinese'
        self.left_btn.bind(on_press=lambda x: self.execute_move('LEFT'))
        direction_grid.add_widget(self.left_btn)
        
        # 中间的提示文字
        center_label = Label(text='方向\n控制', font_size=dp(14), halign='center')
        if chinese_font_registered:
            center_label.font_name = 'Chinese'
        direction_grid.add_widget(center_label)
        
        self.right_btn = Button(text='→ 右', font_size=dp(18), bold=True)
        if chinese_font_registered:
            self.right_btn.font_name = 'Chinese'
        self.right_btn.bind(on_press=lambda x: self.execute_move('RIGHT'))
        direction_grid.add_widget(self.right_btn)
        
        # 第三行
        direction_grid.add_widget(Widget())  # 空白
        self.down_btn = Button(text='↓ 下', font_size=dp(18), bold=True)
        if chinese_font_registered:
            self.down_btn.font_name = 'Chinese'
        self.down_btn.bind(on_press=lambda x: self.execute_move('DOWN'))
        direction_grid.add_widget(self.down_btn)
        direction_grid.add_widget(Widget())  # 空白
        
        suggestion_layout.add_widget(direction_grid)
        main_layout.add_widget(suggestion_layout)
        
        # 初始化显示
        self.display_game_board()
        
        return main_layout
        
    def create_cell_handler(self, row, col):
        """为单元格创建触摸处理函数"""
        def handler(instance, touch):
            if instance.collide_point(*touch.pos) and touch.is_double_tap:
                self.edit_cell(row, col)
                return True
            return False
        return handler
        
    def edit_cell(self, row, col):
        """编辑单元格"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        title = Label(text=f'编辑单元格({row+1},{col+1})', font_size=dp(20), bold=True, size_hint_y=None, height=dp(40))
        if chinese_font_registered:
            title.font_name = 'Chinese'
        content.add_widget(title)
        
        text_input = TextInput(text=str(self.game_board[row][col]), 
                              font_size=dp(20), 
                              multiline=False,
                              size_hint_y=None,
                              height=dp(50))
        if chinese_font_registered:
            text_input.font_name = 'Chinese'
        content.add_widget(text_input)
        
        buttons = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        cancel_btn = Button(text='取消', font_size=dp(18))
        save_btn = Button(text='保存', font_size=dp(18))
        if chinese_font_registered:
            cancel_btn.font_name = 'Chinese'
            save_btn.font_name = 'Chinese'
        buttons.add_widget(cancel_btn)
        buttons.add_widget(save_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(title='编辑单元格',
                     content=content,
                     size_hint=(0.8, 0.6))
        if chinese_font_registered:
            popup.title_font = 'Chinese'
        
        def save_value(instance):
            try:
                value = text_input.text.strip()
                self.game_board[row][col] = int(value) if value.isdigit() else 0
                self.display_game_board()  # 确保更新界面显示
                popup.dismiss()
                # 自动执行AI建议
                self.get_ai_suggestion(None)
            except Exception as e:
                print(f"保存值时出错: {e}")  # 调试信息
                pass
                
        def cancel_edit(instance):
            popup.dismiss()
            
        save_btn.bind(on_press=save_value)
        cancel_btn.bind(on_press=cancel_edit)
        
        # 添加回车键保存功能
        def on_enter(instance):
            save_value(None)
            
        text_input.bind(on_text_validate=on_enter)
        
        # 添加失去焦点时自动保存功能
        def on_focus(instance, value):
            if not value:  # 失去焦点时
                save_value(None)
                
        text_input.bind(focus=on_focus)
        
        popup.open()
        
        # 自动选中所有文本以便编辑
        text_input.select_all()
        
    def display_game_board(self):
        """显示游戏板"""
        for i in range(4):
            for j in range(4):
                self.cells[i][j].value = self.game_board[i][j]
                self.cells[i][j].update_graphics()
                
    def get_ai_suggestion(self, instance):
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
                self.suggestion_label.text = "游戏结束"
                return
                
        direction_text = {
            'UP': '上',
            'DOWN': '下',
            'LEFT': '左',
            'RIGHT': '右'
        }
        self.suggestion_label.text = f"建议方向: {direction_text[best_move]} ({best_move})"
        
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
            
            # 对每个空位置尝试放置2(90%概率)和4(10%概率)
            for i, j in empty_cells:
                for value, prob in [(2, 0.9), (4, 0.1)]:
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
        # 计算新状态
        new_board = self.move_board_direction(self.game_board, direction)
        
        # 只有在移动有效时才更新状态
        if new_board != self.game_board:
            # 使用列表推导式创建完全独立的副本
            self.game_board = [[new_board[i][j] for j in range(4)] for i in range(4)]
            self.display_game_board()
            
            # 更新建议标签
            direction_text = {
                'UP': '上',
                'DOWN': '下',
                'LEFT': '左',
                'RIGHT': '右'
            }
            self.suggestion_label.text = f"已执行: {direction_text[direction]} ({direction})，请手动添加新数字"

if __name__ == '__main__':
    Android2048Assistant().run()