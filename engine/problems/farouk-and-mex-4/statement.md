# Farouk and MEX Sum

Farouk was bored, and so to relieve his boredom, he decided to play a game with a permutation. He wrote down a permutation $p_1, p_2, \cdots, p_n$ of the integers $0, 1, 2, \cdots, n-1$, and he wanted to find the sum of the **MEX** (Minimum Excluded Value\footnote{The **MEX** of a set of integers is the first nonnegative integer not in the set. For example, $**MEX**(\{ 2, 0, 1, 5 \}) = 3.$}) over all subarrays. More formally, find
$$
  \sum_{1 \le l \le r \le n} **MEX**(\{ p_l, p_{l+1}, \cdots, p_{r-1}, p_r \}).
$$
However, he found it rather tedious to calculate the sum of the **MEX** over all subarrays himself and so he tasked you with helping him.

## Input

Each test contains multiple test cases. The first line contains a single integer $t$ ($1 \le t \le 1000$) -- the number of test cases. 

The first line of each test case contains a single integer $n$ ($1 \le n \le 2 \cdot 10^5$) -- the length of the permutation.

The next line contains $n$ integers $p_1, p_2, ..., p_n$ ($0 \le p_i \le n-1$) -- the elements of the permutation.

It is guaranteed that the the sum of $n$ over all test cases does not exceed $2 \cdot 10^5$.


## Output

For each test case, output a single integer -- the sum of the **MEX** over all subarrays of the permutation.


## Note

In the first test case, the **MEX** of $[0]$ and $[2, 0]$ is 1, the **MEX** of the entire permutation is 3, and the **MEX** of all other subarrays is 0. Thus the sum of **MEX** over all subarrays is $1 + 1 + 3 = 5$.


## Example 1

**Input**

```
2
3
1 2 0
5
0 3 2 4 1
```

**Output**

```
5
9
```
