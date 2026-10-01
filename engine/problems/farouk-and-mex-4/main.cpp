#include <bits/stdc++.h>

using namespace std;
#define endl '\n'
typedef long long ll;

void solve() {
  int n;
  cin >> n;
  vector<int> a(n);
  for (int i = 0; i < n; i++)
    cin >> a[i];

  vector<int> pos(n);
  for (int i = 0; i < n; i++)
    pos[a[i]] = i;
  int l = pos[0], r = pos[0];
  ll ans = n;
  for (int x = 0; x < n - 1; x++) {
    l = min(l, pos[x]), r = max(r, pos[x]);
    if (pos[x + 1] < l)
      ans += 1ll * (x + 1) * (l - pos[x + 1]) * (n - r);
    else if (r < pos[x + 1])
      ans += 1ll * (x + 1) * (pos[x + 1] - r) * (l + 1);
  }
  cout << ans << endl;
}
int main() {
  ios_base::sync_with_stdio(0);
  cin.tie(0);

  int t;
  cin >> t;
  while (t--)
    solve();

  return 0;
}
