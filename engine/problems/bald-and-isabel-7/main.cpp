#include "bits/stdc++.h"
using namespace std;
typedef long long ll;
const int MOD = 1000000007, MAX_N = 3e5 + 9;
int main() {
  ios::sync_with_stdio(0); cin.tie(0);
  int t; cin >> t;
  while(t--) {
    int n, k, q; cin >> n >> k >> q;
    vector<int> has(n, 0);
    for(int i = 0; i < k; i++) {
      int u; cin >> u; --u;
      has[u] = 1;
    }
    vector<vector<int>> adj(n);
    for(int i = 0; i < n - 1; i++) {
      int u, v; cin >> u >> v;
      --u; --v;
      adj[u].push_back(v);
      adj[v].push_back(u);
    }
    
    vector<int> par, dist;
    auto farthest = [&](int s, int n) -> int {
      static const int INF = MAX_N;
      dist.assign(n, INF); dist[s] = has[s];
      par.assign(n, -1);
      vector<bool> vis(n);
      queue<int> q; q.push(s);
      vis[s] = 1; int last = s;
      while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v: adj[u]) {
          if (vis[v]) continue;
          dist[v] = dist[u] + has[v];
          if (dist[v] >= dist[last]) last = v;
          q.push(v); vis[v] = 1;
          par[v] = u;
        }
      }
      return last;
    };
    
    int x = farthest(0, n);
    int y = farthest(x, n);

    int all = dist[y], now = 0;
    int current = y, prev = -1;

    vector<bool> answer(n);
    auto dfs = [&](auto &&self, int u, int p, int tokens) -> void {
      tokens += has[u];
      if (tokens == all) answer[u] = 1;
      for(int v : adj[u]) if (v != p) {
        self(self, v, u, tokens);
      }
    };

    while(current != -1) {
      now += has[current];
      int mx = max(now, all - now + has[current]);
      if (mx == all) answer[current] = 1;
      for(int v : adj[current]) if (v != prev && v != par[current]) dfs(dfs, v, current, mx);
      prev = current;
      current = par[current];
    }

    while(q--) {
      int u; cin >> u; --u;
      cout << (answer[u] ? "JA" : "NEIN") << '\n';
    }

  }
}
