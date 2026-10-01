#include "bits/stdc++.h"
#pragma GCC optimize("O3,unroll-loops")
using namespace std;
typedef long long ll;
template<typename T, typename Op, typename OpInv>
struct FT {
  int n;
  vector<T> bit;
  Op op;
  OpInv inv_op;
  FT(int _n, Op _op, OpInv _inv_op) : n(_n), bit(n, T{}), op(_op), inv_op(_inv_op) {}
  FT(vector<T> const &a, Op _op, OpInv _inv_op) : FT(a.size(), _op, _inv_op) {
    for (int i = 0; i < n; i++) {
      bit[i] = op(bit[i], a[i]);
      int r = i | (i + 1);
      if (r < n) bit[r] = op(bit[r], bit[i]);
    }
  }
  T get(int r) const {
    T ret = T{};
    for (; r >= 0; r = (r & (r + 1)) - 1)
      ret = op(ret, bit[r]);
    return ret;
  }
  T get(int l, int r) const {
    if (r < l) return T{};
    return inv_op(get(r), get(l - 1));
  }
  void add(int idx, T delta) {
    for (; idx < n; idx = idx | (idx + 1))
      bit[idx] = op(bit[idx], delta);
  }
  void assign(int idx, T value) {
    T cur = get(idx, idx);
    T delta = inv_op(value, cur);
    add(idx, delta);
  }
  int lower_bound(T k) const {
    T prefix = T{};
    int idx = -1;
    int bit_mask = 1;
    while (bit_mask < n) bit_mask <<= 1;
    bit_mask >>= 1;
    for (; bit_mask > 0; bit_mask >>= 1) {
      int next_idx = idx + bit_mask;
      if (next_idx < n && op(prefix, bit[next_idx]) < k) {
        idx = next_idx;
        prefix = op(prefix, bit[idx]);
      }
    }
    return idx + 1;
  }
};
void solve() {
  int n, q; cin >> n >> q;
  string s; cin >> s;
  vector<pair<ll, int>> qq(q);
  for(int i = 0; i < q; i++) {
    ll x; cin >> x;
    qq[i] = make_pair(x, i);
  }
  set<int> cand, active;
  for(int i = 0; i < n; i++) {
    active.insert(i);
    if (i == n - 1 || s[i] > s[i + 1]) {
      cand.insert(i);
    }
  }
  auto merge = [](int x, int y) -> int {return x + y;};
  auto split = [](int x, int y) -> int {return x - y;};
  FT<int, decltype(merge), decltype(split)> tree(n, merge, split);
  for(int i = 0; i < n; i++) {
    tree.add(i, 1);
  }
  sort(qq.begin(), qq.end());
  vector<char> answer(q);
  ll l = 1, r = n;
  for(int i = 0, j = 0; ; i++) {
    while(j < q && qq[j].first <= r) {
      answer[qq[j].second] = s[tree.lower_bound(qq[j].first - l + 1)];
      ++j;
    }
    if (i == n - 1) {
      break;
    }
    l = r + 1;
    r += (n - i - 1);
    if (cand.empty()) {
      cand.insert(*active.rbegin());
    }
    int p = *cand.begin();
    cand.erase(cand.begin());
    active.erase(p); tree.add(p, -1);
    auto it = active.lower_bound(p);
    if (it != active.end() && it != active.begin()) {
      if (s[*prev(it)] > s[*it]) {
        cand.insert(*prev(it));
      }
    }
  }
  for(int i = 0; i < q; i++) {
    cout << answer[i];
  }
  cout << '\n';
}
int main() {
  ios::sync_with_stdio(0); cin.tie(0);
  int t; cin >> t; while(t--)
  solve();
}