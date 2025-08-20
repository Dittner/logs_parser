import sys
import os
from typing import Any
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import Scheme, Parser, create_scheme


def test_parser():
    logs = [
        {"a": 0, "b": 1, "d": "2025-06-20"},
        {"a": 0, "b": 10, "d": "2025-06-20"},
        {"a": 1, "b": 100, "d": "2025-07-30"},
    ]

    def reduce(log_akk: Any, log: Any):
        if log_akk:
            count = log_akk[2]
            log_akk[0] = log["a"]
            log_akk[1] += log["b"]
            log_akk[2] += 1
            # recalucalting average value of the column b
            log_akk[3] *= count / (count + 1)
            log_akk[3] += log["b"] / (count + 1)
            return log_akk
        else:
            return [log["a"], log["b"], 1, log["b"]] # [a, b, count, avg(b)]

    s = Scheme()
    s.group_by_key = "a"
    s.reduce = reduce

    p = Parser(s)
    p.parse(logs)
    data = list(p.coll.values())
    
    assert len(data) == 2
    assert data[0] == [0, 11, 2, 5.5] # [a, b, count, avg(b)]
    assert data[1] == [1, 100, 1, 100]


def test_def_scheme():
    logs = [
        {"url": "x", "response_time": 0.1},
        {"url": "x", "response_time": 1.0},
        {"url": "y", "response_time": 2.0},
    ]
    s = create_scheme() # grouping by url
    p = Parser(s)
    p.parse(logs)
    data = list(p.coll.values())
    
    assert len(data) == 2
    assert data[0] == ["x", 2, 1.1] # [url, count, sum(response_time)]
    assert data[1] == ["y", 1, 2.0]


def test_avg_scheme():
    logs = [
        {"url": "x", "response_time": 0.1},
        {"url": "x", "response_time": 1.0},
        {"url": "y", "response_time": 2.0},
    ]
    s = create_scheme("average") # grouping by url
    p = Parser(s)
    p.parse(logs)
    data = list(p.coll.values())
    
    assert len(data) == 2
    assert data[0] == ["x", 2, 0.55] # [url, count, avg(response_time)]
    assert data[1] == ["y", 1, 2.0]


def test_avg_scheme_filtered_by_date():
    logs = [
        {"url": "x", "response_time": 0.1, "@timestamp": "2025-06-22T13:57:47+00:00"},
        {"url": "x", "response_time": 0.9, "@timestamp": "2025-06-22T13:57:47+00:00"},
        {"url": "x", "response_time": 1.0, "@timestamp": "2025-06-23T14:57:47+00:00"},
        {"url": "y", "response_time": 2.0, "@timestamp": "2025-06-23T15:57:47+00:00"},
    ]
    s = create_scheme("average", "2025-06-22") # grouping by url
    p = Parser(s)
    p.parse(logs)
    data = list(p.coll.values())
    
    assert len(data) == 1
    assert data[0] == ["x", 2, 0.5] # [url, count, avg(response_time)]

    s = create_scheme(None, "2025")
    p = Parser(s)
    p.parse(logs)
    data = list(p.coll.values())
    
    assert len(data) == 2
    assert data[0] == ["x", 3, 2.0] # [url, count, sum(response_time)]
    assert data[1] == ["y", 1, 2.0]