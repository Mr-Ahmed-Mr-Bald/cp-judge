#include "bits/stdc++.h"
#pragma GCC optimize("O3,unroll-loops")
using namespace std;
typedef long long ll;
const int K = 26;
void solve() {
	int n; cin >> n;
	bool bad = false;
	int distinct = 0;
	vector<int> f(n);
	for(int i = 0; i < n; i++) {
		int x; cin >> x;
		if (x > i) {
			bad = true;
			continue;
		}
		if (bad) {
			continue;
		}
		if (x == 0) {
		    ++distinct;
			++f[x];
		} else if (f[x - 1] > 0) {
			++f[x];
			--f[x - 1];
		} else {
			bad = true;
		}
		if (distinct > K) {
			bad = true;
		}
	}
	cout << (bad ? "NO" : "YES") << '\n';
}
int main() {
	ios::sync_with_stdio(0); cin.tie(0);
	int t; cin >> t; while(t--)
	solve();
}