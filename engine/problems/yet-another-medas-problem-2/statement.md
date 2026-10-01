# MEDAA and subsequences

Meda loves solving number theory puzzles, I think you already know. So, he gives you this problem to solve it with him

He has an integer $n$ and an array $a$ of size $n$. He wants to know if there exists a non-empty subsequence of $a$ such that the sum of its elements is divisible by $n$.  

Given an array $a = [a_1, a_2, \dots, a_n]$, a *subsequence* of $a$ is any sequence of the form  

$$[a_{i_1}, a_{i_2}, \dots, a_{i_k}]$$  

where $1 \leq i_1 < i_2 < \cdots < i_k \leq n$ and $k \geq 1$.  

In other words, a subsequence is obtained by deleting zero or more elements from $a$ without changing the order of the remaining elements.

## Input

The first line of input contains a single integer $t$ $(1 \leq n \leq 10^5)$ --- the size of the array.

The second line contains $n$ integers $a_1, a_2, \dots, a_n$ satisfying $1 \leq a_i \leq 10^5$ for all $1 \leq i \leq n$


## Output

Print `YES` if such a subsequence exists, otherwise print `NO`.


## Note

In the first testcase, you can take the the first or the last element $1 + 2 \equiv 0 \pmod{3}$.
You can also take the second and the last element $4 + 2 \equiv 0 \pmod{3}$

In the second testcase, you can easily take every element in the array.


## Example 1

**Input**

```
3
1 4 2
```

**Output**

```
YES
```

## Example 2

**Input**

```
5
1 2 3 4 5
```

**Output**

```
YES
```
