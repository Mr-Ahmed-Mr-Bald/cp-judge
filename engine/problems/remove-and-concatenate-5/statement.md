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
