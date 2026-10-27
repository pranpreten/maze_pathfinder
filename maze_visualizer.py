from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from search import generate_maze, solve


class App:
    rows = 21
    cols = 31
    colors = {'wall': '#283548', 'empty': '#ffffff', 'visited': '#b9d8f2', 'path': '#ffd375', 'start': '#46a574', 'end': '#df7076'}

    def __init__(self, root):
        self.root = root
        root.title('미로 길찾기 · BFS / A*')
        root.geometry('1120x820')
        root.minsize(950, 700)
        self.start = (1, 1)
        self.end = (self.rows-2, self.cols-2)
        self.grid = generate_maze(self.rows, self.cols, 42)
        self.algorithm = tk.StringVar(value='A*')
        self.mode = tk.StringVar(value='wall')
        self.speed = tk.DoubleVar(value=12)
        self.seed = tk.StringVar(value='42')
        self.status = tk.StringVar(value='벽을 그리거나 지운 후 탐색을 실행하세요. 상하좌우 이동 비용은 모두 1입니다.')
        self.visited = set()
        self.path = set()
        self.after_id = None
        self.running = False
        self.cells = {}
        header = ttk.Frame(root, padding=14)
        header.pack(fill='x')
        ttk.Label(header, text='미로 길찾기', font=('맑은 고딕', 19, 'bold')).pack(side='left')
        ttk.Button(header, text='불러오기', command=self.load).pack(side='right')
        ttk.Button(header, text='미로 저장', command=self.save).pack(side='right', padx=8)
        toolbar = ttk.Frame(root, padding=(14, 0, 14, 10))
        toolbar.pack(fill='x')
        ttk.Label(toolbar, text='난수 시드').pack(side='left')
        ttk.Entry(toolbar, textvariable=self.seed, width=9).pack(side='left', padx=6)
        ttk.Button(toolbar, text='미로 생성', command=self.generate).pack(side='left')
        ttk.Button(toolbar, text='빈 격자', command=self.empty).pack(side='left', padx=6)
        ttk.Combobox(toolbar, values=('BFS', 'A*'), textvariable=self.algorithm, width=6, state='readonly').pack(side='left', padx=(15, 6))
        ttk.Button(toolbar, text='탐색 실행', command=self.run).pack(side='left')
        ttk.Button(toolbar, text='두 알고리즘 비교', command=self.compare).pack(side='left', padx=6)
        ttk.Button(toolbar, text='중지', command=self.stop).pack(side='left')
        tools = ttk.Frame(root, padding=(14, 0, 14, 10))
        tools.pack(fill='x')
        for text, value in [('벽 그리기', 'wall'), ('벽 지우기', 'erase'), ('출발점', 'start'), ('도착점', 'end')]:
            ttk.Radiobutton(tools, text=text, variable=self.mode, value=value).pack(side='left', padx=(0, 12))
        ttk.Label(tools, text='애니메이션 속도').pack(side='left', padx=(15, 4))
        ttk.Scale(tools, from_=1, to=50, variable=self.speed, length=140).pack(side='left')
        ttk.Button(tools, text='경로 지우기', command=self.clear).pack(side='right')
        self.canvas = tk.Canvas(root, bg='#dce3eb', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=14)
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.canvas.bind('<Button-1>', self.edit)
        self.canvas.bind('<B1-Motion>', self.edit)
        legend = ttk.Frame(root, padding=(14, 8))
        legend.pack(fill='x')
        for title, key in [('출발', 'start'), ('도착', 'end'), ('탐색한 칸', 'visited'), ('최단 경로', 'path')]:
            tk.Label(legend, text='  ', bg=self.colors[key]).pack(side='left', padx=(0, 4))
            ttk.Label(legend, text=title).pack(side='left', padx=(0, 16))
        self.table = ttk.Treeview(root, columns=('algorithm', 'visited', 'steps', 'time'), show='headings', height=2)
        for key, text in [('algorithm', '알고리즘'), ('visited', '탐색한 칸 수'), ('steps', '최단 이동 수'), ('time', '계산 시간 (ms, 애니메이션 제외)')]:
            self.table.heading(key, text=text)
            self.table.column(key, anchor='center', width=220)
        self.table.pack(fill='x', padx=14)
        ttk.Label(root, textvariable=self.status, padding=14, wraplength=1050).pack(fill='x')
        root.protocol('WM_DELETE_WINDOW', self.close)

    def close(self):
        self.stop()
        self.root.destroy()

    def color(self, point):
        if point == self.start:
            return self.colors['start']
        if point == self.end:
            return self.colors['end']
        if point in self.path:
            return self.colors['path']
        if point in self.visited:
            return self.colors['visited']
        return self.colors['wall' if self.grid[point[0]][point[1]] else 'empty']

    def draw(self):
        self.canvas.delete('all')
        self.cells = {}
        self.size = max(1, min(self.canvas.winfo_width()/self.cols, self.canvas.winfo_height()/self.rows))
        self.ox = (self.canvas.winfo_width()-self.cols*self.size)/2
        self.oy = (self.canvas.winfo_height()-self.rows*self.size)/2
        for row in range(self.rows):
            for col in range(self.cols):
                x, y = self.ox+col*self.size, self.oy+row*self.size
                self.cells[(row, col)] = self.canvas.create_rectangle(x, y, x+self.size, y+self.size, fill=self.color((row, col)), outline='#e1e7ee', width=1)
        for point, text in ((self.start, 'S'), (self.end, 'E')):
            self.canvas.create_text(self.ox+(point[1]+0.5)*self.size, self.oy+(point[0]+0.5)*self.size, text=text, fill='white', font=('Arial', max(8, int(self.size*0.5)), 'bold'))

    def stop(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.running:
            self.status.set('탐색 표시를 중지했습니다.')
        self.running = False

    def clear(self):
        self.stop()
        self.visited.clear()
        self.path.clear()
        self.table.delete(*self.table.get_children())
        self.draw()

    def edit(self, event):
        col, row = int((event.x-self.ox)//self.size), int((event.y-self.oy)//self.size)
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return
        point = (row, col)
        mode = self.mode.get()
        if mode in ('wall', 'erase') and point in (self.start, self.end):
            return
        if mode == 'start' and point == self.end or mode == 'end' and point == self.start:
            return
        self.clear()
        if mode == 'start':
            self.start = point
            self.grid[row][col] = 0
        elif mode == 'end':
            self.end = point
            self.grid[row][col] = 0
        else:
            self.grid[row][col] = int(mode == 'wall')
        self.draw()
        self.status.set('미로가 변경되었습니다. 탐색을 다시 실행하세요.')

    def generate(self):
        try:
            seed = int(self.seed.get()) if self.seed.get().strip() else None
        except ValueError:
            messagebox.showinfo('시드 입력', '정수를 입력하거나 비워 두세요.')
            return
        self.clear()
        self.start, self.end = (1, 1), (self.rows-2, self.cols-2)
        self.grid = generate_maze(self.rows, self.cols, seed)
        self.draw()
        self.status.set('새 미로를 생성했습니다. 같은 시드는 같은 미로를 만듭니다.')

    def empty(self):
        self.clear()
        self.grid = [[0]*self.cols for _ in range(self.rows)]
        self.draw()
        self.status.set('빈 격자입니다. 마우스로 벽을 그려 보세요.')

    def record(self, result):
        self.table.insert('', 'end', values=(result['algorithm'], len(result['visited']), result['steps'] if result['steps'] is not None else '도달 불가', f"{result['milliseconds']:.3f}"))

    def run(self):
        self.clear()
        result = solve(self.grid, self.start, self.end, self.algorithm.get())
        self.record(result)
        self.running = True
        self.status.set(f"{result['algorithm']} 탐색 과정을 표시하고 있습니다…")
        self.animate(result, 0)

    def animate(self, result, index):
        self.after_id = None
        if not self.running:
            return
        end = min(index+max(1, int(self.speed.get())), len(result['visited']))
        for point in result['visited'][index:end]:
            self.visited.add(point)
            self.canvas.itemconfigure(self.cells[point], fill=self.color(point))
        if end < len(result['visited']):
            self.after_id = self.root.after(30, lambda: self.animate(result, end))
        else:
            self.path = set(result['path'])
            self.running = False
            self.draw()
            self.status.set(f"완료 · 최단 이동 {result['steps']}칸 · 탐색 {len(result['visited'])}칸" if result['path'] else '도착점까지 연결되는 경로가 없습니다. 벽을 일부 지워 보세요.')

    def compare(self):
        self.clear()
        results = [solve(self.grid, self.start, self.end, algorithm) for algorithm in ('BFS', 'A*')]
        for result in results:
            self.record(result)
        self.path = set(results[1]['path'])
        self.visited = set(results[1]['visited'])
        self.draw()
        self.status.set('같은 미로의 결과입니다. 화면은 A* 경로이며 계산 시간은 작은 값이라 실행마다 달라질 수 있습니다.')

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', initialfile='maze.json', filetypes=[('미로 JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(json.dumps({'grid': self.grid, 'start': self.start, 'end': self.end}, ensure_ascii=False, indent=2), encoding='utf-8')
                self.status.set(f'저장 완료 · {Path(path).name}')
            except OSError as exc:
                messagebox.showerror('저장 실패', str(exc))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[('미로 JSON', '*.json')])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            grid = data['grid']
            if len(grid) != self.rows or any(len(row) != self.cols or any(type(cell) is not int or cell not in (0, 1) for cell in row) for row in grid):
                raise ValueError(f'{self.rows}행 {self.cols}열의 0과 1로 된 미로가 필요합니다.')
            start, end = tuple(data['start']), tuple(data['end'])
            for point in (start, end):
                if len(point) != 2 or any(type(value) is not int for value in point):
                    raise ValueError('출발점과 도착점 좌표 형식이 잘못되었습니다.')
            solve(grid, start, end)
            self.clear()
            self.grid, self.start, self.end = grid, start, end
            self.draw()
            self.status.set(f'불러오기 완료 · {Path(path).name}')
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            messagebox.showerror('불러오기 실패', str(exc))


if __name__ == '__main__':
    root = tk.Tk()
    ttk.Style().configure('.', font=('맑은 고딕', 10))
    App(root)
    root.mainloop()
