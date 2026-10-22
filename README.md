# Best bang for the buck

**[Read the writeup](https://gernreich.github.io/bang-for-the-buck/)**: the
method explained, with a live demo where you can change how uneven the folder
sizes are or paste your own `du` output.

**Whose idea this is.** The method is the author's own: sort the folders on a
full drive largest first, take the running total, scale both axes to 0–1 with
the y-axis turned over, and take the point nearest the origin as the cutoff.
`bang_for_the_buck.py` is a fresh implementation of it.

## The method

With sizes s₁ ≥ s₂ ≥ … ≥ s_N, total T and running total S_k:

```
x_k = k / N          share of the folders cleaned up
y_k = 1 - S_k / T    share of the space still left
d_k = sqrt(x_k² + y_k²)
```

The curve runs from (0, 1) to (1, 0). The origin, no effort and no space left,
is the ideal. The k with the smallest d_k is the cutoff: clean up the first k
folders and stop. If every folder is the same size the answer is half of them,
and the more uneven the sizes, the earlier the cutoff.

## Running it

Python 3, no other dependencies:

```
python3 bang_for_the_buck.py /path/to/full/drive        # folders and files directly in it
python3 bang_for_the_buck.py -f /path/to/full/drive     # every file under it instead
python3 bang_for_the_buck.py --all /path/to/full/drive  # the whole list, cutoff marked
python3 bang_for_the_buck.py --csv /path/to/full/drive  # the curve as CSV
```

It measures on-disk size, does not follow symbolic links, and skips anything it
cannot read.

`index.html` is the writeup, written by hand and published by GitHub Pages.
Its demo uses the same cutoff rule as the script.
