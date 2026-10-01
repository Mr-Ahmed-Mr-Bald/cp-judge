#include<bits/stdc++.h>
#define ll long long
#define endl "\n"
using namespace std;
template<class T>
void printff(vector<T>& v) {
  for (auto k : v) cout << k << " ";
  cout << endl;
}

void SOLVE() {
  ll n; cin >> n;
  ll answer = 0;
  for (ll l = 1, r = 1; (n / l); l = r + 1) {
    r = (n / (n / l));
    answer += ((r - l + 1) * (n / l));
  }
  cout << n * (n - 1) - (answer - n) * 2 << endl;
}
int main() {
  std::ios::sync_with_stdio(false);
  std::cin.tie(nullptr); std::cout.tie(nullptr);
  int tc = 1; cin >> tc;
  while(tc--) SOLVE();
  return 0;
}