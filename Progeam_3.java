import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Random;
import java.util.Scanner;        
import java.io.*;
import java.util.*;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Polygon;
import java.awt.RenderingHints;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import java.awt.BorderLayout;
import java.awt.FlowLayout;

public class Main_3 {

    static final long INF = Long.MAX_VALUE;

    static class Flight {
        int from, to, id;
        long price;

        Flight(int from, int to, long price, int id) {
            this.from = from;
            this.to = to;
            this.price = price;
            this.id = id;
        }
    }

    static class State implements Comparable<State> {
        int city, flights, coupons;
        long cost;

        State(int city, int flights, int coupons, long cost) {
            this.city = city;
            this.flights = flights;
            this.coupons = coupons;
            this.cost = cost;
        }

        public int compareTo(State other) {
            return Long.compare(this.cost, other.cost);
        }
    }

    static class Previous {
        int city, flights, coupons, flightId;
        boolean couponUsed;

        Previous(int city, int flights, int coupons,
                 int flightId, boolean couponUsed) {
            this.city = city;
            this.flights = flights;
            this.coupons = coupons;
            this.flightId = flightId;
            this.couponUsed = couponUsed;
        }
    }

    static class Result {
        long minCost = INF;
        List<Flight> path = new ArrayList<>();
        List<Boolean> couponsUsed = new ArrayList<>();
        int flightsUsed;
        int couponsUsedCount;
    }

    static class GraphData {
        List<Flight> flights = new ArrayList<>();
        int maxCity = 0;
    }

    static Scanner sc = new Scanner(System.in);

    static int readInt(String message, int minValue) {
        while (true) {
            System.out.print(message);

            if (sc.hasNextInt()) {
                int value = sc.nextInt();

                if (value >= minValue) {
                    return value;
                }
            } else {
                sc.next();
            }

            System.out.println(
                "Invalid input. Please enter an integer >= "
                + minValue + "."
            );
        }
    }

    static long readLong(String message, long minValue) {
        while (true) {
            System.out.print(message);

            if (sc.hasNextLong()) {
                long value = sc.nextLong();

                if (value >= minValue) {
                    return value;
                }
            } else {
                sc.next();
            }

            System.out.println(
                "Invalid input. Please enter a value >= "
                + minValue + "."
            );
        }
    }

    static void addFlight(GraphData graph,
                          int u, int v, long price) {
        int id = graph.flights.size();

        graph.flights.add(new Flight(u, v, price, id));
        graph.maxCity = Math.max(graph.maxCity, Math.max(u, v));
    }

    // Option 1: Read flights manually.
    static GraphData manualInput(int N, int M) {
        GraphData graph = new GraphData();
        graph.maxCity = N;

        System.out.println("\nEnter the flight details.");
        System.out.println(
            "For each flight, enter:\nsource\tdestination\tprice"
        );
        System.out.println("Example:\n1\t2\t500\n");

        for (int i = 0; i < M; i++) {
            while (true) {
                System.out.println("Flight " + (i + 1) + " of " + M);

                int u = readInt("  Source city: ", 1);
                int v = readInt("  Destination city: ", 1);
                long price = readLong("  Ticket price: ", 0);

                if (u > N || v > N) {
                    System.out.println(
                        "Error: Cities must be between 1 and " + N
                    );
                    continue;
                }

                addFlight(graph, u, v, price);
                break;
            }
        }

        return graph;
    }

    // Option 2: Read a CSV file with columns u,v,price.
    static GraphData csvInput(String filename) throws IOException {
        GraphData graph = new GraphData();

        try (BufferedReader br = new BufferedReader(
                new FileReader(filename))) {

            String line;
            int lineNumber = 0;

            while ((line = br.readLine()) != null) {
                lineNumber++;
                line = line.trim();

                if (line.isEmpty()) {
                    continue;
                }

                String[] parts = line.split(",");

                if (parts.length < 3) {
                    throw new IOException(
                        "Invalid CSV format at line " + lineNumber
                    );
                }

                // Skip a header such as u,v,price.
                if (lineNumber == 1 &&
                    parts[0].trim().equalsIgnoreCase("u")) {
                    continue;
                }

                try {
                    int u = Integer.parseInt(parts[0].trim());
                    int v = Integer.parseInt(parts[1].trim());
                    long price = Long.parseLong(parts[2].trim());

                    if (u < 1 || v < 1 || price < 0) {
                        throw new IOException(
                            "Invalid city or price at line "
                            + lineNumber
                        );
                    }

                    addFlight(graph, u, v, price);

                } catch (NumberFormatException e) {
                    throw new IOException(
                        "Invalid numeric data at line " + lineNumber
                    );
                }
            }
        }

        if (graph.flights.isEmpty()) {
            throw new IOException("The CSV file contains no flights.");
        }

        return graph;
    }

