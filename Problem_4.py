import csv
import math
import random
import sys
import time

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation

EXACT_TIME_LIMIT = 30.0
SCALING_TIME_LIMIT = 5.0
SCALING_STEPS = 8

sys.setrecursionlimit(20000)


class SearchTimeout(Exception):
    pass


def random_edges(n, density):
    return [
        (u, v)
        for u in range(1, n + 1)
        for v in range(u + 1, n + 1)
        if random.random() < density
    ]


def read_input():
    print("Option 1: enter N M R followed by M conflict pairs")
    print("Option 2: enter N R and generate a random conflict graph")
    choice = input("Choose option (1 or 2): ").strip()

    if choice == "1":
        n, m, r = map(int, input("Enter N M R: ").split())
        if n < 0:
            raise ValueError("N cannot be negative.")
        if m < 0:
            raise ValueError("M cannot be negative.")
        if n > 0 and r < 1:
            raise ValueError("R must be at least 1.")
        edges = []
        for i in range(m):
            u, v = map(int, input(f"Conflict {i + 1} (u v): ").split())
            edges.append((u, v))
        return n, r, edges

    if choice == "2":
        n, r = map(int, input("Enter N R: ").split())
        if n < 0:
            raise ValueError("N cannot be negative.")
        if n > 0 and r < 1:
            raise ValueError("R must be at least 1.")
        density = float(input("Enter edge density (0 to 1): "))
        if not 0.0 <= density <= 1.0:
            raise ValueError("Density must be between 0 and 1.")
        return n, r, random_edges(n, density)

    raise ValueError("Option must be 1 or 2.")


def create_graph(n, edges):
    if n < 0:
        raise ValueError("N cannot be negative.")

    graph = nx.Graph()
    graph.add_nodes_from(range(1, n + 1))

    for u, v in edges:
        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"Invalid course number in conflict ({u}, {v}).")
        if u == v:
            raise ValueError("A course cannot conflict with itself.")
        graph.add_edge(u, v)

    return graph


def greedy_clique_size(graph):
    adjacency = {v: set(graph[v]) for v in graph}
    best = 0

    for start in adjacency:
        size = 1
        candidates = set(adjacency[start])

        while candidates:
            chosen = max(
                candidates,
                key=lambda x: len(candidates & adjacency[x])
            )
            size += 1
            candidates &= adjacency[chosen]

        best = max(best, size)

    return best


def lower_bound(graph, capacity):
    n = graph.number_of_nodes()

    if n == 0:
        return 0

    return max(math.ceil(n / capacity), greedy_clique_size(graph))


def welsh_powell(graph, capacity):
    order = sorted(graph.nodes(), key=lambda v: (-graph.degree[v], v))
    assignment = {}
    sequence = []
    remaining = order
    slot = 0

    while remaining:
        slot += 1
        members = []
        deferred = []

        for course in remaining:
            if len(members) < capacity and not any(
                graph.has_edge(course, other) for other in members
            ):
                members.append(course)
                assignment[course] = slot
                sequence.append(course)
            else:
                deferred.append(course)

        remaining = deferred

    return assignment, slot, sequence


def exact_backtracking(graph, capacity, greedy_assignment, greedy_slots,
                       low, time_limit):
    n = graph.number_of_nodes()

    if n == 0:
        return {}, 0, True

    if greedy_slots <= low:
        return dict(greedy_assignment), greedy_slots, True

    adjacency = {v: set(graph[v]) for v in graph}
    deadline = time.perf_counter() + time_limit

    for limit in range(low, greedy_slots):
        assignment = {}
        counts = [0] * (limit + 1)
        blocked = {v: [0] * (limit + 1) for v in adjacency}
        saturation = {v: 0 for v in adjacency}

        def place(course, slot):
            assignment[course] = slot
            counts[slot] += 1
            for u in adjacency[course]:
                if blocked[u][slot] == 0:
                    saturation[u] += 1
                blocked[u][slot] += 1

        def unplace(course, slot):
            del assignment[course]
            counts[slot] -= 1
            for u in adjacency[course]:
                blocked[u][slot] -= 1
                if blocked[u][slot] == 0:
                    saturation[u] -= 1

        def search(used):
            if len(assignment) == n:
                return True

            if time.perf_counter() > deadline:
                raise SearchTimeout

            course = max(
                (v for v in adjacency if v not in assignment),
                key=lambda v: (saturation[v], len(adjacency[v]))
            )

            for slot in range(1, min(used + 1, limit) + 1):
                if counts[slot] >= capacity or blocked[course][slot]:
                    continue

                place(course, slot)

                if search(max(used, slot)):
                    return True

                unplace(course, slot)

            return False

        try:
            if search(0):
                return dict(assignment), limit, True
        except SearchTimeout:
            return dict(greedy_assignment), greedy_slots, False

    return dict(greedy_assignment), greedy_slots, True


