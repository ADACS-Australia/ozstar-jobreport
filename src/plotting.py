import pandas as pd
import plotext
from itertools import cycle

from utils import human_time, resample

def make_ascii_plot(df, plot_width, plot_height, title="", ylims=None, colours=['default'], labels=False, verbose=False):
    if verbose:
        print(f"Generating plot: {title}")

    if df is None:
        if verbose:
            print(f"  No data available")
        return None

    # Handle case where incoming df is actually a dataseries (i.e. 1 column)
    df = pd.DataFrame(df)

    colour = cycle(colours)
    fac, tunit = human_time(df.index)
    df.index = df.index * fac

    plotext.clear_figure()
    if ylims is not None:
        plotext.ylim(*ylims)
    plotext.plotsize(plot_width, plot_height)
    plotext.theme('clear')
    plotext.title(title)
    plotext.xlabel(f'Time ({tunit})')

    for column in df.columns.tolist():
        # Resample to 2x the plot width, since the ascii characters used for plotting
        # can represent roughly two points each
        d = df[column].dropna()

        # Skip empty data series after dropping nans
        if len(d) == 0:
            continue

        x, y = resample(d.index.values, d.values, plot_width*2)
        if labels:
            label = column
        else:
            label = None
        plotext.plot(x, y, color=next(colour), label=label)

    # Save the plot as a string
    return plotext.build()