    // Option 3: Generate a random directed graph.
    static GraphData generateGraph(int N, int M, int K) {
        GraphData graph = new GraphData();
        graph.maxCity = N;

        Random random = new Random();

        // Guarantee a route from city 1 to city N within the stop limit,
        // whenever N > 1. A route with K stops can use at most K + 1 flights.
        int maxAllowedFlights = K + 1;
        int routeFlights = Math.min(N - 1, maxAllowedFlights);

        if (N > 1) {
            for (int step = 0; step < routeFlights; step++) {
                int u = (step == 0) ? 1 : step + 1;
                int v = (step == routeFlights - 1) ? N : step + 2;
                long price = 100 + random.nextInt(901);
                addFlight(graph, u, v, price);
            }
        }

        // Add the remaining random flights.
        while (graph.flights.size() < M) {
            int u = 1 + random.nextInt(N);
            int v = 1 + random.nextInt(N);

            if (N > 1 && u == v) {
                continue;
            }

            long price = 100 + random.nextInt(901);
            addFlight(graph, u, v, price);
        }

        return graph;
    }

    static Result findMinimumCost(GraphData graph,
                                  int N, int K, int C) {

        int maxFlights = K + 1;
        int maxCoupons = Math.min(C, maxFlights);

        List<List<Flight>> adj = new ArrayList<>();

        for (int i = 0; i <= N; i++) {
            adj.add(new ArrayList<>());
        }

        for (Flight f : graph.flights) {
            adj.get(f.from).add(f);
        }

        long[][][] dist =
            new long[N + 1][maxFlights + 1][maxCoupons + 1];

        Previous[][][] prev =
            new Previous[N + 1][maxFlights + 1]
                        [maxCoupons + 1];

        for (int city = 0; city <= N; city++) {
            for (int f = 0; f <= maxFlights; f++) {
                Arrays.fill(dist[city][f], INF);
            }
        }

        PriorityQueue<State> pq = new PriorityQueue<>();

        dist[1][0][0] = 0;
        pq.offer(new State(1, 0, 0, 0));

        while (!pq.isEmpty()) {
            State cur = pq.poll();

            if (cur.cost !=
                dist[cur.city][cur.flights][cur.coupons]) {
                continue;
            }

            if (cur.flights == maxFlights) {
                continue;
            }

            for (Flight flight : adj.get(cur.city)) {
                int v = flight.to;
                int nf = cur.flights + 1;

                // Choice 1: Pay the full ticket price.
                if (cur.cost <= INF - flight.price) {
                    long newCost = cur.cost + flight.price;

                    if (newCost <
                        dist[v][nf][cur.coupons]) {

                        dist[v][nf][cur.coupons] = newCost;

                        prev[v][nf][cur.coupons] =
                            new Previous(
                                cur.city, cur.flights,
                                cur.coupons, flight.id, false
                            );

                        pq.offer(new State(
                            v, nf, cur.coupons, newCost
                        ));
                    }
                }

                // Choice 2: Apply a coupon.
                if (cur.coupons < maxCoupons) {
                    int nc = cur.coupons + 1;
                    long discountedPrice = flight.price / 2;

                    if (cur.cost <= INF - discountedPrice) {
                        long newCost =
                            cur.cost + discountedPrice;

                        if (newCost < dist[v][nf][nc]) {
                            dist[v][nf][nc] = newCost;

                            prev[v][nf][nc] =
                                new Previous(
                                    cur.city, cur.flights,
                                    cur.coupons, flight.id, true
                                );

                            pq.offer(new State(
                                v, nf, nc, newCost
                            ));
                        }
                    }
                }
            }
        }

        Result result = new Result();

        // Choose the cheapest valid destination state.
        int bestF = -1, bestC = -1;

        for (int f = 0; f <= maxFlights; f++) {
            for (int c = 0; c <= maxCoupons; c++) {
                if (dist[N][f][c] < result.minCost) {
                    result.minCost = dist[N][f][c];
                    bestF = f;
                    bestC = c;
                }
            }
        }

        if (result.minCost == INF) {
            return result;
        }

        result.flightsUsed = bestF;
        result.couponsUsedCount = bestC;

        // Reconstruct the exact selected flights.
        int city = N, f = bestF, c = bestC;

        while (f > 0) {
            Previous p = prev[city][f][c];

            if (p == null) {
                throw new IllegalStateException(
                    "Unable to reconstruct the selected route."
                );
            }

            Flight original = graph.flights.get(p.flightId);

            result.path.add(original);
            result.couponsUsed.add(p.couponUsed);

            city = p.city;
            f = p.flights;
            c = p.coupons;
        }

        Collections.reverse(result.path);
        Collections.reverse(result.couponsUsed);

        return result;
    }

