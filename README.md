# crashsimilarity

[![Build Status](https://travis-ci.org/marco-c/crashsimilarity.svg?branch=master)](https://travis-ci.org/marco-c/crashsimilarity)
[![codecov](https://codecov.io/gh/marco-c/crashsimilarity/branch/master/graph/badge.svg)](https://codecov.io/gh/marco-c/crashsimilarity)

### Description
Crashsimilarity is a tool to cluster slightly different crash reports, reporting the same problem. It supports crashes reported to the Mozilla [Socorro crash reporting system](https://crash-stats.mozilla.com/)

It uses doc2vec for word embedding and [WMD](http://proceedings.mlr.press/v37/kusnerb15.pdf) as a distance metric.

:exclamation: The project is in early prototype stage.  :exclamation:

### How to run
For now only command line interface is supported. Have a look at the [cli](https://github.com/marco-c/crashsimilarity/tree/master/crashsimilarity/cli) directory.

### Tests
```sh
# Run all tests
py.test tests

# Run a specific test
py.test tests/test_whatever.py
```