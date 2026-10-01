#include<bits/stdc++.h>
using namespace std;
#define ll long long
#define endl '\n'

const int N = 1e5 + 5;
vector<int> divs[N];
void SOLVE() {
    for(int i = 1; i < N; i++){
        for(int j = i; j < N; j += i){
            divs[j].push_back(i);
        }
    }

    int n; cin >> n;
    vector<int> a(n + 1), dp(n + 1, 1e9);
    for(auto & val : a) cin >> val;
    dp[0] = 0;
    for(int i = 1; i <= n; i++){
        for(int d : divs[a[i]]){
            if(i - d < 0) break;
            dp[i] = min(dp[i], dp[i - d] + 1);
        }
    }
    cout << dp[n] << endl;
}
signed main(){
    ios_base::sync_with_stdio(false); cout.tie(nullptr); cin.tie(nullptr);
    //int o_o; cin >> o_o; while(o_o--)
    SOLVE(); return 0;
}