def slot_color(slot, slots):
    if slots <= 20:
        return plt.get_cmap("tab20")((slot - 1) % 20)
    return plt.get_cmap("hsv")((slot - 1) / slots)


def slot_courses(assignment, slots):
    return [
        sorted(c for c, s in assignment.items() if s == slot)
        for slot in range(1, slots + 1)
    ]


def print_timetable(title, assignment, slots, optimal, filename, capacity):
    print("\n" + "=" * 45)
    print(title)
    print("=" * 45)
    print("Slots used:", slots)
    print("Proven optimal:", "Yes" if optimal else "No")

    rows = slot_courses(assignment, slots)

    for index, courses in enumerate(rows, start=1):
        print(f"Slot {index}: {', '.join(map(str, courses))}")

    columns = min(capacity, len(assignment))

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Slot"] + [f"Hall_{i}" for i in range(1, columns + 1)]
        )
        for index, courses in enumerate(rows, start=1):
            writer.writerow(
                [f"Slot_{index}"] + courses + [""] * (columns - len(courses))
            )

    print("CSV saved:", filename)


def visualize(graph, assignment, slots):
    rows = slot_courses(assignment, slots)
    columns = max((len(row) for row in rows), default=1)
    colors = [slot_color(assignment[node], slots) for node in graph.nodes()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    nx.draw_networkx(
        graph,
        nx.spring_layout(graph, seed=42),
        ax=ax1,
        with_labels=True,
        node_color=colors,
        node_size=700,
        edge_color="gray"
    )
    ax1.set_title("Conflict Graph")
    ax1.axis("off")

    ax2.set_title("Exam Timetable")
    ax2.set_xlabel("Hall")
    ax2.set_ylabel("Time Slot")
    ax2.set_xlim(0.5, columns + 0.5)
    ax2.set_ylim(slots + 0.5, 0.5)
    ax2.set_xticks(range(1, columns + 1))
    ax2.set_yticks(range(1, slots + 1))
    ax2.grid(True, alpha=0.3)

    for slot, courses in enumerate(rows, start=1):
        for hall, course in enumerate(courses, start=1):
            ax2.add_patch(
                plt.Rectangle(
                    (hall - 0.4, slot - 0.4),
                    0.8,
                    0.8,
                    facecolor=slot_color(slot, slots),
                    edgecolor="black"
                )
            )
            ax2.text(hall, slot, str(course), ha="center", va="center")

    plt.tight_layout()
    plt.show()


def animate_assignment(graph, assignment, sequence, slots):
    fig, ax = plt.subplots(figsize=(7, 6))
    position = nx.spring_layout(graph, seed=42)
    nodes = list(graph.nodes())

    def draw(frame):
        ax.clear()
        done = set(sequence[:frame])
        colors = [
            slot_color(assignment[v], slots) if v in done else "lightgray"
            for v in nodes
        ]
        nx.draw_networkx(
            graph,
            position,
            ax=ax,
            with_labels=True,
            node_color=colors,
            node_size=700,
            edge_color="gray"
        )
        if 0 < frame <= len(sequence):
            last = sequence[frame - 1]
            ax.set_title(
                f"Step {frame}/{len(sequence)}: "
                f"course {last} -> slot {assignment[last]}"
            )
        else:
            ax.set_title("Welsh-Powell assignment order")
        ax.axis("off")

    animation = FuncAnimation(
        fig,
        draw,
        frames=len(sequence) + 1,
        interval=700,
        repeat=False
    )
    plt.show()
    return animation


def run_both(graph, capacity, time_limit):
    low = lower_bound(graph, capacity)

    start = time.perf_counter()
    greedy_assignment, greedy_slots, sequence = welsh_powell(graph, capacity)
    greedy_time = time.perf_counter() - start

    start = time.perf_counter()
    exact_assignment, exact_slots, optimal = exact_backtracking(
        graph, capacity, greedy_assignment, greedy_slots, low, time_limit
    )
    exact_time = time.perf_counter() - start

    return {
        "low": low,
        "greedy": (greedy_assignment, greedy_slots, greedy_time, sequence),
        "exact": (exact_assignment, exact_slots, exact_time, optimal),
    }


def scaling_comparison(n, capacity, density):
    sizes = sorted({
        max(1, round(n * step / SCALING_STEPS))
        for step in range(1, SCALING_STEPS + 1)
    })
    rows = []

    print("\nScaling comparison (density %.2f, R = %d)" % (density, capacity))
    print(f"{'N':>5} {'WP slots':>9} {'WP time':>10} "
          f"{'BT slots':>9} {'BT time':>10} {'Optimal':>8}")

    for size in sizes:
        graph = create_graph(size, random_edges(size, density))
        result = run_both(graph, capacity, SCALING_TIME_LIMIT)
        _, g_slots, g_time, _ = result["greedy"]
        _, e_slots, e_time, optimal = result["exact"]
        rows.append((size, g_slots, g_time, e_slots, e_time))
        print(f"{size:>5} {g_slots:>9} {g_time:>10.6f} "
              f"{e_slots:>9} {e_time:>10.6f} {'Yes' if optimal else 'No':>8}")

    xs = [r[0] for r in rows]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(xs, [r[1] for r in rows], marker="o", label="Welsh-Powell")
    ax1.plot(xs, [r[3] for r in rows], marker="s", label="Backtracking")
    ax1.set_title("Time Slots Used vs N")
    ax1.set_xlabel("N (courses)")
    ax1.set_ylabel("Slots")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(xs, [r[2] for r in rows], marker="o", label="Welsh-Powell")
    ax2.plot(xs, [r[4] for r in rows], marker="s", label="Backtracking")
    ax2.set_title("Running Time vs N")
    ax2.set_xlabel("N (courses)")
    ax2.set_ylabel("Seconds")
    ax2.set_yscale("log")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def ask_yes_no(prompt):
    return input(prompt).strip().lower().startswith("y")


def main():
    try:
        n, capacity, edges = read_input()

        if n > 0 and capacity <= 0:
            raise ValueError("R must be at least 1.")

        graph = create_graph(n, edges)

        print("\nNumber of courses:", n)
        print("Number of conflicts:", graph.number_of_edges())
        print("Maximum exams per slot:", capacity)

        result = run_both(graph, capacity, EXACT_TIME_LIMIT)
        low = result["low"]
        g_assignment, g_slots, g_time, sequence = result["greedy"]
        e_assignment, e_slots, e_time, e_optimal = result["exact"]
        g_optimal = g_slots <= low

        print_timetable(
            "Welsh Powell Greedy",
            g_assignment,
            g_slots,
            g_optimal,
            "welsh_powell_timetable.csv",
            capacity
        )
        print_timetable(
            "Exact Backtracking",
            e_assignment,
            e_slots,
            e_optimal,
            "exact_backtracking_timetable.csv",
            capacity
        )

        print("\n" + "=" * 45)
        print("Comparison")
        print("=" * 45)
        print("Lower bound on slots:", low)
        print(f"Welsh-Powell : {g_slots} slots, {g_time:.6f}s, "
              f"proven optimal: {'Yes' if g_optimal else 'No'}")
        print(f"Backtracking : {e_slots} slots, {e_time:.6f}s, "
              f"proven optimal: {'Yes' if e_optimal else 'No'}")

        if n == 0:
            return

        visualize(graph, e_assignment, e_slots)

        if ask_yes_no("\nAnimate Welsh-Powell assignment order? (y/n): "):
            animate_assignment(graph, g_assignment, sequence, g_slots)

        if ask_yes_no("Run scaling comparison as N increases? (y/n): "):
            max_pairs = n * (n - 1) / 2
            density = graph.number_of_edges() / max_pairs if max_pairs else 0.0
            scaling_comparison(n, capacity, density)

    except ValueError as error:
        print("Input error:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nProgram stopped.")


if __name__ == "__main__":
    main()
