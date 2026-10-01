# MEDAA, Farouk, and Bald

The three authors of this contest were playing a game. They were given a large positive integer $n$, represented as a binary string. Together, they need to choose a positive integer $x$ such that $ \lfloor \log_2 x \rfloor \;\le\; \lfloor \log_2 n \rfloor,$ that is, the binary representation of $x$ contains at most as many bits as the binary representation of $n$.  

However, each of them wants to apply a different operation on $n$ using $x$:  
\begin{itemize}
  \item Meda wants to compute $n + x$.  
  \item Farouk wants to compute $n \mid x$, where $\mid$ denotes the bitwise OR operation\footnote{For an explanation of the bitwise OR operation, see the notes.}.  
  \item Bald wants to compute $n \oplus x$, where $\oplus$ denotes the bitwise XOR operation\footnote{For an explanation of the bitwise XOR operation, see the notes.}.  
\end{itemize}
To avoid any conflict, they agreed to choose $x$ such that all three expressions give the same result. Your task is to determine the number of positive integers $x$ that satisfy this condition. Since this number can be large, output it modulo $10^9 + 7$.

## Input

The first line contains a single integer $m$ $(1 \leq m \leq 10^6)$ --- the length of the binary string.  

The second line contains the integer $n$, given as a binary string of length $m$. It is guaranteed that the string has no leading zeros.


## Output

Print a single integer --- the number of positive integers $x$ satisfying the conditions, modulo $10^{9}+7$.


## Note

Bitwise OR is a binary operation which is performed on each bit of two integers independently. It outputs 1 if and only if either of the input bits is 1, that is, $0 \mid 0 = 0, 0 \mid 1 = 1, 1 \mid 0 = 1, 1 \mid 1 = 1$. For example, $101_2 \mid 011_2 = 111_2$.

Bitwise XOR is a binary operation which is performed on each bit of two integers independently. It outputs 1 if and only if the input bits are different, that is, $0 \oplus 0 = 0, 0 \oplus 1 = 1, 1 \oplus 0 = 1, 1 \oplus 1 = 0$. For example, $101_2 \oplus 011_2 = 110_2$.


## Example 1

**Input**

```
5
11010
```

**Output**

```
3
```
