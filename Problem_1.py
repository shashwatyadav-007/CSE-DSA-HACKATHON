import argparse
import csv
import random
import sys
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

KEYS = 'abcdfg'
DOORS = 'ABCDFG'

def is_key(ch):
    return len(ch) == 1 and ch in KEYS

def is_door(ch):
    return len(ch) == 1 and ch in DOORS

def bit(ch):
    return 1 << KEYS.index(ch.lower())

def find(grid, ch):
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == ch:
                return (r, c)
    return None

def solve(grid):
    R, C = len(grid), len(grid[0])
    s, e = find(grid, 'S'), find(grid, 'E')
    if s is None or e is None:
        return None
    start = (s[0], s[1], 0)
    parent = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        r, c, m = cur
        if (r, c) == e:
            path = []
            while cur is not None:
                path.append((cur[0], cur[1]))
                cur = parent[cur]
            return path[::-1]
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < R and 0 <= nc < C):
                continue
            ch = grid[nr][nc]
            if ch == '#':
                continue
            nm = m
            if is_door(ch) and not m & bit(ch):
                continue
            if is_key(ch):
                nm |= bit(ch)
            nxt = (nr, nc, nm)
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)
    return None

def read_csv(path):
    grid = []
    with open(path, newline='') as f:
        for row in csv.reader(f):
            if not row or all(not x.strip() for x in row):
                continue
            cells = []
            for x in row:
                x = x.strip()
                if x == '':
                    x = '.'
                elif len(x) == 2 and x[0] == 'x':      
                    x = x[1]
                elif x == 'x':
                    x = '.'
                cells.append(x)
            grid.append(cells)
    if not grid:
        raise ValueError("empty grid")
    w = len(grid[0])
    if any(len(r) != w for r in grid):
        raise ValueError("rows have different lengths")
    return grid

def write_csv(path, grid):
    with open(path, 'w', newline='') as f:
        csv.writer(f).writerows(grid)

def mark_path(grid, path):
    out = [row[:] for row in grid]
    for r, c in path:
        ch = out[r][c]
        if ch in 'SE':
            continue
        out[r][c] = 'x' if ch == '.' else 'x' + ch
    return out

def _bfs_dist(grid, src, blocked=lambda ch: ch == '#'):
    R, C = len(grid), len(grid[0])
    dist, par = {src: 0}, {src: None}
    q = deque([src])
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            n = (r + dr, c + dc)
            if 0 <= n[0] < R and 0 <= n[1] < C and n not in dist \
                    and not blocked(grid[n[0]][n[1]]):
                dist[n] = dist[(r, c)] + 1
                par[n] = (r, c)
                q.append(n)
    return dist, par

def generate(n, T, rng, loops=0.04):
    if n < 7:
        raise ValueError("N must be at least 7")
    for _ in range(200):
        g = [['#'] * n for _ in range(n)]
        g[1][1] = '.'
        stack = [(1, 1)]
        while stack:                                  
            r, c = stack[-1]
            nb = [(r + 2 * dr, c + 2 * dc, r + dr, c + dc) for dr, dc in DIRS
                  if 1 <= r + 2 * dr <= n - 2 and 1 <= c + 2 * dc <= n - 2
                  and g[r + 2 * dr][c + 2 * dc] == '#']
            if not nb:
                stack.pop()
                continue
            nr, nc, wr, wc = rng.choice(nb)
            g[wr][wc] = g[nr][nc] = '.'
            stack.append((nr, nc))
        for r in range(1, n - 1):                     
            for c in range(1, n - 1):
                if g[r][c] == '#' and rng.random() < loops and (
                        (g[r - 1][c] == '.' and g[r + 1][c] == '.') or
                        (g[r][c - 1] == '.' and g[r][c + 1] == '.')):
                    g[r][c] = '.'

        dist, par = _bfs_dist(g, (1, 1))
        e = max(dist, key=lambda p: (dist[p], rng.random()))
        path = [e]
        while par[path[-1]] is not None:
            path.append(par[path[-1]])
        path.reverse()
        interior = len(path) - 2
        if interior < 2 * T:
            continue

        seg = interior // T
        idx = [1 + i * seg + rng.randrange(seg) for i in range(T)]
        letters = list(DOORS[:T])
        rng.shuffle(letters)
        for i, p in zip(idx, letters):
            r, c = path[i]
            g[r][c] = p
        g[1][1], g[e[0]][e[1]] = 'S', 'E'

        ok = True
        for i, d in enumerate(letters):
            closed = set(letters[i:])
            reach, _ = _bfs_dist(g, (1, 1), lambda ch: ch == '#' or ch in closed)
            free = [p for p in reach if g[p[0]][p[1]] == '.']
            if not free:
                ok = False
                break
            r, c = rng.choice(free)
            g[r][c] = d.lower()
        if ok and solve(g) is not None:
            return g
    raise RuntimeError("could not generate a maze; try a larger N")

KEY_COLORS = {'a': '#1f77b4', 'b': '#ff7f0e', 'c': '#9467bd',
              'd': '#8c564b', 'f': '#17becf', 'g': '#e377c2'}

