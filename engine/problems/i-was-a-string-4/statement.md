# I Was a String

You are given an integer sequence $p_1, p_2, \dots, p_n$.

A sequence $p$ can be constructed from a string $s$ of length $n$ consisting only of lowercase Latin letters (a--z) as follows:

For every position $i$ ($1 \le i \le n$), let $s_i$ be the character at position $i$. Then define

$$
p_i = |\{ j : 1 \le j < i,\ s_j = s_i \}|.
$$

In other words, $p_i$ is the number of previous occurrences of the character $s_i$ before position $i$.

For example, if

$$
s = `abacaba`,
$$

then the resulting sequence is

$$
[0, 0, 1, 0, 2, 1, 3].
$$

Determine whether the given sequence $p$ is valid, i.e. whether there exists at least one string $s$ consisting only of lowercase Latin letters that produces it.

## Input

The first line contains a single integer $t$ ($1 \le t \le 10^4$) --- the number of test cases.

Each test case consists of two lines.

The first line of each test case contains a single integer $n$ ($1 \le n \le 2 \times 10^5$) --- the length of the sequence.

The second line contains $n$ integers $p_1, p_2, \dots, p_n$ ($0 \le p_i \le 10^9$).

It is guaranteed that the sum of all $n$ over all test cases does not exceed $2 \times 10^5$.


## Output

For each query across all test cases, print `YES` if the sequence is valid, and `NO` otherwise.

You can output each letter in any case (upper or lower). For example, `YeS`, `yeS`, `yes`, and `YES` will all be accepted as positive answers.




## Note

In the first test case, the string `abacaba` is valid.

In the second test case, the string `xxyxy` is valid.

In the third test case, it can be proven that no string can construct the given sequence.


## Example 1

**Input**

```
3
7
0 0 1 0 2 1 3
5
0 1 0 2 1
6
0 2 0 1 0 0
```

**Output**

```
YES
YES
NO
```
