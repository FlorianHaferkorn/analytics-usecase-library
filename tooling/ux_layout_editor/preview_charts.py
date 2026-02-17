"""
Live-preview chart builders for UX Layout Editor.
Uses Plotly with sample data so the editor shows real chart types (line, bar, waterfall, etc.).
"""

from typing import Any, List, Optional

import plotly.graph_objects as go


def sample_data_trend() -> tuple:
    """Lists (x_labels, y_values) for a line chart."""
    x = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    y = [102, 98, 105, 110, 108, 115]
    return x, y


def sample_data_waterfall() -> tuple:
    """Lists (x_labels, y_values, measures) for Plotly Waterfall. measure: 'relative' or 'total'."""
    x = ["Start", "Price", "Volume", "Mix", "End"]
    y = [100, 12, -5, 8, 115]
    measure = ["absolute", "relative", "relative", "relative", "total"]
    return x, y, measure


def sample_data_bar() -> tuple:
    """Lists (categories, values) for a bar chart."""
    x = ["A", "B", "C", "D"]
    y = [28, 45, 32, 52]
    return x, y


def sample_data_stacked_bar() -> tuple:
    """Lists (categories, list of series) for 100% stacked bar. Series are normalized to 100%."""
    x = ["W1", "W2", "W3", "W4"]
    s1 = [40, 35, 45, 50]
    s2 = [35, 40, 30, 25]
    s3 = [25, 25, 25, 25]
    total = [a + b + c for a, b, c in zip(s1, s2, s3)]
    s1_n = [100 * a / t if t else 0 for a, t in zip(s1, total)]
    s2_n = [100 * b / t if t else 0 for b, t in zip(s2, total)]
    s3_n = [100 * c / t if t else 0 for c, t in zip(s3, total)]
    return x, [s1_n, s2_n, s3_n], ["Series A", "Series B", "Series C"]


def sample_data_funnel() -> tuple:
    """Lists (stages, values) for a funnel chart."""
    x = ["Lead", "Qualified", "Proposal", "Won"]
    y = [500, 320, 180, 95]
    return x, y


def build_preview_chart(
    visual_type: str,
    kpi_id: Optional[str] = None,
    kpi_ids: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Build a Plotly figure for the given ux_layout_rules visual_type.
    Uses sample data. Returns a figure suitable for st.plotly_chart.
    """
    layout = dict(
        margin=dict(l=40, r=40, t=40, b=40),
        height=280,
        showlegend=bool(visual_type in ("bar_chart", "hundred_percent_stacked_bar")),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=12))

    if visual_type == "trend_line":
        x, y = sample_data_trend()
        fig = go.Figure(data=[go.Scatter(x=x, y=y, mode="lines+markers", name="Value")])
        fig.update_layout(**layout)
        fig.update_yaxes(title_text="")
        return fig

    if visual_type == "waterfall":
        x, y, measure = sample_data_waterfall()
        fig = go.Figure(
            go.Waterfall(
                name="Variance",
                orientation="v",
                x=x,
                y=y,
                measure=measure,
            )
        )
        fig.update_layout(**layout)
        fig.update_yaxes(title_text="")
        return fig

    if visual_type == "bar_chart":
        x, y = sample_data_bar()
        fig = go.Figure(data=[go.Bar(x=x, y=y, name="Value")])
        fig.update_layout(**layout)
        fig.update_yaxes(title_text="")
        return fig

    if visual_type == "hundred_percent_stacked_bar":
        x, series_list, names = sample_data_stacked_bar()
        fig = go.Figure()
        for name, vals in zip(names, series_list):
            fig.add_trace(go.Bar(name=name, x=x, y=vals))
        fig.update_layout(barmode="stack", **layout)
        fig.update_yaxes(title_text="%", range=[0, 100])
        return fig

    if visual_type == "funnel":
        x, y = sample_data_funnel()
        fig = go.Figure(go.Funnel(name="", x=x, y=y))
        fig.update_layout(**layout)
        return fig

    # Fallback: placeholder for unknown type
    fig = go.Figure()
    fig.add_annotation(
        text=f"Preview: {visual_type or 'unknown'}",
        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14)
    )
    fig.update_layout(**layout)
    return fig
