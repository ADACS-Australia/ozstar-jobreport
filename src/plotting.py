import os
os.environ['QT_QUICK_BACKEND'] = 'software'

import plotext
import pandas as pd
import pyqtgraph as pg
from itertools import cycle
from utils import human_time, resample


# Set default colors for pyqtgraph
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

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

    for column in df.columns:

        d = df[column].dropna()

        # Skip empty data series after dropping nans
        if len(d) == 0:
            continue

        # Resample to 2x the plot width, since the ascii characters used for plotting
        # can represent roughly two points each
        x, y = resample(d.index.values, d.values, plot_width*2)
        if labels:
            label = column
        else:
            label = None
        plotext.plot(x, y, color=next(colour), label=label)

    # Save the plot as a string
    return plotext.build()

def interactive_plot(df, plot_width, plot_height, title="", ylims=None, colours=['black'], labels=False, verbose=False, jobid=None):

    win = pg.GraphicsLayoutWidget(title=f"Job Report: {jobid}")

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

    p = win.addPlot(title=title)
    if ylims is not None:
        p.setYRange(*ylims)
    if labels:
        p.addLegend()

    #plotsize
    p.setLabel('bottom', f'Time ({tunit})')

    for col in df.columns:
        # d = df[column].dropna()
        p.plot(df.index, df[col], pen=pg.mkPen(color=next(colour), width=2), name=col)

    # # Second plot below
    # win.nextRow()
    # p2 = win.addPlot(title="Double Frequency Sine")
    # p2.plot(df.index, df['c'], pen=pg.mkPen('b', width=2))
    # p2.setLabel('bottom', 'X')
    # p2.setLabel('left', 'Y')
    # p2.setYRange(-1.5, 1.5)

    win.show()
    pg.exec()
