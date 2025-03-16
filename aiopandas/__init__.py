from pandas import *
import asyncio

from warnings import catch_warnings, simplefilter

from pandas.core.frame import DataFrame
from pandas.core.series import Series

try:
    with catch_warnings():
        simplefilter("ignore", category=FutureWarning)
        from pandas import Panel
except ImportError:  # pandas>=1.2.0
    Panel = None
Rolling, Expanding = None, None
try:  # pandas>=1.0.0
    from pandas.core.window.rolling import _Rolling_and_Expanding
except ImportError:
    try:  # pandas>=0.18.0
        from pandas.core.window import _Rolling_and_Expanding
    except ImportError:  # pandas>=1.2.0
        try:  # pandas>=1.2.0
            from pandas.core.window.expanding import Expanding
            from pandas.core.window.rolling import Rolling
            _Rolling_and_Expanding = Rolling, Expanding
        except ImportError:  # pragma: no cover
            _Rolling_and_Expanding = None
try:  # pandas>=0.25.0
    from pandas.core.groupby.generic import SeriesGroupBy  # , NDFrameGroupBy
    from pandas.core.groupby.generic import DataFrameGroupBy
except ImportError:  # pragma: no cover
    try:  # pandas>=0.23.0
        from pandas.core.groupby.groupby import DataFrameGroupBy, SeriesGroupBy
    except ImportError:
        from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy
try:  # pandas>=0.23.0
    from pandas.core.groupby.groupby import GroupBy
except ImportError:  # pragma: no cover
    from pandas.core.groupby import GroupBy

try:  # pandas>=0.23.0
    from pandas.core.groupby.groupby import PanelGroupBy
except ImportError:
    try:
        from pandas.core.groupby import PanelGroupBy
    except ImportError:  # pandas>=0.25.0
        PanelGroupBy = None

def inner_generator(df_function='apply'):
    async def inner(df, async_func, *args, max_parallel=16, on_error='raise', tqdm=None, tqdm_kwargs=None, **kwargs):
        """
        Parameters
        ----------
        df : DataFrame | Series | GroupBy
            The input data, which may be grouped.

        async_func : async function
            An asynchronous function to be applied to each (grouped) element of `df`.

        max_parallel : int
            Maximum number of concurrent executions of `async_func`. Default is `16`.

        on_error : {'raise', 'ignore'} | function | coroutine
            Specifies how to handle errors:
            - `'raise'`: Raises the exception and stops further executions.
            - `'ignore'`: Ignores the exception and returns `None` for the corresponding element.
            - Function or coroutine: Called with the exception as an argument. If this handler raises an exception, 
              execution stops, and the error propagates.

        tqdm : tqdm class | None, optional
            A `tqdm` class (from `tqdm import tqdm`) used to display a progress bar. Default is `None` (no progress bar).

        tqdm_kwargs : dict | None, optional
            Keyword arguments passed to the `tqdm` instance if `tqdm` is used.

        **kwargs : dict, optional
            Additional arguments passed to `df.apply()`.
        """


        if len(args) > 0:
            # *args intentionally not supported (see #244, #299 - tqdm)
            warnings.warn(
                "Except async_func, normal arguments are intentionally" +
                " not supported by" +
                " `(DataFrame|Series|GroupBy).aapply`." +
                " Use keyword arguments instead.",
            )

        t = None
        if tqdm is not None:
            tqdm_kwargs = (tqdm_kwargs or {}).copy()
            deprecated_t = [tqdm_kwargs.pop('deprecated_t', None)]
            total = tqdm_kwargs.pop("total", getattr(df, 'ngroups', None))
            if total is None:  # not grouped
                if df_function == 'applymap':
                    total = df.size
                elif isinstance(df, Series):
                    total = len(df)
                elif (_Rolling_and_Expanding is None or
                      not isinstance(df, _Rolling_and_Expanding)):
                    # DataFrame or Panel
                    axis = kwargs.get('axis', 0)
                    if axis == 'index':
                        axis = 0
                    elif axis == 'columns':
                        axis = 1
                    # when axis=0, total is shape[axis1]
                    total = df.size // df.shape[axis]

            # Init bar
            if deprecated_t[0] is not None:
                t = deprecated_t[0]
                deprecated_t[0] = None
            else:
                t = tqdm(total=total, **tqdm_kwargs)

        try:  # pandas>=1.3.0
            from pandas.core.common import is_builtin_func
        except ImportError:
            is_builtin_func = df._is_builtin_func
        try:
            async_func = is_builtin_func(async_func)
        except TypeError:
            pass

        semaphore = asyncio.Semaphore(max_parallel)
        stop_event = asyncio.Event()

        async def wrapper(*args, **kwargs):
            async with semaphore:
                if not stop_event.is_set():
                    out = None
                    try:
                        out = await async_func(*args, **kwargs)
                    except Exception as e:
                        if on_error == 'raise':
                            stop_event.set()
                            raise e
                        if on_error == 'ignore':
                            pass

                        if callable(on_error):
                            try:
                                if asyncio.iscoroutinefunction(on_error):
                                    out = await on_error(e)
                                else:
                                    out = on_error(e)
                            except Exception as handler_error:
                                stop_event.set()
                                raise handler_error

                    if tqdm is not None:
                        t.update(n=1 if not t.total or t.n < t.total else 0)
                    return out

        # Apply the provided function (in **kwargs)
        try:
            return await asyncio.gather(*list(getattr(df, df_function)(wrapper, **kwargs)))
        finally:
            if tqdm is not None:
                t.close()

    return inner

# Monkeypatch pandas to provide easy methods
Series.aapply = inner_generator()
SeriesGroupBy.aapply = inner_generator()
Series.amap = inner_generator('map')
SeriesGroupBy.amap = inner_generator('map')

DataFrame.aapply = inner_generator()
DataFrameGroupBy.aapply = inner_generator()
DataFrame.aapplymap = inner_generator('applymap')
DataFrame.amap = inner_generator('map')
DataFrameGroupBy.amap = inner_generator('map')

if Panel is not None:
    Panel.aapply = inner_generator()
if PanelGroupBy is not None:
    PanelGroupBy.aapply = inner_generator()

GroupBy.aapply = inner_generator()
GroupBy.aaggregate = inner_generator('aggregate')
GroupBy.atransform = inner_generator('transform')

if Rolling is not None and Expanding is not None:
    Rolling.aapply = inner_generator()
    Expanding.aapply = inner_generator()
elif _Rolling_and_Expanding is not None:
    _Rolling_and_Expanding.aapply = inner_generator()

