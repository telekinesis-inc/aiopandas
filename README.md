# aiopandas  
🚀 **Async-Powered Pandas**: Lightweight Pandas monkey-patch that adds async support to `map`, `apply`, `applymap`, `aggregate`, and `transform`, enabling seamless handling of async functions with **controlled parallel execution** (`max_parallel`).

## ✨ Features
- **Drop-in replacement** for Pandas functions, now supporting **async functions**.
- **Automatic async execution** with **controlled concurrency** via `max_parallel`.
- **Built-in error handling** – choose between raising, ignoring, or logging errors. 
- **Supports tqdm** for real-time progress tracking.

---

## 🚀 Quick Start  

```python
import aiopandas as pd  # Monkey-patches Pandas with async methods
import asyncio

# Create a sample DataFrame
df = pd.DataFrame({'x': range(10)})

# Define an async function (simulating API calls, I/O, etc.)
async def f(x):
    await asyncio.sleep(0.1 * x)  # Simulate async processing
    return x * 2  # Example transformation

# Apply the async function to the DataFrame column
df['y'] = await df.x.amap(f, max_parallel=5)  # Default max_parallel=16
print(df)
```

## ⚠️ Handling Errors Gracefully

aiopandas includes built-in error handling, allowing you to manage failures without breaking the entire operation.

1. Default behavior (raise) – stops on the first error

```python
async def f(x):
    if x > 50 and x % 3:
        raise Exception('exception example')
    await asyncio.sleep(0.01 * x)
    return x

df = pd.DataFrame({'x': range(100)})

df['y'] = await df.x.amap(f, max_parallel=50)  # Raises an exception
```
Output (Error traceback):
```
Exception: exception example
```

2. Ignore errors (on_error='ignore')
```python
df['y'] = await df.x.amap(f, max_parallel=50, on_error='ignore')  # Easy to ignore exceptions
```

Now, instead of crashing, rows that trigger exceptions return NaN:

```python
print(df['y'])
```
```
0      0.0
1      1.0
2      2.0
...
95     NaN
96    96.0
97     NaN
98     NaN
99    99.0
Name: y, Length: 100, dtype: float64
```
3. Custom error handling (on_error=print)

You can log or process errors with a custom function (or coroutines):
```python
df['y'] = await df.x.amap(f, max_parallel=50, on_error=print)  # Print errors instead of failing
```

Output:
```
exception example
exception example
exception example
...
```

## 📊 Progress Tracking with tqdm

To visualize progress, pass tqdm as an argument:

```python
from tqdm import tqdm

df['y'] = await df.x.amap(f, max_parallel=5, tqdm=tqdm)
```
Example output:
```
 69%|█████████████████████████████████████████████████████                | 69/100 [00:06<00:03, 9.99it/s]
```

## 🎯 Why Use aiopandas?

* Ideal for async API calls (e.g., LLMs, web scraping, database queries).
* Massively speeds up Pandas workflows when dealing with async I/O operations.
* Minimal code changes – just swap .map() for .amap() (or .apply() for aapply(), etc.) and you’re good to go!

## 📦 Installation

```sh
pip install aiopandas
```

Or, install it manually:
```sh
git clone https://github.com/telekinesis-inc/aiopandas.git
cd aiopandas
pip install .
```

## 💡 Contributing

Pull requests are welcome! If you find issues or have suggestions, feel free to open an issue. 🚀

## 🙌 Acknowledgements

The monkey patching in aiopandas was heavily inspired by (basically copy-pasted) and adapted from the tqdm.pandas() method. Special thanks to the tqdm maintainers for their excellent work on integrating progress bars with Pandas.

