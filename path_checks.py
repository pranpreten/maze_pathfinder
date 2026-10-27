import random
import unittest
from search import solve, generate_maze


class MazeTests(unittest.TestCase):
    def test_known_shortest_path(self):
        grid = [[0, 1, 0], [0, 1, 0], [0, 0, 0]]
        for name in ('BFS', 'A*'):
            result = solve(grid, (0, 0), (0, 2), name)
            self.assertEqual(result['steps'], 6)
            self.assertEqual(result['path'][0], (0, 0))
            self.assertEqual(result['path'][-1], (0, 2))

    def test_unreachable_and_same_point(self):
        for name in ('BFS', 'A*'):
            self.assertIsNone(solve([[0, 1, 0]], (0, 0), (0, 2), name)['steps'])
            self.assertEqual(solve([[0]], (0, 0), (0, 0), name)['steps'], 0)

    def test_random_grids_match_bfs(self):
        rng = random.Random(17)
        for _ in range(40):
            grid = [[int(rng.random() < 0.3) for _ in range(17)] for _ in range(13)]
            grid[0][0] = grid[-1][-1] = 0
            bfs = solve(grid, (0, 0), (12, 16), 'BFS')
            astar = solve(grid, (0, 0), (12, 16), 'A*')
            self.assertEqual(astar['steps'], bfs['steps'])
            for a, b in zip(astar['path'], astar['path'][1:]):
                self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]), 1)
                self.assertEqual(grid[b[0]][b[1]], 0)

    def test_generation(self):
        self.assertEqual(generate_maze(seed=42), generate_maze(seed=42))
        for seed in range(10):
            self.assertTrue(solve(generate_maze(seed=seed), (1, 1), (19, 29))['path'])

    def test_blocked_endpoint(self):
        with self.assertRaises(ValueError):
            solve([[1, 0]], (0, 0), (0, 1))


if __name__ == '__main__':
    unittest.main()
