#include "bits/stdc++.h"
using namespace std;
typedef long long ll;
template <typename T, typename S, typename Merge>
struct ST {
	int size, n;
	Merge merge;
	T ID;
	vector<T> t;
	ST() = default;
	ST(int n_, Merge merge_, T id = T())
	: size(1), n(n_), merge(merge_), ID(id) {
		while(size < n) size *= 2;
		t.resize(2 * size, ID);
	}
	// BUILD
	// Array with default mapping
	void build(const vector<T> &a) {
		build([&](int i) { return a[i]; }, 0, n - 1, 0);
	}
	// Array with custom mapping
	template <typename U, typename Create> 
	void build(const vector<U> &a, const Create& create) {
		build([&](int i) { return create(a[i], i); }, 0, n - 1, 0);
	}
	// Constant with default mapping
	void build(const T& x) {
		build([&]([[maybe_unused]] int i) { return x; }, 0, n - 1, 0);
	}
	// Constant with custom mapping
	template <typename U, typename Create> 
	void build(const U& x, const Create& create) {
		build([&](int i) { return create(x, i); }, 0, n - 1, 0);
	}
	// SET
	void set(int i, T v) {
		set(i, v, [](T& z, const T& y) {z = y;}, 0, n - 1, 0);
	}
	template <typename Setter>
	void set(int i, S v, Setter setter) {
		set(i, v, setter, 0, n - 1, 0);
	}
	// MUTATE
	template <typename Recurse, typename Apply> // Recurse(tree_node), Apply(tree_node)
	void mutate(int l, int r, const Recurse& recurse, const Apply& apply) {
		mutate(l, r, recurse, apply, 0, n - 1, 0);
	}
	// GET
	T get(int l, int r) {
		if (l > r) return ID;
		return get(l, r, [this](const T& x, const T& y) {T z; this->merge(z, x, y); return z;}, [](const T& z) {return z;}, 0, n - 1, 0);
	}
	template <typename GetMerge, typename Select>
	auto get(int l, int r, GetMerge get_merge, Select select) {
		if (l > r) return select(ID);
		return get(l, r, get_merge, select, 0, n - 1, 0);
	}
	// LOWER BOUND
	int lower_bound(int l, int r, int v) {
		return lower_bound(l, r, v, 0, n - 1, 0);
	}
	private:
	template <typename Generator>
	void build(const Generator& gen, int l, int r, int p) {
		if (l == r) {
			if (l < n) t[p] = gen(l);
			return;
		}
		int mid = (l + r) / 2;
		build(gen, l, mid, p + p + 1);
		build(gen, mid + 1, r, p + p + 2);
		merge(t[p], t[p + p + 1], t[p + p + 2]);
	}
	template <typename Setter, typename V>
	void set(int i, V v, Setter setter, int l, int r, int p) {
		if (l == r) {setter(t[p], v); return;}
		int mid = (l + r) / 2;
		if (i > mid) set(i, v, setter, mid + 1, r, p + p + 2);
		else set(i, v, setter, l, mid, p + p + 1);
		merge(t[p], t[p + p + 1], t[p + p + 2]);
	}
	template <typename Recurse, typename Apply>
	void mutate(int l, int r, const Recurse& recurse, const Apply& apply, int _l, int _r, int p) {
		if (_r < l || _l > r || !recurse(t[p])) return;
		if (_l == _r) {
			apply(t[p]);
			return;
		}
		int mid = (_l + _r) / 2;
		mutate(l, r, recurse, apply, _l, mid, p + p + 1);
		mutate(l, r, recurse, apply, mid + 1, _r, p + p + 2);
		merge(t[p], t[p + p + 1], t[p + p + 2]);
	}
	template <typename GetMerge, typename Select>
	auto get(int l, int r, GetMerge get_merge, Select select, int _l, int _r, int p) {
		if (_r < l || _l > r) return select(ID);
		if (_l >= l && _r <= r) return select(t[p]);
		int mid = (_l + _r) / 2;
		return get_merge(get(l, r, get_merge, select, _l, mid, p + p + 1), get(l, r, get_merge, select, mid + 1, _r, p + p + 2));
	}
	int lower_bound(int l, int r, int v, int _l, int _r, int p) {
		if (_r < l || _l > r || t[p] < v) return -1;
		if (_l == _r) return _l;
		int mid = (_l + _r) / 2;
		int res = lower_bound(l, r, v, _l, mid, p + p + 1);
		if (res == -1) res = lower_bound(l, r, v, mid + 1, _r, p + p + 2);
		return res;
	}
};
void solve() {
	int n, q; cin >> n >> q;
	array<vector<int>, 2> g;
	for(int i = 0; i < 2; i++) {
		g[i].resize(n);
		for(int j = 0; j < n; j++) {
			cin >> g[i][j];
		}
	}
	int m = n + n - 2;
	vector<array<int, 3>> c(m);
	for(int j = 0; j < n - 1; j++) {
		c[j + j] = {min(g[0][j], g[0][j + 1]), max(g[0][j], g[0][j + 1]), j};
		c[j + j + 1] = {min(g[1][j], g[1][j + 1]), max(g[1][j], g[1][j + 1]), j};
	}
	sort(c.rbegin(), c.rend());
	vector<array<int, 7>> qq(q);
	for(int i = 0; i < q; i++) {
		cin >> qq[i][0] >> qq[i][1] >> qq[i][2] >> qq[i][3] >> qq[i][4] >> qq[i][5];
		qq[i][6] = i;
	}
	sort(qq.begin(), qq.end(), [](auto &a1, auto &a2) -> bool {
		return a2[4] < a1[4];
	});
	vector<bool> answer(q);
	auto merge = [](int &z, const int &x, const int &y) {z = max(x, y);};
	ST<int, int, decltype(merge)> tree(n, merge, INT_MIN);
	tree.build(INT_MAX);
	for(int i = 0, j = 0; i < q; i++) {
		auto [r1, c1, r2, c2, l, r, k] = qq[i];
		--r1; --c1; --r2; --c2;
		while(j < m && c[j][0] >= l) {
			tree.set(c[j][2], c[j][1], [](int &z, int x) {z = min(z, x);});
			++j;
		}
		answer[k] = (
			g[r1][c1] >= l && g[r1][c1] <= r &&
			g[r2][c2] >= l && g[r2][c2] <= r &&
			tree.get(min(c1, c2), max(c1, c2) - 1) <= r
		);
	}
	for(int i = 0; i < q; i++) {
		cout << (answer[i] ? "YES" : "NO") << '\n';
	}
}
int main() {
	ios::sync_with_stdio(0); cin.tie(0);
	int t; cin >> t; while(t--)
	solve();
}