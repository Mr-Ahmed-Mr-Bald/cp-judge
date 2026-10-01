# Easy Queries

You are given a grid of $2$ rows and $n$ columns. The cell located at the intersection of the $i$-th row ($1 \le i \le 2$) and the $j$-th column ($1 \le j \le n$) contains an integer value $a_{i, j}$. 

You can move from one cell to another if they share a common side (up, down, left, or right) and both cells are currently **active**. Initially, all cells are inactive.

You must answer $q$ queries. Each query provides the coordinates of two cells $(r_1, c_1)$ and $(r_2, c_2)$, along with two integers $l$ and $r$. For each query, a cell $(i, j)$ is considered **active** if and only if its value satisfies $l \le a_{i, j} \le r$. Your task is to determine if there exists a path between $(r_1, c_1)$ and $(r_2, c_2)$ using only active cells. If **either** the starting cell or the destination cell is inactive, the answer is `NO`.

## Input

The first line of the input contains a single integer $t$ ($1 \le t \le 10^4$) --- the number of test cases. The description of the test cases follows.

The first line of each test case contains two integers $n$ and $q$ ($1 \le n, q \le 1 \times 10^5$) --- the number of columns and the number of queries, respectively.

Each of the next two lines of the test case contains $n$ integers. The $j$-th integer in the $i$-th line represents $a_{i, j}$ ($1 \le a_{i, j} \le 10^9$).

Each of the following $q$ lines contains six integers $r_1, c_1, r_2, c_2, l$, and $r$ ($1 \le r_1, r_2 \le 2$; $1 \le c_1, c_2 \le n$; $1 \le l \le r \le 10^9$) --- the row and column of the starting cell, the row and column of the destination cell, and the range of values $[l, r]$ defining an active cell.

It is guaranteed that the sum of $n$ and the sum of $q$ over all test cases do not exceed $1 \times 10^5$.


## Output

For each query across all test cases, output `YES` if a path exists between the two cells using only active cells, and `NO` otherwise.

You can output each letter in any case (upper or lower). For example, `YeS`, `yeS`, `yes`, and `YES` will all be accepted as positive answers.


## Hints

The key observation is that the grid has only two rows. Therefore, for any fixed set of active cells, moving from one column to the next is possible only through the horizontal adjacency between two consecutive columns in the same row.

Consider the boundary between columns $j$ and $j+1$. A path can cross this boundary if and only if at least one of the following two pairs of adjacent cells is active:
$$
(a_{1,j},a_{1,j+1}),
$$
$$
(a_{2,j},a_{2,j+1}).
$$
Here, by a pair we simply mean the two cells in the same row and in two consecutive columns. For a fixed query interval $[l,r]$, such a pair $(x,y)$ is active exactly when
$$
l \le x \le r
$$
and
$$
l \le y \le r.
$$
This is equivalent to
$$
\min(x,y)\ge l
$$
and
$$
\max(x,y)\le r.
$$

For each boundary $j$, each row contributes one candidate pair of adjacent cells. Let
$$
u=\min(x,y),
$$
$$
v=\max(x,y).
$$
Then this pair becomes available for every query with lower bound $l\le u$, and once it is available, it allows crossing the boundary whenever $r\ge v$.

So, for a fixed value of $l$, each boundary $j$ has an associated value
$$
best_j=\min v,
$$
taken over the two row-pairs whose value $u$ satisfies $u\ge l$. If no such pair exists, then $best_j=\infty$. The boundary is passable if and only if
$$
best_j\le r.
$$

This condition is both necessary and sufficient. It is necessary because every path from one column to another must cross each intermediate boundary, so each such boundary has to be passable. It is sufficient because if every intermediate boundary is passable, then for each boundary we can choose one active row that crosses it, and by concatenating these crossings we obtain a valid path between the two queried cells. Since the grid has only two rows, there is no additional obstruction beyond the passability of every boundary.

This suggests an offline approach. Sort all row-pairs by $u$ in decreasing order, and sort the queries by $l$ in decreasing order as well. While processing the queries in this order, activate all row-pairs with $u\ge l$. For each boundary $j$, maintain the minimum value of $v$ among all activated pairs. This can be done with a segment tree by performing point updates of the form
$$
best_j \leftarrow \min(best_j,v).
$$
The segment tree is then used to answer range maximum queries on the boundaries between the two columns of the query.

For a query $(r_1,c_1,r_2,c_2,l,r)$, first check whether both endpoint cells are active:
$$
l \le a_{r_1,c_1}\le r,
$$
$$
l \le a_{r_2,c_2}\le r.
$$
If one of them is inactive, the answer is immediately `NO`.

Otherwise, let
$$
L=\min(c_1,c_2),
$$
$$
R=\max(c_1,c_2).
$$
Any path from one cell to the other must cross every boundary between columns $L$ and $R$. Consequently, the path exists if and only if every boundary in the interval $[L,R-1]$ is passable, that is,
$$
\max_{j=L}^{R-1} best_j \le r.
$$
If this condition holds, the answer is `YES`; otherwise, it is `NO`.


There are $2(n-1)$ row-pairs in total. Each pair causes one segment tree update, and each query requires one range maximum query. Therefore, the total complexity is
$$
O((n+q)\log n).
$$


## Note

In the given test case, we have three queries:

\begin{itemize}
    \item In the first query, we are given $(r_1, c_1) = (1, 1), (r_1, c_2) = (1, 3)$ and $(l, r) = (1, 10)$. Obviously, this range makes all cells active, and so there is a path between any two cells. Thus, the answer is `YES`.
    \item In the third test case, we are given $(r_1, c_1) = (1, 2), (r_1, c_2) = (2, 3)$ and $(l, r) = (2, 5)$. Therefore, a valid path is $$(1, 2) \rightarrow (1, 3) \rightarrow (2, 3).$$
\end{itemize}


## Example 1

**Input**

```
1
3 3
3 4 2
1 7 5
1 1 1 3 1 10
1 1 1 2 1 2
1 2 2 3 2 5
```

**Output**

```
YES
NO
YES
```
