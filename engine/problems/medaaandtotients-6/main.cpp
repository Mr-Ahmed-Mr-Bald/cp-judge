#include<bits/stdc++.h>
using namespace std;
using ll = long long;
#define endl '\n'

const int N = 1e6 + 5;
int lp[N];
vector<int> primes;
void init(){
    lp[1] = 1;
    for (int i = 2; i < N; i++){
        if (!lp[i]) {
            lp[i] = i;
            primes.push_back(i);
        }
        for (int p : primes){
            ll x = i * 1LL * p;
            if (x >= N) break;
            lp[x] = p;
            if (p == lp[i]) break;
        }
    }
}
void SOLVE() {
    int n; cin >> n;
    set<int> s;
    for(int i = 0, x; i < n; i++){
        cin >> x;
        int prod = 1;
        while(x > 1){
            int spf = lp[x];
            while(x % spf == 0) x /= spf;
            prod *= spf;
        }
        s.insert(prod);
    }
    cout << (int)s.size() << endl;
}
signed main(){
    ios_base::sync_with_stdio(false); cout.tie(nullptr); cin.tie(nullptr);
    //int o_o; cin >> o_o; while(o_o--)
    init();
    SOLVE(); return 0;
}