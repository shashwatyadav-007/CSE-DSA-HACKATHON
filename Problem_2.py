
import random
import time
import math
import matplotlib.pyplot as plt

def brute_force(points):
    if len(points) < 2:
        return None, None

    min_dist = float("inf")
    closest_pair = None

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            p1, p2 = points[i], points[j]
            dist = math.dist(p1, p2)

            if dist < min_dist:
                min_dist = dist
                closest_pair = (p1, p2)

    return min_dist, closest_pair


def divide_and_conquer(points):
    if len(points) < 2:
        return None, None

    px = sorted(points, key=lambda p: (p[0], p[1]))
    py = sorted(points, key=lambda p: (p[1], p[0]))

    def dist2(a, b):
        return (
            (a[0] - b[0]) ** 2
            + (a[1] - b[1]) ** 2
        )

    def solve(px, py):
        n = len(px)

        if n <= 3:
            best = float("inf")
            pair = None

            for i in range(n):
                for j in range(i + 1, n):
                    d = dist2(px[i], px[j])

                    if d < best:
                        best = d
                        pair = (px[i], px[j])

            return best, pair

        mid = n // 2
        left_x = px[:mid]
        right_x = px[mid:]
        mid_x = px[mid][0]

        remaining = {}

        for p in left_x:
            remaining[p] = remaining.get(p, 0) + 1

        left_y = []
        right_y = []

        for p in py:
            if remaining.get(p, 0) > 0:
                left_y.append(p)
                remaining[p] -= 1
            else:
                right_y.append(p)

        d1, pair1 = solve(left_x, left_y)
        d2, pair2 = solve(right_x, right_y)

        if d1 <= d2:
            best, pair = d1, pair1
        else:
            best, pair = d2, pair2

        strip = [
            p for p in py
            if (p[0] - mid_x) ** 2 < best
        ]

        for i in range(len(strip)):
            for j in range(i + 1, min(i + 8, len(strip))):
                if (strip[j][1] - strip[i][1]) ** 2 >= best:
                    break

                d = dist2(strip[i], strip[j])

                if d < best:
                    best = d
                    pair = (strip[i], strip[j])

        return best, pair

    min_d2, closest_pair = solve(px, py)

    return math.sqrt(min_d2), closest_pair

def measure(algorithm, points):
    start = time.perf_counter()
    result = algorithm(points)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return result, elapsed_ms

def show_result(name, result):
    distance, pair = result

    if pair is None:
        print(f"{name}: No valid pair")
    else:
        p1, p2 = pair

        print(
            f"{name}: {distance:.6f} "
            f"{p1} {p2}"
        )

def visualize(points, brute_result, dc_result):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    ax = axes[0]

    ax.scatter(
        xs, ys,
        color="gray",
        s=40,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.5,
        label="All Points",
        zorder=1
    )

    if brute_result[1] is not None:
        p1, p2 = brute_result[1]

        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color="red",
            linestyle="--",
            linewidth=2.5,
            label="Brute Force",
            zorder=3
        )

        ax.scatter(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color="red",
            marker="o",
            s=100,
            edgecolors="black",
            linewidths=1,
            zorder=4
        )

    if dc_result[1] is not None:
        p1, p2 = dc_result[1]

        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color="blue",
            linestyle="-",
            linewidth=2,
            label="Divide and Conquer",
            zorder=5
        )

        ax.scatter(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color="blue",
            marker="o",
            s=90,
            edgecolors="white",
            linewidths=2,
            label="DC Closest Points",
            zorder=6
        )

        ax.annotate(
            f"P1 {p1}",
            xy=p1,
            xytext=(10, 10),
            textcoords="offset points",
            color="blue",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.25",
                fc="white",
                ec="blue",
                alpha=0.9
            )
        )

        ax.annotate(
            f"P2 {p2}",
            xy=p2,
            xytext=(10, -18),
            textcoords="offset points",
            color="blue",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.25",
                fc="white",
                ec="blue",
                alpha=0.9
            )
        )

    ax.set_title("Closest Pair Comparison")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax = axes[1]

    ax.scatter(
        xs, ys,
        color="gray",
        s=40,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.5,
        label="All Points",
        zorder=2
    )

    px = sorted(points, key=lambda p: (p[0], p[1]))
    mid = len(px) // 2
    mid_x = px[mid][0]

    left = px[:mid]
    right = px[mid:]

    d_left, _ = brute_force(left)
    d_right, _ = brute_force(right)

    valid_distances = [
        d for d in (d_left, d_right)
        if d is not None
    ]

    d = min(valid_distances) if valid_distances else dc_result[0]

    ax.axvline(
        mid_x,
        color="black",
        linestyle="--",
        linewidth=2,
        label="Dividing Line",
        zorder=3
    )

    ax.axvspan(
        mid_x - d,
        mid_x + d,
        color="orange",
        alpha=0.25,
        label=f"Strip (width {2 * d:.2f})",
        zorder=1
    )

    if dc_result[1] is not None:
        p1, p2 = dc_result[1]

        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color="blue",
            linewidth=2.5,
            marker="o",
            markersize=6,
            markerfacecolor="blue",
            markeredgecolor="white",
            markeredgewidth=1.5,
            label="DC Closest Pair",
            zorder=5
        )

    ax.set_title("Divide and Conquer Strip")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def benchmark():
    sizes = [50, 100, 200, 400, 800, 1200]

    brute_times = []
    dc_times = []

    print("\nPERFORMANCE ANALYSIS")
    print("-" * 65)

    print(
        f"{'N':<10}"
        f"{'Brute Force (ms)':<23}"
        f"{'Divide and Conquer (ms)'}"
    )

    for n in sizes:
        points = [
            (
                random.randint(0, 1000),
                random.randint(0, 1000)
            )
            for _ in range(n)
        ]

        _, t1 = measure(brute_force, points)
        _, t2 = measure(divide_and_conquer, points)

        brute_times.append(t1)
        dc_times.append(t2)

        print(f"{n:<10}{t1:<23.6f}{t2:.6f}")

    plt.figure(figsize=(9, 5))

    plt.plot(
        sizes,
        brute_times,
        marker="o",
        label="Brute Force O(N²)"
    )

    plt.plot(
        sizes,
        dc_times,
        marker="s",
        label="Divide and Conquer O(N log N)"
    )

    plt.xlabel("Number of Points (N)")
    plt.ylabel("Execution Time (ms)")
    plt.title("Running Time Comparison")

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    try:
        n = int(input("Enter number of points (N): "))
    except ValueError:
        print("Please enter a valid integer.")
        return

    if n < 2:
        print("N must be at least 2.")
        print("A closest pair requires at least two points.")
        return

    points = [
        (
            random.randint(0, 1000),
            random.randint(0, 1000)
        )
        for _ in range(n)
    ]

    print("\nGenerated Points:")
    for p in points:
        print(p)

    brute_result, brute_ms = measure(brute_force, points)
    dc_result, dc_ms = measure(divide_and_conquer, points)

    print("\nRESULTS")
    print("-" * 50)

    show_result("Brute Force", brute_result)
    show_result("Divide and Conquer", dc_result)

    print(
        f"Execution time: Brute Force = {brute_ms:.6f} ms, "
        f"Divide and Conquer = {dc_ms:.6f} ms"
    )

    if math.isclose(
        brute_result[0],
        dc_result[0],
        rel_tol=1e-9,
        abs_tol=1e-9
    ):
        print("Verification: Both algorithms agree.")
    else:
        print("Verification FAILED!")

    visualize(points, brute_result, dc_result)
    benchmark()


if __name__ == "__main__":
    main()
