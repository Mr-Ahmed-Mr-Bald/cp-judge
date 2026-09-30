#include "bits/stdc++.h"
#include "testlib.h"
// ---- inlined from the Polygon export: global.h ----
// globals.h
#pragma once
#include <string>

// YES and NO
const std::string YES = "ja", NO = "nein";

// Maximum # test cases
const int MAX_T = 100'000;

// Maximum # n per test case
const int MAX_N = 300'000;
const int MAX_Q = 300'000;

// Sum of n over all test cases
const int MAX_SUM_OF_N = 300'000;
const int MAX_SUM_OF_Q = 300'000;
using namespace std;

string lower(string str) {
  for(char &c : str)
    c = static_cast<char>(tolower(static_cast<unsigned char>(c)));
  return str;
}

int main(int argc, char *argv[]) {
  registerTestlibCmd(argc, argv);

  const int T = inf.readInt(1, MAX_T, "T");
  for(int tc = 1; tc <= T; tc++) {
    int n = inf.readInt(1, MAX_N, "n");
    int k = inf.readInt(0, n, "k");
    int q = inf.readInt(1, MAX_Q, "n");
    for(int i = 0; i < k; i++) inf.readInt(1, n, "x_i");
    for(int i = 0; i < n - 1; i++) {
        inf.readInt(1, n, "u_i");
        inf.readInt(1, n, "v_i");
    }
    for(int i = 0; i < q; i++) {
        inf.readInt(1, n, "x_i");
        string pa = lower(ouf.readWord());
        string ja = lower(ans.readWord());
        if (pa != YES && pa != NO)
          quitf(_pe, "Test case: %d, expected %s or %s, but found '%s'", tc, YES.c_str(), NO.c_str(), pa.c_str());
    
        if (ja != YES && ja != NO)
          quitf(_fail, "Test case: %d, expected %s or %s in answer, but found '%s'", tc, YES.c_str(), NO.c_str(), ja.c_str());
    
        if (pa != ja)
          quitf(_wa, "Test case: %d, expected '%s', but found '%s'", tc, ja.c_str(), pa.c_str());
    }
  }

  quitf(_ok, "All tests passed!");
}