import argparse
import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

from tabulate import tabulate


class Scheme:
    group_by_key: str
    predicate: Callable | None = None
    reduce: Callable
    sorting: Callable | None = None
    headers: list[str]


class Parser:
    scheme: Scheme
    coll: dict[str, list[any]]

    def __init__(self, scheme: Scheme):
        self.coll = {}
        self.scheme = scheme

    def parse(self, logs: Iterable):
        group_by_key = self.scheme.group_by_key
        for log in logs:
            if self.scheme.predicate and not self.scheme.predicate(log):
                continue
            key = str(log[group_by_key])
            akk = self.coll.get(key)
            self.coll[key] = self.scheme.reduce(akk, log)


def main():
    args = parse_args()
    scheme = create_scheme(args.report, args.date)
    parser = Parser(scheme)
    for f in args.file:
        parser.parse(read_file_by_line(f))
    print_report(parser.coll.values(), scheme)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", nargs="+", help="Path to log files", type=validate_log_file)
    parser.add_argument("-d", "--date", help="Specify date to filter logs", type=validate_date)
    parser.add_argument("-r", "--report", help="Type of the report", choices=["average", None], type=str, default=None)
    args = parser.parse_args()

    if not args.file:
        msg = "No log-file is specified"
        raise argparse.ArgumentTypeError(msg)

    return args


def validate_log_file(file_path: str):
    path = Path(file_path)
    if path.exists():
        if file_path.endswith(".log"):
            return file_path
        else:
            msg = f"File <{file_path}> has an invalid extension, <.log> is expected"
            raise argparse.ArgumentTypeError(msg)
    else:
        msg = f"File <{file_path}> not found"
        raise argparse.ArgumentTypeError(msg)


def validate_date(date: str):
    if re.match(r"^[0-9T:-]+$", date):
        return date
    else:
        msg = f"Invalid format of date <{date}>, <YYYY-MM-DD> is expected"
        raise argparse.ArgumentTypeError(msg)


def create_scheme(report: str | None = None, date: str | None = None) -> Scheme:
    match report:
        case "average":
            res = create_avg_scheme()
        case _:
            res = create_def_scheme()

    if date:
        res.predicate = lambda log: log.get("@timestamp") and log["@timestamp"].startswith(date)
    return res


def create_def_scheme() -> Scheme:
    def reduce(log_akk: any, log: any):
        if log_akk:
            log_akk[1] += 1
            log_akk[2] += log["response_time"]
            return log_akk
        else:
            return [log["url"], 1, log["response_time"]]

    res = Scheme()
    res.group_by_key = "url"
    res.headers = ["url", "total", "total_response_time"]
    res.sorting = lambda values: sorted(values, key=lambda t: t[1], reverse=True)
    res.reduce = reduce
    return res


def create_avg_scheme() -> Scheme:
    def reduce(log_akk: any, log: any):
        if log_akk:
            n = log_akk[1]
            log_akk[1] += 1
            log_akk[2] *= n / (n + 1)
            log_akk[2] += log["response_time"] / (n + 1)

            return log_akk
        else:
            return [log["url"], 1, log["response_time"]]

    res = Scheme()
    res.group_by_key = "url"
    res.headers = ["url", "total", "avg_response_time"]
    res.sorting = lambda values: sorted(values, key=lambda t: t[1], reverse=True)
    res.reduce = reduce
    return res


def read_file_by_line(path: str):
    with Path(path).open() as f:
        for row in f:
            yield json.loads(row.strip())


def print_report(data: list[any], scheme: Scheme):
    values = scheme.sorting(data) if scheme.sorting else data
    tbl = tabulate(values, scheme.headers, showindex="always", floatfmt=".3f")
    print(tbl)


if __name__ == "__main__":
    main()