    // Output 2: Write all flights to a CSV file.
    static void writeOutputCSV(GraphData graph,
                               Result result,
                               String filename) throws IOException {

        Map<Integer, Boolean> selected = new HashMap<>();
        Map<Integer, Boolean> couponMap = new HashMap<>();

        for (int i = 0; i < result.path.size(); i++) {
            int id = result.path.get(i).id;
            selected.put(id, true);
            couponMap.put(id, result.couponsUsed.get(i));
        }

        try (PrintWriter out = new PrintWriter(
                new FileWriter(filename))) {

            out.println(
                "u,v,price,selected,coupon_used,paid_price"
            );

            for (Flight f : graph.flights) {
                boolean isSelected =
                    selected.getOrDefault(f.id, false);

                boolean coupon =
                    couponMap.getOrDefault(f.id, false);

                long paidPrice =
                    coupon ? f.price / 2 : f.price;

                out.printf(
                    Locale.US, "%d,%d,%d,%s,%s,%d%n",
                    f.from, f.to, f.price,
                    isSelected ? "x" : "",
                    isSelected && coupon ? "yes" :
                        (isSelected ? "no" : ""),
                    isSelected ? paidPrice : 0
                );
            }
        }
    }

    // Graph visualization and animated journey using Java Swing.
    static class GraphVisualizer extends JPanel {
        private final GraphData graph;
        private final Result result;
        private final int cityCount;
        private int animatedFlights = 0;
        private long runningCost = 0;
        private final JLabel status = new JLabel("Preparing journey...", SwingConstants.CENTER);
        private final Timer timer;

        GraphVisualizer(GraphData graph, Result result, int cityCount) {
            this.graph = graph;
            this.result = result;
            this.cityCount = cityCount;
            setPreferredSize(new Dimension(1100, 740));
            setBackground(new Color(18, 24, 38));
            setLayout(new BorderLayout());

            status.setForeground(Color.WHITE);
            status.setFont(new Font("SansSerif", Font.BOLD, 16));
            status.setBorder(BorderFactory.createEmptyBorder(12, 8, 12, 8));
            status.setOpaque(true);
            status.setBackground(new Color(30, 41, 59));
            add(status, BorderLayout.SOUTH);

            timer = new Timer(1100, e -> advanceAnimation());
            if (result.minCost == INF || result.path.isEmpty()) {
                status.setText("No valid route from city 1 to city " + cityCount
                        + ". All flights are shown without a journey animation.");
            } else {
                status.setText("Journey starts at City 1 | Running cost: 0 | Flights used: 0 | Stops used: 0");
                timer.start();
            }
        }

        private void advanceAnimation() {
            if (animatedFlights < result.path.size()) {
                Flight flight = result.path.get(animatedFlights);
                boolean coupon = result.couponsUsed.get(animatedFlights);
                runningCost += coupon ? flight.price / 2 : flight.price;
                animatedFlights++;
                int stopsUsed = Math.max(0, animatedFlights - 1);
                status.setText("Reached City " + flight.to + " | Running cost: " + runningCost
                        + " | Flights used: " + animatedFlights + " | Stops used: " + stopsUsed
                        + (coupon ? " | COUPON: " + flight.price + " → " + (flight.price / 2) : ""));
                repaint();
            } else {
                timer.stop();
                status.setText("Journey complete | Minimum cost: " + result.minCost
                        + " | Intermediate stops: " + Math.max(0, result.flightsUsed - 1)
                        + " | Coupons used: " + result.couponsUsedCount);
            }
        }

