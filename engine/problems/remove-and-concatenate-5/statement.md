# Remove and Concatenate

You are given a string $s$ of length $n$ consisting of lowercase Latin letters.
Let $t = s$. Then, we perform the following procedure exactly $n - 1$ times:

\begin{enumerate}
  \item Remove a character from $s$ such that the resulting string is
        lexicographically minimal among all possible single-character removals. For example, if $s = dabc$, we remove the first character to obtain $abc$. Note that removing any other character will result in a lexicographically larger string.
  \item Append the current $s$ to $t$.
\end{enumerate}

You are given $q$ queries. Each query gives an integer $p$; report the
character at $1$-indexed position $p$ in the final string $t$.

## Input

The first line contains a single integer $t$ ($1 \le t \le 10^4$) --- the
number of test cases.

For each test case:
\begin{itemize}
  \item The first line contains two integers $n$ and $q$
        ($1 \le n \le 2 \times 10^5$, $1 \le q \le 2 \times 10^5$) --- the
        length of the string and the number of queries.
  \item The second line contains the string $s$ of length $n$ consisting of
        lowercase Latin letters.
  \item The third line contains $q$ integers $p_1, p_2, \ldots, p_q$
        ($1 \le p_i \le \frac{n(n+1)}{2}$) --- the query positions.
\end{itemize}

It is guaranteed that the sum of $n$ over all test cases does not exceed
$2 \times 10^5$, and the sum of $q$ over all test cases does not exceed
$2 \times 10^5$.


## Output

For each test case, print a single line containing $q$ characters (without
spaces), where the $i$-th character is the answer to the $i$-th query.


## Hints

The final string $t$ is the concatenation $t = s_1 s_2 \cdots s_n$, where $s_i$
has length $n - i + 1$. Given a query $p$, we sweep through segments to identify which one it belongs to, and output its value. We do this offline after sorting the queries.

The lexicographically minimal result of a single removal is obtained by removing
the leftmost index $i$ such that $s[i] > s[i+1]$. If no such index exists,
the string is non-decreasing and we remove the last character. To see why,
suppose we remove at some position $i$ where $s[i] \leq s[i+1]$, while $j < i$
is the first descent. The two resulting strings first differ at position $j$:
removing $j$ places $s[j+1]$ there, while removing $i$ leaves $s[j]$. Since
$s[j] > s[j+1]$, removing $j$ produces a strictly smaller string.

To apply this greedily across all $n - 1$ steps efficiently, we maintain a
sorted set $*cand*$ of original indices that are currently valid descent
starts, alongside a sorted set $*active*$ of all remaining original indices.
After removing the leftmost candidate $p$, we check whether the predecessor of
$p$ in $*active*$ now forms a descent with the successor of $p$, and
insert it into $*cand*$ if so. No stale entries can accumulate: since we
always remove the leftmost candidate, any index to the left of $p$ that was ever
inserted into $*cand*$ would itself have been the leftmost candidate and
removed before $p$. By the time $p$ is processed, all active indices to its left
are already non-decreasing, so no outdated descent entries for them can exist.

To answer queries efficiently, we maintain a Fenwick tree over the $n$ original
positions, each initialized to $1$. The prefix sum up to position $i$ gives the
count of still-active characters among $s[0..i]$. This supports an
order-statistic query: given a rank $r$, find the $r$-th active original index
in $O(\log n)$ via a binary search on the Fenwick tree. We sort all queries by
their position $p$ and sweep through segments $i = 1, 2, \ldots, n$. For each
segment with window $[L_i, R_i]$, we answer every query $p$ in that window by
computing $r = p - L_i + 1$ and looking up the $r$-th active index in the
Fenwick tree, then reading off $s[that index]$. After answering all
queries for segment $i$, we remove the next greedy character: pop the minimum of
$*cand*$ (or the last active element if $*cand*$ is empty),
decrement the Fenwick tree at that index, and update $*cand*$.

Each of the $n$ removals costs $O(\log n)$ for the Fenwick update and $O(\log n)$
for the set operations. Each of the $q$ queries costs $O(\log n)$ for the Fenwick
order-statistic. Sorting the queries costs $O(q \log q)$. The total time
complexity per test case is therefore:
$$
O((n + q) \log n).
$$


## Note

In the second test case, the final string $t$ that we obtain is $$dabcabcaba$$ As a result, the third, seventh, and ninth characters are $b$, $c$, and $b$ respectively.


## Example 1

**Input**

```
2
1 1
b
1
4 3
dabc
3 7 9
```

**Output**

```
b
bcb
```
