#include<bits/stdc++.h>
using namespace std;
#define ll long long
#define endl '\n'

const int MOD = 1e9 + 7;
void SOLVE() {
    int n; cin >> n;
    char c;
    ll answer = 1;
    for(int i = 0; i < n; i++){
        cin >> c;
        if(c == '0') answer = (answer * 2LL) % MOD;
    }
    cout << (answer - 1 + MOD) % MOD << endl;
}
signed main(){
    ios_base::sync_with_stdio(false); cout.tie(nullptr); cin.tie(nullptr);
    //int o_o; cin >> o_o; while(o_o--)
    SOLVE(); return 0;
}