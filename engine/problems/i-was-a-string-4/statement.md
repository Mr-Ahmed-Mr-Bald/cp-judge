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


## Hints

The validity of the sequence $p$ depends entirely on the availability of character frequencies as we process the sequence from left to right.

For each position $i$ ($1 \le i \le n$), the value $p_i$ denotes the number of times the character $s_i$ has appeared prior to index $i$. This imposes two immediate physical constraints. First, the value $p_i$ cannot exceed the number of elements preceding it, which means we must have $p_i \le i - 1$. Second, the total number of distinct characters used across the entire string cannot exceed the alphabet size $K = 26$.

To track the availability of characters efficiently, we can maintain an array $f$, where $f_x$ represents the number of distinct characters that have appeared exactly $x + 1$ times so far. Equivalently, $f_x$ is the count of characters currently waiting to match a future element whose value is $x + 1$.

When processing an element $p_i = x$, we transition our frequency states based on two cases. A value of $x = 0$ signifies the introduction of a new distinct character. We register this new character by incrementing its corresponding frequency bucket, $f_0 \leftarrow f_0 + 1$, and incrementing our global count of unique characters, $*distinct* \leftarrow *distinct* + 1$.

Alternatively, a value of $x > 0$ signifies that an existing character is being repeated. For this to be valid, there must be at least one character available that has already appeared exactly $x$ times. In our state tracking, this requires:
$$
f_{x-1} > 0.
$$
If this condition is met, we consume one such character from its old frequency bucket and promote it to the next bucket:
$$
f_{x-1} \leftarrow f_{x-1} - 1,
$$
$$
f_x \leftarrow f_x + 1.
$$
If $f_{x-1} = 0$, no such character exists, making the sequence immediately invalid.

At any point during the iteration, if the total number of unique characters exceeds the alphabet limit, meaning:
$$
*distinct* > 26,
$$
the sequence is determined to be invalid.

This suggests a simple online approach. We loop through the sequence from left to right while tracking the frequency distribution array $f$ and the total number of unique elements $*distinct*$. For each element $x$ at 0-indexed position $i$, we first check if $x > i$. If it is, the answer is immediately `NO`. Otherwise, we apply the transition rules. If at any point an invalid state is reached, we flag the sequence.

If the loop finishes without triggering any invalid conditions, the answer is `YES`; otherwise, it is `NO`.

We perform a single pass over the sequence of length $n$. Inside the loop, all frequency array modifications and condition checks are executed in $O(1)$ constant time. Therefore, the total time complexity is:
$$
O(n).
$$
The space complexity is determined by the frequency array $f$, which requires at most:
$$
O(n).
$$


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