        private java.awt.Point pointForCity(int city, int width, int height) {
            double cx = width / 2.0;
            double cy = height / 2.0;
            double radius = Math.max(80, Math.min(width * 0.36, height * 0.37));
            if (cityCount == 1) return new java.awt.Point((int) cx, (int) cy);
            double angle = -Math.PI / 2 + 2 * Math.PI * (city - 1) / cityCount;
            return new java.awt.Point((int) (cx + radius * Math.cos(angle)),
                    (int) (cy + radius * Math.sin(angle)));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int w = getWidth();
            int h = getHeight() - 55;

            Map<Integer, Integer> selectedIndex = new HashMap<>();
            Map<Integer, Boolean> couponById = new HashMap<>();
            Set<Integer> routeCities = new HashSet<>();
            routeCities.add(1);
            for (int i = 0; i < result.path.size(); i++) {
                Flight f = result.path.get(i);
                selectedIndex.put(f.id, i);
                couponById.put(f.id, result.couponsUsed.get(i));
                routeCities.add(f.from);
                routeCities.add(f.to);
            }

            // Draw every directed flight. Each flight gets a readable price badge.
            // Slightly offset labels perpendicular to the edge to reduce overlap.
            for (int edgeIndex = 0; edgeIndex < graph.flights.size(); edgeIndex++) {
                Flight f = graph.flights.get(edgeIndex);
                java.awt.Point a = pointForCity(f.from, w, h);
                java.awt.Point b = pointForCity(f.to, w, h);
                boolean selected = selectedIndex.containsKey(f.id);
                int routeIndex = selectedIndex.getOrDefault(f.id, Integer.MAX_VALUE);
                boolean alreadyTravelled = selected && routeIndex < animatedFlights;
                boolean coupon = couponById.getOrDefault(f.id, false);

                if (selected && coupon) g2.setColor(new Color(245, 190, 55));
                else if (selected && alreadyTravelled) g2.setColor(new Color(34, 211, 238));
                else if (selected) g2.setColor(new Color(100, 180, 255));
                else g2.setColor(new Color(100, 116, 139, 190));
                g2.setStroke(new BasicStroke(selected ? 3.4f : 1.8f));

                if (f.from == f.to) {
                    g2.drawOval(a.x - 22, a.y - 38, 44, 30);
                } else {
                    drawArrow(g2, a.x, a.y, b.x, b.y);
                }

                String label = coupon && selected
                        ? f.price + " -> " + (f.price / 2)
                        : String.valueOf(f.price);
                double dx = b.x - a.x;
                double dy = b.y - a.y;
                double len = Math.max(1.0, Math.sqrt(dx * dx + dy * dy));
                // Alternate badge positions for nearby/parallel edges.
                int side = (edgeIndex % 2 == 0) ? 1 : -1;
                int offset = 24 + ((edgeIndex / 2) % 4) * 16;
                int lx = (a.x + b.x) / 2 + (int) (-dy / len * offset * side);
                int ly = (a.y + b.y) / 2 + (int) (dx / len * offset * side);
                g2.setFont(new Font("SansSerif", Font.BOLD, 12));
                java.awt.FontMetrics fm = g2.getFontMetrics();
                int labelWidth = fm.stringWidth(label);
                int labelHeight = fm.getHeight();
                int badgeX = lx - labelWidth / 2 - 6;
                int badgeY = ly - labelHeight / 2 - 2;
                g2.setColor(new Color(15, 23, 42, 235));
                g2.fillRoundRect(badgeX, badgeY, labelWidth + 12, labelHeight + 4, 10, 10);
                g2.setColor(coupon && selected ? new Color(255, 214, 102) : Color.WHITE);
                g2.drawString(label, lx - labelWidth / 2, ly + fm.getAscent() / 2 - 2);
            }

            // Draw cities on top of the edges.
            for (int city = 1; city <= cityCount; city++) {
                java.awt.Point p = pointForCity(city, w, h);
                Color fill;
                if (city == 1) fill = new Color(34, 197, 94); // Start = green
                else if (city == cityCount) fill = new Color(239, 68, 68); // Destination = red
                else if (routeCities.contains(city)) fill = new Color(249, 115, 22); // Route stop = orange
                else fill = new Color(71, 85, 105);

                boolean currentCity = false;
                if (result.minCost != INF && !result.path.isEmpty()) {
                    int current = animatedFlights == 0 ? 1 : result.path.get(Math.min(animatedFlights - 1, result.path.size() - 1)).to;
                    currentCity = city == current;
                }
                if (currentCity) {
                    g2.setColor(Color.WHITE);
                    g2.setStroke(new BasicStroke(3f));
                    g2.drawOval(p.x - 25, p.y - 25, 50, 50);
                }
                g2.setColor(fill);
                g2.fillOval(p.x - 20, p.y - 20, 40, 40);
                g2.setColor(Color.WHITE);
                g2.setFont(new Font("SansSerif", Font.BOLD, 13));
                String text = String.valueOf(city);
                g2.drawString(text, p.x - g2.getFontMetrics().stringWidth(text) / 2, p.y + 5);
            }

            // Show the final total directly above the destination node so it is easy to find.
            if (result.minCost != INF && !result.path.isEmpty()) {
                java.awt.Point destination = pointForCity(cityCount, w, h);
                String totalLabel = "TOTAL COST: " + result.minCost;
                g2.setFont(new Font("SansSerif", Font.BOLD, 14));
                FontMetrics totalFm = g2.getFontMetrics();
                int totalWidth = totalFm.stringWidth(totalLabel);
                int badgeWidth = totalWidth + 22;
                int badgeHeight = totalFm.getHeight() + 10;
                int badgeX = Math.max(8, Math.min(w - badgeWidth - 8,
                        destination.x - badgeWidth / 2));
                int badgeY = Math.max(8, destination.y - 20 - badgeHeight - 12);
                g2.setColor(new Color(15, 23, 42, 245));
                g2.fillRoundRect(badgeX, badgeY, badgeWidth, badgeHeight, 14, 14);
                g2.setColor(new Color(134, 239, 172));
                g2.setStroke(new BasicStroke(1.5f));
                g2.drawRoundRect(badgeX, badgeY, badgeWidth, badgeHeight, 14, 14);
                g2.drawString(totalLabel, badgeX + (badgeWidth - totalWidth) / 2,
                        badgeY + (badgeHeight - totalFm.getHeight()) / 2 + totalFm.getAscent());
            }

            g2.setColor(Color.WHITE);
            g2.setFont(new Font("SansSerif", Font.PLAIN, 12));
            g2.drawString("Every edge shows its price   Gold label: original -> discounted price   Green: Start   Red: Destination", 18, h + 28);
            g2.dispose();
        }

