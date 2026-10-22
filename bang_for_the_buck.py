#!/usr/bin/env python3
"""Best bang for the buck: which subdirectories to clean up first.

Give it a directory. It measures every entry directly inside it, sorts them
largest first and finds the point where cleaning up one more stops paying
off, then prints the entries worth acting on.

The cutoff is found like this:

  1. Sort the sizes largest first and take the running total.
  2. Let x = k / N, the share of the N entries handled so far, and
     y = 1 - (running total after k) / (grand total), the share of the
     space still left. The curve runs from (0, 1) to (1, 0) and bows
     towards the origin, more deeply the more uneven the sizes are.
  3. Measure each point's distance to the origin, sqrt(x^2 + y^2).
     The nearest point is the knee: few entries, little space left.

Usage:
  python3 bang_for_the_buck.py PATH            # subdirectories and files in PATH
  python3 bang_for_the_buck.py -f PATH         # every file under PATH instead
  python3 bang_for_the_buck.py --csv PATH      # the whole curve as CSV
"""

import argparse
import csv
import os
import sys
from math import sqrt


def disk_bytes(st):
    """Bytes the file occupies on disk, falling back to its length."""
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def tree_size(path):
    """Total on-disk bytes under path, not following symlinks."""
    total = 0
    stack = [path]
    while stack:
        here = stack.pop()
        try:
            with os.scandir(here) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    total += disk_bytes(st)
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
        except OSError:
            pass
    return total


def top_level_sizes(root):
    """(bytes, name) for each entry directly inside root."""
    sizes = []
    with os.scandir(root) as it:
        for entry in it:
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if entry.is_dir(follow_symlinks=False):
                sizes.append((tree_size(entry.path), entry.name + "/"))
            else:
                sizes.append((disk_bytes(st), entry.name))
    return sizes


def file_sizes(root):
    """(bytes, relative path) for every file under root."""
    sizes = []
    for here, dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(here, name)
            try:
                st = os.lstat(path)
            except OSError:
                continue
            sizes.append((disk_bytes(st), os.path.relpath(path, root)))
    return sizes


def knee(sizes):
    """Return (k, curve) for sizes sorted largest first.

    curve[k] = (x, y, distance) for k = 0..N; k is the index of the point
    nearest the origin, so the first k entries are the ones worth acting on.
    """
    n = len(sizes)
    total = sum(sizes)
    curve = []
    running = 0
    for k in range(n + 1):
        if k:
            running += sizes[k - 1]
        x = k / n if n else 0.0
        y = 1 - running / total if total else 0.0
        curve.append((x, y, sqrt(x * x + y * y)))
    # On a tie take the later point, so a lone entry is still acted on.
    best = min(range(len(curve)), key=lambda k: (curve[k][2], -k))
    return best, curve


def human(n):
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find the entries to clean up for the most space for the least effort.")
    parser.add_argument("path", help="a directory or mount point")
    parser.add_argument("-f", "--files", action="store_true",
                        help="rank every file under PATH instead of the entries directly in it")
    parser.add_argument("--csv", action="store_true",
                        help="print the whole curve as CSV instead of the report")
    parser.add_argument("--all", action="store_true",
                        help="list every entry, marking the cutoff, not just the ones to act on")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.path):
        parser.error(f"not a directory: {args.path}")

    rows = file_sizes(args.path) if args.files else top_level_sizes(args.path)
    rows = [r for r in rows if r[0] > 0]
    rows.sort(key=lambda r: (-r[0], r[1]))
    if not rows:
        print("Nothing with any size in", args.path)
        return 0

    sizes = [r[0] for r in rows]
    k, curve = knee(sizes)
    total = sum(sizes)

    if args.csv:
        out = csv.writer(sys.stdout)
        out.writerow(["k", "name", "bytes", "x", "y", "distance", "knee"])
        out.writerow([0, "", 0, *(f"{v:.6f}" for v in curve[0]), int(k == 0)])
        for i, (size, name) in enumerate(rows, 1):
            out.writerow([i, name, size, *(f"{v:.6f}" for v in curve[i]), int(k == i)])
        return 0

    freed = sum(sizes[:k])
    shown = rows if args.all else rows[:k]
    running = 0
    print(f"{'#':>4}  {'size':>8}  {'running':>7}  name")
    for i, (size, name) in enumerate(shown, 1):
        running += size
        print(f"{i:>4}  {human(size):>8}  {100 * running / total:6.1f}%  {name}")
        if args.all and i == k:
            print("      ---- knee: the entries above are the best bang for the buck ----")
    print()
    print(f"Act on {k} of {len(rows)} entries ({100 * k / len(rows):.1f}%) "
          f"to reach {human(freed)} of {human(total)} ({100 * freed / total:.1f}%).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
