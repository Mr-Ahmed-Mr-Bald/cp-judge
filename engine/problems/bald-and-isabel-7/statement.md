# Bald and Isabel

It was a hot summer day when Bald stumbled upon an interesting problem in Graph Theory. After many failed attempts to solve it, he decided to seek help from the only person he knows at his university who teaches the subject, Dr. Isabel.

You are given a tree* with $n$ vertices. Among them, there are $k$ special vertices $a_1, a_2, a_3, \dots ,a_k$, each contains a **single** token. All other vertices do **not** contain any tokens. Let $X$ denote the maximum number of tokens that can be collected by taking any simple* path in the tree. 

You will be given $q$ queries. Each query is described by a single vertex $u_i$. To answer the $i$-th query, you need to decide if you can collect $X$ tokens by taking any path that **starts** at $u_i$

Now Dr. Isabel was a little bit busy playing around with matrices. As one of her best students, you decided to take on this task.


---



* A tree is a connected graph with no cycles.

* A simple path is a path in which no vertex is repeated.

## Input

Each test contains multiple test cases. The first line of each test contains an integer $t$ $(1 \leq t \leq 10^5)$ --- the number of test cases.

The first line of each test case contains three integers $n, k$, and $q$ $(1 \leq n \leq 3 \cdot 10^5, 0 \leq k \leq n, 1 \leq q \leq 3 \cdot 10^5)$ --- the number of vertices, number of special vertices, and number of queries, respectively.

The second line of each test case contains $k$ integers $a_1, a_2, a_3, \dots ,a_k$ --- denoting the indices of the special vertices.

Then follow $n - 1$ lines that describe the tree. Each of them contains two integers $u_i$ and $v_i$ $(1 \leq u_i, v_i \leq n)$ --- indices of vertices connected by the $i$-th edge.

The last line of each test case contains $q$ integers $u_1, u_2, u_3, \cdots, u_q$ --- the indices of the vertices you must find the answer for.


## Output

For each test case, output the answer for each of the $q$ queries on a single line. For the $i$-th query, if you can collect $X$ tokens by taking any path **starting** at $u_i$, output `JA`. Otherwise, output `NEIN`. 

You can output the answer in any case (upper or lower). For example, the strings `JA`, `Ja`, `jA`, and `ja` will be recognized as positive responses.


## Note

In the second test case, the tree looks as follows:





You can see that the maximum number of tokens that can be collected is $X = 5$. Among the vertices given in the queries, you can only start at vertices $6$ or $10$, and still collect $X$ tokens.

- Special nodes are in blue


## Example 1

**Input**

```
2
5 5 3
1 2 3 4 5
1 2
2 3
3 4
4 5
1 3 4
13 8 6
2 4 5 6 10 13 11 12
1 2
2 3
3 4
4 5
5 6
6 7
2 10
3 8
8 9
4 11
4 12
4 13
2 5 6 9 10 13
```

**Output**

```
JA
NEIN
NEIN
NEIN
NEIN
JA
NEIN
JA
NEIN
```
