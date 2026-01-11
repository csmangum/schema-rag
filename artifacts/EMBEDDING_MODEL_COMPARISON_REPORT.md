================================================================================
MULTI-MODEL EMBEDDING COMPARISON REPORT
================================================================================

--------------------------------------------------------------------------------
SUMMARY TABLE
--------------------------------------------------------------------------------

Model                          Match%     Query(ms)    Index(MB)    Init(s)   
--------------------------------------------------------------------------------
all-MiniLM-L6-v2                81.82%      8.26      1.66      1.90
all-mpnet-base-v2               89.09%     13.07      2.87      1.75
all-MiniLM-L12-v2               86.36%     13.27      1.66      1.92
multi-qa-mpnet-base-dot-v1      85.45%     13.31      2.87      1.71
intfloat/e5-large-v2            89.09%     23.66      3.67      1.84

--------------------------------------------------------------------------------
PAIRWISE COMPARISONS
--------------------------------------------------------------------------------

Comparison: all-MiniLM-L6-v2_vs_all-mpnet-base-v2

  Expected Match Rate:
    Model 1: 0.8182
    Model 2: 0.8909
    Difference: +0.0727 (+8.89%)

  Model Match Rate:
    Model 1: 0.9545
    Model 2: 0.9909
    Difference: +0.0364 (+3.81%)

  Column Match Rate:
    Model 1: 0.8182
    Model 2: 0.8909
    Difference: +0.0727 (+8.89%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.5364
    Model 2: 3.9727
    Difference: +0.4364 (+12.34%)

  Average Top Score:
    Model 1: 19.2411
    Model 2: 19.9800
    Difference: +0.7388 (+3.84%)

  Performance:
    Query Time: 8.26ms → 13.07ms (+4.82ms)
    Index Size: 1.66 MB → 2.87 MB (1.21 MB)

--------------------------------------------------------------------------------

Comparison: all-MiniLM-L6-v2_vs_all-MiniLM-L12-v2

  Expected Match Rate:
    Model 1: 0.8182
    Model 2: 0.8636
    Difference: +0.0455 (+5.56%)

  Model Match Rate:
    Model 1: 0.9545
    Model 2: 0.9273
    Difference: -0.0273 (-2.86%)

  Column Match Rate:
    Model 1: 0.8182
    Model 2: 0.8636
    Difference: +0.0455 (+5.56%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.5364
    Model 2: 3.7273
    Difference: +0.1909 (+5.40%)

  Average Top Score:
    Model 1: 19.2411
    Model 2: 19.3324
    Difference: +0.0912 (+0.47%)

  Performance:
    Query Time: 8.26ms → 13.27ms (+5.01ms)
    Index Size: 1.66 MB → 1.66 MB (1.00 B)

--------------------------------------------------------------------------------

Comparison: all-MiniLM-L6-v2_vs_multi-qa-mpnet-base-dot-v1

  Expected Match Rate:
    Model 1: 0.8182
    Model 2: 0.8545
    Difference: +0.0364 (+4.44%)

  Model Match Rate:
    Model 1: 0.9545
    Model 2: 0.9727
    Difference: +0.0182 (+1.90%)

  Column Match Rate:
    Model 1: 0.8182
    Model 2: 0.8545
    Difference: +0.0364 (+4.44%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.5364
    Model 2: 3.9545
    Difference: +0.4182 (+11.83%)

  Average Top Score:
    Model 1: 19.2411
    Model 2: 19.1853
    Difference: -0.0559 (-0.29%)

  Performance:
    Query Time: 8.26ms → 13.31ms (+5.06ms)
    Index Size: 1.66 MB → 2.87 MB (1.21 MB)

--------------------------------------------------------------------------------

Comparison: all-MiniLM-L6-v2_vs_intfloat/e5-large-v2

  Expected Match Rate:
    Model 1: 0.8182
    Model 2: 0.8909
    Difference: +0.0727 (+8.89%)

  Model Match Rate:
    Model 1: 0.9545
    Model 2: 0.9818
    Difference: +0.0273 (+2.86%)

  Column Match Rate:
    Model 1: 0.8182
    Model 2: 0.8909
    Difference: +0.0727 (+8.89%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.5364
    Model 2: 4.1909
    Difference: +0.6545 (+18.51%)

  Average Top Score:
    Model 1: 19.2411
    Model 2: 20.2333
    Difference: +0.9922 (+5.16%)

  Performance:
    Query Time: 8.26ms → 23.66ms (+15.40ms)
    Index Size: 1.66 MB → 3.67 MB (2.01 MB)

--------------------------------------------------------------------------------

Comparison: all-mpnet-base-v2_vs_all-MiniLM-L12-v2

  Expected Match Rate:
    Model 1: 0.8909
    Model 2: 0.8636
    Difference: -0.0273 (-3.06%)

  Model Match Rate:
    Model 1: 0.9909
    Model 2: 0.9273
    Difference: -0.0636 (-6.42%)

  Column Match Rate:
    Model 1: 0.8909
    Model 2: 0.8636
    Difference: -0.0273 (-3.06%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.9727
    Model 2: 3.7273
    Difference: -0.2455 (-6.18%)

  Average Top Score:
    Model 1: 19.9800
    Model 2: 19.3324
    Difference: -0.6476 (-3.24%)

  Performance:
    Query Time: 13.07ms → 13.27ms (+0.20ms)
    Index Size: 2.87 MB → 1.66 MB (-1267200.00 B)

--------------------------------------------------------------------------------

Comparison: all-mpnet-base-v2_vs_multi-qa-mpnet-base-dot-v1

  Expected Match Rate:
    Model 1: 0.8909
    Model 2: 0.8545
    Difference: -0.0364 (-4.08%)

  Model Match Rate:
    Model 1: 0.9909
    Model 2: 0.9727
    Difference: -0.0182 (-1.83%)

  Column Match Rate:
    Model 1: 0.8909
    Model 2: 0.8545
    Difference: -0.0364 (-4.08%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.9727
    Model 2: 3.9545
    Difference: -0.0182 (-0.46%)

  Average Top Score:
    Model 1: 19.9800
    Model 2: 19.1853
    Difference: -0.7947 (-3.98%)

  Performance:
    Query Time: 13.07ms → 13.31ms (+0.24ms)
    Index Size: 2.87 MB → 2.87 MB (9.00 B)

--------------------------------------------------------------------------------

Comparison: all-mpnet-base-v2_vs_intfloat/e5-large-v2

  Expected Match Rate:
    Model 1: 0.8909
    Model 2: 0.8909
    Difference: +0.0000 (+0.00%)

  Model Match Rate:
    Model 1: 0.9909
    Model 2: 0.9818
    Difference: -0.0091 (-0.92%)

  Column Match Rate:
    Model 1: 0.8909
    Model 2: 0.8909
    Difference: +0.0000 (+0.00%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.9727
    Model 2: 4.1909
    Difference: +0.2182 (+5.49%)

  Average Top Score:
    Model 1: 19.9800
    Model 2: 20.2333
    Difference: +0.2534 (+1.27%)

  Performance:
    Query Time: 13.07ms → 23.66ms (+10.59ms)
    Index Size: 2.87 MB → 3.67 MB (825.00 KB)

--------------------------------------------------------------------------------

Comparison: all-MiniLM-L12-v2_vs_multi-qa-mpnet-base-dot-v1

  Expected Match Rate:
    Model 1: 0.8636
    Model 2: 0.8545
    Difference: -0.0091 (-1.05%)

  Model Match Rate:
    Model 1: 0.9273
    Model 2: 0.9727
    Difference: +0.0455 (+4.90%)

  Column Match Rate:
    Model 1: 0.8636
    Model 2: 0.8545
    Difference: -0.0091 (-1.05%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.7273
    Model 2: 3.9545
    Difference: +0.2273 (+6.10%)

  Average Top Score:
    Model 1: 19.3324
    Model 2: 19.1853
    Difference: -0.1471 (-0.76%)

  Performance:
    Query Time: 13.27ms → 13.31ms (+0.04ms)
    Index Size: 1.66 MB → 2.87 MB (1.21 MB)

--------------------------------------------------------------------------------

Comparison: all-MiniLM-L12-v2_vs_intfloat/e5-large-v2

  Expected Match Rate:
    Model 1: 0.8636
    Model 2: 0.8909
    Difference: +0.0273 (+3.16%)

  Model Match Rate:
    Model 1: 0.9273
    Model 2: 0.9818
    Difference: +0.0545 (+5.88%)

  Column Match Rate:
    Model 1: 0.8636
    Model 2: 0.8909
    Difference: +0.0273 (+3.16%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.7273
    Model 2: 4.1909
    Difference: +0.4636 (+12.44%)

  Average Top Score:
    Model 1: 19.3324
    Model 2: 20.2333
    Difference: +0.9010 (+4.66%)

  Performance:
    Query Time: 13.27ms → 23.66ms (+10.39ms)
    Index Size: 1.66 MB → 3.67 MB (2.01 MB)

--------------------------------------------------------------------------------

Comparison: multi-qa-mpnet-base-dot-v1_vs_intfloat/e5-large-v2

  Expected Match Rate:
    Model 1: 0.8545
    Model 2: 0.8909
    Difference: +0.0364 (+4.26%)

  Model Match Rate:
    Model 1: 0.9727
    Model 2: 0.9818
    Difference: +0.0091 (+0.93%)

  Column Match Rate:
    Model 1: 0.8545
    Model 2: 0.8909
    Difference: +0.0364 (+4.26%)

  Average Docs Returned:
    Model 1: 5.0000
    Model 2: 5.0000
    Difference: +0.0000 (+0.00%)

  Average Schema Refs:
    Model 1: 3.9545
    Model 2: 4.1909
    Difference: +0.2364 (+5.98%)

  Average Top Score:
    Model 1: 19.1853
    Model 2: 20.2333
    Difference: +1.0481 (+5.46%)

  Performance:
    Query Time: 13.31ms → 23.66ms (+10.35ms)
    Index Size: 2.87 MB → 3.67 MB (825.00 KB)

--------------------------------------------------------------------------------

================================================================================