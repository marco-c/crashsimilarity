# crashsimilarity

[![Build Status](https://travis-ci.org/marco-c/crashsimilarity.svg?branch=master)](https://travis-ci.org/marco-c/crashsimilarity)
[![codecov](https://codecov.io/gh/marco-c/crashsimilarity/branch/master/graph/badge.svg)](https://codecov.io/gh/marco-c/crashsimilarity)

### Description
Crashsimilarity is a tool to cluster slightly different crash reports, reporting the same problem. It is built for mozilla and support crash reports produced by [breakpad](https://chromium.googlesource.com/breakpad/breakpad/).

 :exclamation: The project is in early prototype stage.  :exclamation:

### How does it work
It use doc2vec for word embedding. Similarity based on [WMD Distance](http://proceedings.mlr.press/v37/kusnerb15.pdf) is calculated.

### How to run
For now only command line interface is supported. Have a look at [cli](https://github.com/marco-c/crashsimilarity/tree/master/crashsimilarity/cli) directory.

### Tests
```sh
# Run all tests
py.test tests

# Run a specific test
py.test tests/test_whatever.py
```