def visualize(grid, path, T, gif=None, show=True, interval=350):
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.patches import Rectangle, Circle

    R, C = len(grid), len(grid[0])
    present = sorted({ch for row in grid for ch in row if is_key(ch)})
    fig = plt.figure(figsize=(10, 6.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[5, 1.1])
    ax, inv = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    L = len(path) - 1 if path else 0
    HOLD = 6

    held = []                  
    picked, opened = [], []    
    h, p_, o_ = set(), set(), set()
    for (r, c) in (path or []):
        ch = grid[r][c]
        if is_key(ch):
            h.add(ch)
            p_.add((r, c))
        elif is_door(ch):
            o_.add((r, c))
        held.append(set(h)); picked.append(set(p_)); opened.append(set(o_))

    def unlock_icon(r, c, col):
        ax.add_patch(Rectangle((c - .2, r - .02), .4, .28, color=col, zorder=5))
        ax.plot([c - .1, c - .1, c + .1, c + .1],
                [r - .02, r - .27, r - .27, r - .15],
                color=col, lw=2.2, zorder=5, solid_capstyle='round')

    def draw(k):
        k = min(k, L)
        ax.clear()
        ax.set_xlim(-.5, C - .5)
        ax.set_ylim(R - .5, -.5)
        ax.set_aspect('equal')
        ax.axis('off')
        trail = set(path[:k + 1]) if path else set()
        for r in range(R):
            for c in range(C):
                ch = grid[r][c]
                face = 'white'
                if ch == '#':
                    face = 'black'
                elif ch == 'S':
                    face = '#2ca02c'
                elif ch == 'E':
                    face = '#d62728'
                elif is_door(ch) and (r, c) not in (opened[k] if path else ()):
                    face = KEY_COLORS[ch.lower()]
                elif (r, c) in trail:
                    face = '#fff2a8'
                ax.add_patch(Rectangle((c - .5, r - .5), 1, 1, facecolor=face,
                                       edgecolor='#bbbbbb', lw=.5))
                if is_key(ch) and (r, c) not in (picked[k] if path else ()):
                    ax.add_patch(Circle((c, r), .3, color=KEY_COLORS[ch], zorder=4))
                    ax.text(c, r, ch, ha='center', va='center', color='white',
                            fontweight='bold', zorder=6)
                elif is_door(ch):
                    if path and (r, c) in opened[k]:
                        unlock_icon(r, c, KEY_COLORS[ch.lower()])
                    else:
                        ax.text(c, r, ch, ha='center', va='center',
                                color='white', fontweight='bold', zorder=6)
                elif ch in 'SE':
                    ax.text(c, r, ch, ha='center', va='center',
                            color='white', fontweight='bold')
        if path:
            xs = [c for r, c in path[:k + 1]]
            ys = [r for r, c in path[:k + 1]]
            ax.plot(xs, ys, color='#e6a700', lw=3, alpha=.9, zorder=3)
            ax.add_patch(Circle((xs[-1], ys[-1]), .22, color='#111133', zorder=7))
            ax.set_title(f"Step {k}/{L}")
        else:
            ax.set_title("No path exists (-1)")

        inv.clear()
        inv.set_xlim(0, 1)
        inv.set_ylim(len(present) + .5, -.5)
        inv.set_aspect('equal')
        inv.axis('off')
        inv.set_title("Keys")
        hk = held[k] if path else set()
        for i, kc in enumerate(present):
            got = kc in hk
            inv.add_patch(Rectangle((.1, i - .4), .8, .8,
                                    facecolor=KEY_COLORS[kc] if got else '#eeeeee',
                                    edgecolor='#555555'))
            inv.text(.5, i, kc if got else kc + ' ?', ha='center', va='center',
                     color='white' if got else '#999999', fontweight='bold')

    anim = FuncAnimation(fig, draw, frames=L + 1 + HOLD, interval=interval,
                         repeat=True)
    if gif:
        anim.save(gif, writer='pillow', fps=max(1, int(1000 / interval)))
        print(f"saved animation to {gif}", file=sys.stderr)
    if show:
        plt.show()
    return anim

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--csv', help='read the grid from this CSV (Option 1)')
    ap.add_argument('--n', type=int, default=15, help='size N when generating (Option 2)')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--out', default='solution.csv', help='CSV with the path marked')
    ap.add_argument('--save-grid', default='maze.csv', help='where to store a generated grid')
    ap.add_argument('--no-viz', action='store_true')
    ap.add_argument('--no-show', action='store_true', help='do not open a window')
    ap.add_argument('--gif', help='save the animation as a GIF')
    ap.add_argument('--interval', type=int, default=350, help='ms per animation frame')
    a = ap.parse_args()

    if sys.stdin.isatty():
        print("Enter T (1-6): ", end='', file=sys.stderr, flush=True)
    try:
        T = int(sys.stdin.readline().split()[0])
    except (IndexError, ValueError):
        sys.exit("first stdin line must be the integer T")
    if not 1 <= T <= 6:
        sys.exit("T must be between 1 and 6")

    if a.csv:
        grid = read_csv(a.csv)
    else:
        grid = generate(a.n, T, random.Random(a.seed))
        write_csv(a.save_grid, grid)
        print(f"generated maze saved to {a.save_grid}", file=sys.stderr)

    path = solve(grid)
    print(len(path) - 1 if path else -1)
    if path:
        write_csv(a.out, mark_path(grid, path))
        print(f"marked path written to {a.out}", file=sys.stderr)

    if not a.no_viz:
        visualize(grid, path, T, gif=a.gif, show=not a.no_show, interval=a.interval)

if __name__ == '__main__':
    main()
