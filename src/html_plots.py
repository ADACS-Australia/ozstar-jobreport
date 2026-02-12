import pygal
import numpy as np
import pandas as pd

class HtmlPlots:

    TEMPLATE_STRING = """
<!DOCTYPE html>
<html>

<head>
    <script type="text/javascript" src="http://kozea.github.com/pygal.js/latest/pygal-tooltips.min.js"></script>
    <!-- ... -->
</head>

<body>
{html_figures}
</body>

</html>
"""

    def __init__(self, plot_data):
        figures = []
        for name, df in plot_data.items():
            if df is not None:
                figures.append(f"<figure> {str(SvgPlot(df, title=name))} </figure>")
        self.html_figures = "\n".join(figures)

    def __str__(self):
        return self.TEMPLATE_STRING.format(html_figures=self.html_figures)


class SvgPlot:
    def __init__(self, df, title='', xlabel='x', ylims=None):
        if ylims is not None:
            y_lims = {
                'min_value': ylims[0],
                'max_value': ylims[1]
            }
        else:
            y_lims = {}

        self.chart = pygal.XY(
            show_dots=True,
            title=title,
            x_title=xlabel,
            **y_lims,
            )

        df = pd.DataFrame(df)

        for col in df.columns:
            s = df[col]
            s.dropna(inplace=True)
            if not s.empty:
                xy = list(zip(s.index, s))
                self.chart.add(col, xy)

    def __str__(self):
        return self.chart.render(is_unicode=True, disable_xml_declaration=True, pretty_print=True)
