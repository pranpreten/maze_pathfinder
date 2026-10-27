from collections import deque
from heapq import heappop, heappush
from time import perf_counter
import random


def neighbors(grid, node):
    row, col = node
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        nr, nc = row+dr, col+dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == 0:
            yield nr, nc


def solve(grid, start, end, algorithm='BFS'):
    if algorithm not in ('BFS', 'A*'):
        raise ValueError('지원 알고리즘: BFS, A*')
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('직사각형 격자가 필요합니다.')
    for point in (start, end):
        if not (0 <= point[0] < len(grid) and 0 <= point[1] < len(grid[0])) or grid[point[0]][point[1]]:
            raise ValueError('출발점과 도착점은 통로 안에 있어야 합니다.')
    started = perf_counter()
    parents = {start: None}
    distance = {start: 0}
    visited = []
    closed = set()
    if algorithm == 'BFS':
        frontier = deque([start])
        while frontier:
            node = frontier.popleft()
            visited.append(node)
            if node == end:
                break
            for nxt in neighbors(grid, node):
                if nxt not in parents:
                    parents[nxt] = node
                    distance[nxt] = distance[node]+1
                    frontier.append(nxt)
    else:
        heuristic = lambda point: abs(point[0]-end[0])+abs(point[1]-end[1])
        frontier = [(heuristic(start), heuristic(start), 0, start)]
        serial = 0
        while frontier:
            _, _, _, node = heappop(frontier)
            if node in closed:
                continue
            closed.add(node)
            visited.append(node)
            if node == end:
                break
            for nxt in neighbors(grid, node):
                candidate = distance[node]+1
                if candidate < distance.get(nxt, float('inf')):
                    distance[nxt] = candidate
                    parents[nxt] = node
                    serial += 1
                    heappush(frontier, (candidate+heuristic(nxt), heuristic(nxt), serial, nxt))
    path = []
    if visited and visited[-1] == end:
        node = end
        while node is not None:
            path.append(node)
            node = parents[node]
        path.reverse()
    return {'algorithm': algorithm, 'visited': visited, 'path': path, 'steps': len(path)-1 if path else None, 'milliseconds': (perf_counter()-started)*1000}


def generate_maze(rows=21, cols=31, seed=None):
    if rows < 5 or cols < 5 or rows % 2 == 0 or cols % 2 == 0:
        raise ValueError('미로 크기는 5 이상의 홀수여야 합니다.')
    rng = random.Random(seed)
    grid = [[1]*cols for _ in range(rows)]
    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        row, col = stack[-1]
        candidates = [(row+dr, col+dc) for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)) if 0 < row+dr < rows-1 and 0 < col+dc < cols-1 and grid[row+dr][col+dc]]
        if not candidates:
            stack.pop()
            continue
        nr, nc = rng.choice(candidates)
        grid[(row+nr)//2][(col+nc)//2] = 0
        grid[nr][nc] = 0
        stack.append((nr, nc))
    for row in range(1, rows-1):
        for col in range(1, cols-1):
            if grid[row][col] and rng.random() < 0.05:
                horizontal = grid[row][col-1] == grid[row][col+1] == 0
                vertical = grid[row-1][col] == grid[row+1][col] == 0
                if horizontal or vertical:
                    grid[row][col] = 0
    return grid
