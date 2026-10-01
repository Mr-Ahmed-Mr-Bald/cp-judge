# MEDAA and Totients

Meda was studying his favorite subject --- **Number theory**.  

He came across Euler's Totient function, which for $n = p_1^{\alpha_1} \cdot p_2^{\alpha_2} \cdot \ldots \cdot p_k^{\alpha_k},$  is defined as  
$$\varphi(n) = n \cdot \left(1 - \frac{1}{p_1}\right) \cdot \left(1 - \frac{1}{p_2}\right) \cdots \left(1 - \frac{1}{p_k}\right).$$
where $p_1, p_2, \ldots, p_k$ are the distinct prime factors of $n$.

Although Meda loves number theory, he did not pay attention while studying. So, he defined Euler's Totient function as follows  
$$
f(n) = \left(1 - \frac{1}{p_1}\right) \cdot \left(1 - \frac{1}{p_2}\right) \cdots \left(1 - \frac{1}{p_k}\right),
$$  

Meda was then given an array of integers $a_1, a_2, \ldots, a_n$.  
He computes $f(a_i)$ for each $1 \leq i \leq n$.  

Your task is to determine how many **distinct rational numbers** appear among Meda's results.

## Input

The first line of each test case contains a single integer $n$ $(1 \leq n \leq 2 \cdot 10^5)$.  

The second line contains $n$ integers $a_1, a_2, \ldots, a_n$ $(2 \leq a_i \leq 10^6)$.


## Output

A single integer representing the number of distinct rational numbers among $ f(a_1), f(a_2), \ldots, f(a_n) $.


## Note

In the first testcase, Let's compute $f(a)$ for each element.  
\begin{itemize}
    \item For $a_1 = 2$: the prime divisors are $\{2\}$, so  
    $f(2) = 1 - \tfrac{1}{2} = \tfrac{1}{2}.$  

    \item For $a_2 = 3$: the prime divisors are $\{3\}$, so  
    $f(3) = 1 - \tfrac{1}{3} = \tfrac{2}{3}.$  

    \item For $a_3 = 4$: the prime divisors are $\{2\}$ (since $4 = 2^2$), so  
    $f(4) = 1 - \tfrac{1}{2} = \tfrac{1}{2}.$  
\end{itemize}
It is clear that the number of distinct values is $2$.


## Example 1

**Input**

```
3
2 3 4
```

**Output**

```
2
```

## Example 2

**Input**

```
6
3 9 93842 123 2 1024
```

**Output**

```
4
```
