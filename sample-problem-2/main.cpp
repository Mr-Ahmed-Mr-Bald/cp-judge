#include "bits/stdc++.h"
using namespace std;
typedef long long ll;
void solve() {
  int n; cin >> n;
  set<int> s;
  bool answer = false;
  for(int i = 0; i < n; i++) {
    int x; cin >> x;
    if (s.find(x) == s.end()) {
      s.insert(x);
    } else {
      answer = true;
    }
  }
  cout << (answer ? "YES" : "NO") << '\n';
}
int main() {
  ios::sync_with_stdio(0); cin.tie(0);
  int t; cin >> t; while(t--)
  solve();
}