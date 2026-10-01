# MEDAA and Mohamed Hazem

Meda and Mohamed Hazem are competitive programmers who love exploring number theory puzzles. One day, Meda challanged Mohamed Hazem with a problem:

Let $\tau(n)$ be the number of positive divisors of $n$.

Given a positive integer $n$, find the number of ordered pairs $(a, b)$ such that $1 \leq a, b \leq n$ satisfing the following inequality

$$\tau(a) + \tau(b) < \tau(\gcd(a, b)) + \tau(lcm(a,b))$$

**Note that** $(2, 3)$ and $(3, 2)$ are not considered the same.

## Input

Each test contains multiple test cases. The first line of input contains a single integer $t$ $(1 \leq t \leq 10^4)$ --- the number of test cases. The description of the test cases follows.

The only line of each test case contains a single integer $n$  $(1 \leq n \leq 10^6)$.


## Output

For each test case, output a single integer, the number of pairs satisfying the given inequality.


## Note

In the second test case, it can be shown that only the pairs $(2, 3)$ and $(3, 2)$ satisfy the inequality.

$\tau(2) = 2$, $\tau(3) = 2$, $\tau(\gcd(2,3))= \tau(1) = 1$, and $\tau(lcm(2,3)) = \tau(6) = 4$

Obviously, $2 + 2 < 1 + 4$ is true.


## Example 1

**Input**

```
3
2
3
4
```

**Output**

```
0
2
4
```
