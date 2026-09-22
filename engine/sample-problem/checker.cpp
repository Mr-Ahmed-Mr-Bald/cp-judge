#include "testlib.h"
typedef long long ll;
int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    ll pans = ouf.readLong(-2000000000000LL, 2000000000000LL, "sum of numbers");
    ll jans = ans.readLong();

    if (pans == jans) {
        quitf(_ok, "The sum is correct.");
    } else {
        quitf(_wa, "Expected %d, found %d", jans, pans);
    }
}