        private void drawArrow(Graphics2D g2, int x1, int y1, int x2, int y2) {
            double dx = x2 - x1;
            double dy = y2 - y1;
            double length = Math.sqrt(dx * dx + dy * dy);
            if (length == 0) return;
            double ux = dx / length;
            double uy = dy / length;
            int startX = (int) (x1 + ux * 22);
            int startY = (int) (y1 + uy * 22);
            int endX = (int) (x2 - ux * 25);
            int endY = (int) (y2 - uy * 25);
            g2.drawLine(startX, startY, endX, endY);
            int arrowSize = 11;
            int ax1 = (int) (endX - arrowSize * ux + arrowSize * 0.55 * uy);
            int ay1 = (int) (endY - arrowSize * uy - arrowSize * 0.55 * ux);
            int ax2 = (int) (endX - arrowSize * ux - arrowSize * 0.55 * uy);
            int ay2 = (int) (endY - arrowSize * uy + arrowSize * 0.55 * ux);
            Polygon arrow = new Polygon();
            arrow.addPoint(endX, endY);
            arrow.addPoint(ax1, ay1);
            arrow.addPoint(ax2, ay2);
            g2.fillPolygon(arrow);
        }

        static void show(GraphData graph, Result result, int cityCount) {
            SwingUtilities.invokeLater(() -> {
                JFrame frame = new JFrame("Budget Traveller with Coupons — Flight Graph");
                GraphVisualizer visualizer = new GraphVisualizer(graph, result, cityCount);
                frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
                frame.setLayout(new BorderLayout());
                frame.add(visualizer, BorderLayout.CENTER);
                JButton replay = new JButton("Replay journey");
                replay.addActionListener(e -> {
                    visualizer.timer.stop();
                    visualizer.animatedFlights = 0;
                    visualizer.runningCost = 0;
                    visualizer.repaint();
                    if (result.minCost != INF && !result.path.isEmpty()) {
                        visualizer.status.setText("Journey starts at City 1 | Running cost: 0 | Flights used: 0 | Stops used: 0");
                        visualizer.timer.start();
                    }
                });
                JPanel controls = new JPanel(new FlowLayout(FlowLayout.CENTER));
                controls.add(replay);
                frame.add(controls, BorderLayout.NORTH);
                frame.pack();
                frame.setLocationRelativeTo(null);
                frame.setVisible(true);
            });
        }
    }

