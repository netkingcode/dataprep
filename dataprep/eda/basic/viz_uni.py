"""
This module implements functions for plotting visualizations for a single field.
"""
# pytype: disable=import-error
# pylint: disable=R0903
# pylint: disable=R0914
import math
from typing import Any, Dict, Optional, Tuple, List
from operator import itemgetter
import bokeh.palettes as bp
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from bokeh.models import (
    ColumnDataSource,
    FixedTicker,
    FuncTickFormatter,
    Grid,
    HoverTool,
    LinearAxis,
    Plot,
    Legend,
    LegendItem,
)
from bokeh.models.annotations import Title
from bokeh.models.glyphs import Circle, Rect, Segment, VBar
from bokeh.models.ranges import FactorRange
from bokeh.plotting import figure
from bokeh.transform import cumsum

from ..palette import PALETTE

TOOLS = ""


class UniViz:
    """
    Encapsulation for Univariate visualizations.
    """

    pie: bool = False  # to know if the pie chart is plotted error-lessly.
    barplot: bool = False  # to know if the bar plot is plotted error-lessly.
    box: bool = False  # to know if the box plot is plotted error-lessly.
    hist: bool = False  # to know if the histogram is plotted error-lessly.
    qqnorm: bool = False  # to know if the QQ norm plot is plotted error-lessly.
    kde: bool = False  # to know if the kernel density plot is plotted error-lessly.
    cat_caption: str = "Top {} of {} categories"
    max_xlab_len: int = 15  # maximum length of x axis label for bar plots
    max_num_legend: int = 7  # maximum number of entries in pi plot legend
    num_x_vals: int = 50  # number of x coordinates for gaussian_kde
    max_bar_labels: int = 30  # maximum number of labels in bar plot

    def pie_viz(
        self, data: Dict[str, int], col_x: str, bars: int, ascending: bool
    ) -> Any:
        """
        Pie chart vizualisation for categorical data
        :param data: the result from the intermediate
        :param col_x: the plotted column
        :param bars: number of slices to show in the pie
        :param ascending: if True plot smallest to largest slices of pie,
        else plot largest to smallest
        :return: Bokeh plot figure
        """
        chart_radius = 0.62
        data_df = (
            pd.Series(data)
            .dropna()
            .reset_index(name="count")
            .rename(columns={"index": "cat"})
        )
        data_sorted = data_df.sort_values(by=["count"], ascending=ascending)
        if len(data_sorted) > bars:
            data_df = data_sorted[0:bars]
            data_df = data_df.append(
                {"cat": "Other", "count": data_sorted["count"][bars:].sum()},
                ignore_index=True,
            )
        else:
            data_df = data_sorted
        total_count = sum(data_df["count"])
        data_df["percen"] = data_df["count"] / total_count * 100
        data_df["angle"] = (data_df["percen"] / 100) * 2 * math.pi
        color_list = bp.d3["Category20c"]  # pylint: disable=E1101
        color_list.update({1: ["#084594"], 2: ["#084594", "#9ecae1"]})
        color_list = color_list[20] * (len(data_df["cat"]) // len(color_list[20]) + 1)
        data_df["colour"] = color_list[0 : len(data_df)]
        plot_figure = figure(
            title="{}".format(col_x), tools=TOOLS, toolbar_location=None
        )

        renderer = plot_figure.wedge(
            x=0,
            y=1,
            radius=chart_radius,
            start_angle=cumsum("angle", include_zero=True),
            end_angle=cumsum("angle"),
            line_color="white",
            fill_color="colour",
            source=data_df,
        )
        hover = HoverTool(
            tooltips=[
                ("" + col_x + "", "@cat"),
                ("Count", "@count"),
                ("Percentage", "@percen{0.2f}%"),
            ],
            mode="mouse",
        )
        if len(data_df) <= self.max_num_legend:
            legend = Legend(
                items=[LegendItem(label=dict(field="cat"), renderers=[renderer])]
            )
            legend.label_text_font_size = "8pt"
            plot_figure.add_layout(legend, "right")
        plot_figure.add_tools(hover)
        plot_figure.axis.axis_label = None
        plot_figure.axis.visible = False
        plot_figure.grid.grid_line_color = None
        plot_figure.title.text_font_size = "10pt"
        # plot_figure.legend.location = "top_left"
        # plot_figure.legend.background_fill_alpha = 0.5
        self.pie = True
        return plot_figure

    def bar_viz(  # pylint: disable=too-many-arguments
        self,
        data: Dict[Any, Any],
        missing: List[int],
        col_x: str,
        bars: int,
        ascending: bool,
    ) -> Any:
        """
        Bar chart vizualisation for the categorical data
        :param data: the result from the intermediate
        :param missing: number of missing values in column
        :param col_x: the name of the field
        :param bars: the number of bars to show in plot
        :param ascending: if True show bars plotted in ascending order,
        else show bars plotted in descending order
        :return: Bokeh plot figure
        """
        miss_cnt = missing[0]
        data_sorted = sorted(data.items(), key=itemgetter(1), reverse=(not ascending))[
            0:bars
        ]
        cat_list = [
            (str(x[0])[: (self.max_xlab_len - 1)] + "...")
            if len(str(x[0])) > self.max_xlab_len
            else str(x[0])
            for x in data_sorted
        ]
        data_source = pd.DataFrame(
            {"count": [i[1] for i in data_sorted], "cat": cat_list}
        )
        total = sum([y for (x, y) in data.items()]) + miss_cnt
        data_source["percen"] = data_source["count"] / total * 100
        interm = ColumnDataSource(data_source)
        if miss_cnt > 0:
            miss_perc = round(miss_cnt / total * 100, 1)
            title = "{} ({}% missing values)".format(col_x, miss_perc)
        else:
            title = "{}".format(col_x)
        plot_figure = figure(
            tools=TOOLS,
            title=title,
            x_range=FactorRange(factors=cat_list),
            toolbar_location=None,
        )

        hover = HoverTool(
            tooltips=[
                ("" + col_x + "", "@cat"),
                ("Count", "@count"),
                ("Percentage", "@percen{0.2f}%"),
            ],
            mode="mouse",
        )
        plot_bars = VBar(
            x="cat", top="count", bottom=0, width=0.9, fill_color="#3182bd"
        )
        plot_figure.add_glyph(interm, plot_bars)
        plot_figure.add_tools(hover)
        plot_figure.xaxis.major_label_orientation = math.pi / 3
        plot_figure.xgrid.grid_line_color = None
        plot_figure.ygrid.grid_line_color = None
        plot_figure.yaxis.major_label_text_font_size = "0pt"
        plot_figure.yaxis.major_tick_line_color = None
        plot_figure.yaxis.minor_tick_line_color = None
        # plot_figure.xaxis.axis_label = col_x
        plot_figure.yaxis.axis_label = "Count"
        plot_figure.title.text_font_size = "10pt"
        if len(data.items()) > bars:
            plot_figure.xaxis.axis_label = self.cat_caption.format(
                data_source.shape[0], len(data.items())
            )
        if bars > self.max_bar_labels:
            plot_figure.xaxis.major_label_text_font_size = "0pt"

        self.barplot = True
        return plot_figure

    def hist_viz(  # pylint: disable=too-many-arguments
        self,
        data: Tuple[np.array, np.array],
        missing: List[int],
        orig_df_len: int,
        show_y_label: bool,
        col_x: str,
        yscale: str,
    ) -> Any:
        """
        Histogram for a column
        :param data: intermediate result
        :param missing: the number of missing values
        :param orig_df_len: the original dataframe length
        :param show_y_label: if True show y axis labels
        :param col_x: name of the column
        :param yscale: linear or logarithmic y axis
        :return: Bokeh Plot Figure
        """
        hist_array = data[0]
        bins_array = data[1]
        miss_cnt = missing[0]
        if miss_cnt > 0:
            miss_perc = np.round(miss_cnt / orig_df_len * 100, 1)
            title = "{} ({}% missing values)".format(col_x, miss_perc)
        else:
            title = "{}".format(col_x)

        plot_figure = figure(
            tools=TOOLS, title=title, toolbar_location=None, y_axis_type=yscale
        )

        data_source = pd.DataFrame(
            {
                "left": bins_array[:-1],
                "right": bins_array[1:],
                "freq": hist_array,
                "percen": hist_array / orig_df_len * 100,
            }
        )
        interm = ColumnDataSource(data_source)

        hover = HoverTool(
            tooltips=[
                ("Bin", "[@left, @right]"),
                ("Frequency", "@freq"),
                ("Percentage", "@percen{0.2f}%"),
            ],
            mode="vline",
        )
        plot_figure.quad(
            source=interm,
            left="left",
            right="right",
            bottom=0.01,
            alpha=0.5,
            top="freq",
            fill_color="#6baed6",
        )
        plot_figure.add_tools(hover)

        plot_figure.xaxis.major_label_orientation = math.pi / 3
        plot_figure.xaxis.major_label_text_font_size = "10pt"
        plot_figure.xaxis.major_tick_line_color = "black"
        plot_figure.xgrid.grid_line_color = None
        plot_figure.ygrid.grid_line_color = None
        plot_figure.yaxis.axis_label = "Frequency"
        plot_figure.title.text_font_size = "10pt"
        plot_figure.xaxis.ticker = bins_array
        if not show_y_label:
            plot_figure.yaxis.major_label_text_font_size = "0pt"
            plot_figure.yaxis.major_tick_line_color = None
            plot_figure.yaxis.minor_tick_line_color = None
            plot_figure.xaxis.minor_tick_line_color = None

        self.hist = True
        return plot_figure

    def qqnorm_viz(self, in_data: Dict[str, Any], col_x: str) -> Any:
        """
        QQ-Norm plot for a column
        :param in_data: intermediate result
        :param col_x: name of the field
        :return: Bokeh Plot Figure
        """
        plot = figure(tools=TOOLS, title="{}".format(col_x), toolbar_location=None)
        plot.circle(
            x=list(in_data["theory"]),
            y=list(in_data["sample"]),
            size=3,
            color=PALETTE[0],
        )
        all_values = np.concatenate((in_data["theory"], in_data["sample"]))
        plot.line(
            x=[np.min(all_values), np.max(all_values)],
            y=[np.min(all_values), np.max(all_values)],
            color="red",
        )
        hover = HoverTool(tooltips=[("x", "@x"), ("y", "@y")], mode="mouse")
        plot.add_tools(hover)
        plot.xgrid.grid_line_color = None
        plot.ygrid.grid_line_color = None

        plot.xaxis.axis_label = "Normal Quantiles"
        plot.yaxis.axis_label = "Quantiles of {}".format(col_x)
        plot.title.text_font_size = "10pt"
        self.qqnorm = True
        return plot

    def hist_kde_viz(self, data: np.core.array, bandwidth: float, col_x: str) -> Any:
        """
        histogram + KDE visualization
        :param data: tuple containing frequency, bins and values
        :param bandwidth: required bandwidth of the kde
        :param col_x: the name of the column
        :return: the Bokeh Plot Figure
        """
        data = data[~np.isnan(data)]
        freq, edges = np.histogram(data, density=True)
        x_vals = np.linspace(np.min(data), np.max(data), self.num_x_vals)
        pdf = gaussian_kde(data, bw_method=bandwidth)
        data_source = pd.DataFrame(
            {"left": edges[:-1], "right": edges[1:], "freq": freq}
        )
        interm = ColumnDataSource(data_source)
        plot_figure = figure(
            tools=TOOLS, title="{}".format(col_x), toolbar_location=None
        )
        hist = plot_figure.quad(
            source=interm,
            left="left",
            right="right",
            bottom=1e-7,
            alpha=0.5,
            top="freq",
            fill_color="#6baed6",
        )
        hover_hist = HoverTool(
            renderers=[hist],
            tooltips=[("Bin", "[@left, @right]"), ("Density", "@freq")],
            mode="mouse",
        )
        line = plot_figure.line(
            x_vals, pdf(x_vals), line_color="#9467bd", line_width=2, alpha=0.5
        )
        hover_dist = HoverTool(
            renderers=[line], tooltips=[("x", "@x"), ("y", "@y")], mode="mouse"
        )
        plot_figure.add_tools(hover_hist)
        plot_figure.add_tools(hover_dist)
        plot_figure.title.text_font_size = "10pt"
        plot_figure.xaxis.major_label_orientation = math.pi / 3
        plot_figure.xaxis.major_label_text_font_size = "10pt"
        plot_figure.yaxis.major_label_text_font_size = "10pt"
        plot_figure.xgrid.grid_line_color = None
        plot_figure.ygrid.grid_line_color = None
        plot_figure.yaxis.axis_label = "Density"
        self.kde = True
        return plot_figure

    def box_viz(
        self,
        data: Dict[str, Dict[str, Any]],
        col_x: str,
        col_y: Optional[str] = None,
        box_width: float = 0.25,
    ) -> Any:
        """
        *SPECIAL CASE
        Box plot for any number of categories or a single column
        :param data: intermediate result
        :param col_x: name in case of a single column
        :param col_y: name of column y in plot(df, x, y)
        :param box_width: width of each box
        :return: Bokeh Plot Figure
        """
        df = pd.DataFrame(data)  # , index=range(0, len(data)))
        df = df.append(
            pd.Series(
                {col: i for col, i in zip(df.columns, range(1, len(df.columns) + 1))},
                name="x",
            )
        )
        df = df.transpose()
        df["y"], df["w"] = (df["tf"] + df["sf"]) / 2, [box_width] * len(df)
        df["x0"], df["x1"] = df["x"] - box_width / 2, df["x"] + box_width / 2
        df["h"] = df["sf"] - df["tf"]

        # Bokeh plotting code from here
        if col_y is None:
            title = "{}".format(col_x)
        else:
            title = "{} by {}".format(col_y, col_x)

        plot = Plot(
            plot_width=300,
            plot_height=500,
            min_border=0,
            toolbar_location=None,
            tools=[],
            title=Title(text=title),
        )

        hover_box = HoverTool(
            tooltips=[("25%", "@tf"), ("50%", "@fy"), ("75%", "@sf")],
            mode="mouse",
            names=["box"],
        )

        plot.add_glyph(
            ColumnDataSource(data=df),
            Rect(x="x", y="y", width="w", height="h", fill_color=PALETTE[0]),
            name="box",
        )
        plot.add_glyph(
            ColumnDataSource(data=df),
            Segment(
                x0="x0", y0="fy", x1="x1", y1="fy", line_width=1.5, line_color="black"
            ),
        )

        for cat in df.index:
            series = df.loc[cat]
            temp_list = [series["x"]] * len(series["outliers"])
            source = ColumnDataSource(
                data=pd.DataFrame({"x": temp_list, "y": series["outliers"]})
            )
            outliers = Circle(x="x", y="y", size=3, fill_color=PALETTE[6])
            plot.add_glyph(source, outliers, name="outlier")

        plot.add_glyph(
            ColumnDataSource(data=df),
            Segment(
                x0="x", y0="uw", x1="x", y1="sf", line_width=1.5, line_color="black"
            ),
        )
        plot.add_glyph(
            ColumnDataSource(data=df),
            Segment(
                x0="x", y0="lw", x1="x", y1="tf", line_width=1.5, line_color="black"
            ),
        )
        plot.add_glyph(
            ColumnDataSource(data=df),
            Segment(
                x0="x0", y0="uw", x1="x1", y1="uw", line_width=1.5, line_color="black"
            ),
            name="upper",
        )
        plot.add_glyph(
            ColumnDataSource(data=df),
            Segment(
                x0="x0", y0="lw", x1="x1", y1="lw", line_width=1.5, line_color="black"
            ),
            name="lower",
        )

        # Add Tools
        plot.add_tools(hover_box)
        plot.add_tools(
            HoverTool(
                tooltips=[("Upper Whisker", "@uw")], mode="mouse", names=["upper"]
            )
        )
        plot.add_tools(
            HoverTool(
                tooltips=[("Lower Whisker", "@lw")], mode="mouse", names=["lower"]
            )
        )
        plot.add_tools(HoverTool(tooltips=[("Value", "@y")], names=["outlier"]))

        yaxis = LinearAxis()
        xaxis = LinearAxis()

        plot.add_layout(yaxis, "left")
        plot.add_layout(xaxis, "below")
        plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
        plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
        plot.xaxis.major_label_orientation = math.pi / 4
        plot.yaxis.axis_label = col_y
        plot.xaxis.ticker = FixedTicker(ticks=list(df["x"]))
        plot.xaxis.formatter = FuncTickFormatter(
            code="""
            var mapping = """
            + str({key: value for key, value in zip(df["x"], df.index)})
            + """;
            return mapping[tick];
        """
        )
        self.box = True
        plot.title.text_font_size = "10pt"
        return plot
        # pytype: enable=import-error