# MEDAA and the Jumping Stones

Meda is standing at stone $0$. There are $n + 1$ stones in a line, numbered $0, 1, 2, \dots, n$.

You are also given an array $a$ of length $n+1$, where $a_i$ is written on stone $i$.

From stone $i$, Meda can jump to any stone $j > i$ if $(j - i)$ divides $a_j$ (i.e. $a_j \bmod (j-i) = 0$).

Meda wants to reach stone $n$ starting from stone $0$. Find the minimum number of jumps required. If it is impossible, print $-1$.

## Input

The first line contains an integer $n$ $(1 \leq n \leq 10^5)$ --- the size of the array.

The second line contains $n+1$ integers $a_0, a_1, \dots, a_n$ $(1 \leq a_i \leq 10^5)$.


## Output

Print a single integer --- the minimum number of jumps to reach stone $n$, or $-1$ if it is impossible.


## Note

In the first testcase, the path is:
\begin{itemize}
    \item $0 \to 1$, since $8 \bmod (1 - 0) = 0$.
    \item $1 \to 3$, since $4 \bmod (3 - 1) = 0$.
    \item $3 \to 5$, since $2 \bmod (5 - 3) = 0$.
    \item $5 \to 6$, since $1 \bmod (6 - 5) = 0$.
\end{itemize}
It can be shown that this is the minimum number of steps to reach the $6$th stone.


## Example 1

**Input**

```
6
1 8 3 4 1 2 1
```

**Output**

```
4
```

## Example 2

**Input**

```
10
7 8 2 2 3 4 9 6 1 2 3
```

**Output**

```
3
```
