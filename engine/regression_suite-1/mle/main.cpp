#include "bits/stdc++.h"
using namespace std;
typedef long long ll;
int a[1000000000];
void solve() {
  int n = 1;
  while(n < 1e9) n *= 2;
  vector<int> a(n);
  ll x, y; cin >> x >> y;
  cout << x + y;
}
int main() {
  ios::sync_with_stdio(0); cin.tie(0);
  solve();
}