    public static void main(String[] args) {
        System.out.println("========================================");
        System.out.println("   BUDGET TRAVELLER WITH COUPONS");
        System.out.println("========================================");

        System.out.println("\nSelect an input option:");
        System.out.println("1. Enter flights manually");
        System.out.println("2. Load flights from a CSV file");
        System.out.println("3. Generate a random flight graph");

        int option;

        while (true) {
            option = readInt("Enter your choice (1-3): ", 1);

            if (option >= 1 && option <= 3) {
                break;
            }

            System.out.println("Please select 1, 2, or 3.");
        }

        GraphData graph;
        int N, K, C;

        try {
            if (option == 1) {
                N = readInt("Enter the number of cities (N): ", 1);
                int M = readInt("Enter the number of flights (M): ", 0);

                K = readInt(
                    "Enter maximum intermediate stops (K): ", 0
                );
                C = readInt("Enter available coupons (C): ", 0);

                graph = manualInput(N, M);

            } else if (option == 2) {
                K = readInt(
                    "Enter maximum intermediate stops (K): ", 0
                );
                C = readInt("Enter available coupons (C): ", 0);

                System.out.print("Enter CSV file path: ");
                sc.nextLine();
                String filename = sc.nextLine().trim();

                graph = csvInput(filename);
                N = graph.maxCity;

                System.out.println("CSV file loaded successfully.");
                System.out.println("Cities detected: " + N);
                System.out.println(
                    "Flights loaded: " + graph.flights.size()
                );

            } else {
                N = readInt("Enter the number of cities (N): ", 1);

                int minFlights = Math.max(0, N - 1);
                int M = readInt(
                    "Enter the number of flights (M, at least "
                    + minFlights + "): ", minFlights
                );

                K = readInt(
                    "Enter maximum intermediate stops (K): ", 0
                );
                C = readInt("Enter available coupons (C): ", 0);

                graph = generateGraph(N, M, K);

                System.out.println("\nRandom graph generated.");
                System.out.println("Cities: " + N);
                System.out.println(
                    "Flights: " + graph.flights.size()
                );
            }

            System.out.println("\nCalculating minimum travel cost...");

            Result result = findMinimumCost(graph, N, K, C);

            System.out.println("\n========== OUTPUT 1 ==========");

            if (result.minCost == INF) {
                System.out.println("Minimum cost: -1");
                System.out.println(
                    "No valid route from city 1 to city " + N + "."
                );
            } else {
                System.out.println(
                    "Minimum cost: " + result.minCost
                );

                System.out.print("Selected route: 1");

                for (Flight f : result.path) {
                    System.out.print(" -> " + f.to);
                }

                System.out.println();
                System.out.println(
                    "Flights used: " + result.flightsUsed
                );
                System.out.println(
                    "Intermediate stops used: "
                    + Math.max(0, result.flightsUsed - 1)
                );
                System.out.println(
                    "Coupons used: " + result.couponsUsedCount
                );

                System.out.println("\nSelected flight details:");

                for (int i = 0; i < result.path.size(); i++) {
                    Flight f = result.path.get(i);
                    boolean coupon = result.couponsUsed.get(i);

                    long paid = coupon ? f.price / 2 : f.price;

                    System.out.printf(
                        "%d -> %d | Original price: %d | "
                        + "Paid: %d%s%n",
                        f.from, f.to, f.price, paid,
                        coupon ? " | COUPON USED" : ""
                    );
                }
            }

            String outputFile = "flights_output.csv";

            writeOutputCSV(graph, result, outputFile);

            System.out.println("\n========== OUTPUT 2 ==========");
            System.out.println(
                "CSV file created: " + outputFile
            );
            System.out.println(
                "Selected flights are marked with 'x'."
            );
            System.out.println(
                "Coupon usage and discounted prices are included."
            );

            // Open the graph window after calculating the result and CSV output.
            GraphVisualizer.show(graph, result, N);

        } catch (IOException e) {
            System.out.println("File error: " + e.getMessage());
        } catch (IllegalStateException e) {
            System.out.println("Error: " + e.getMessage());
        } catch (OutOfMemoryError e) {
            System.out.println(
                "Error: Input is too large for available memory."
            );
        }
    }
}

