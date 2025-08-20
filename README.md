# Logs parser
Examples:
```cmd
$ python main.py --file files/example1.log --report average
$ python main.py --file files/example1.log --date 2025-06
$ python main.py --file files/example1.log files/example2.log
```
Testing:
```cmd
$ pytest tests/test_main.py
```

## Run parser using uv
```cmd
$ pip install uv
$ uv sync
$ uv run main.py -f files/example1.log files/example2.log -r average -d 2025
```

## Run test using uv
```code
$ uv run pytest tests/test_main.py
```