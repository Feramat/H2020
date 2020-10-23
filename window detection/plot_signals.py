#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# plot_signals.py
#
"""
@author: Sulc Jan
"""
import pandas as pd
import plotly.offline as py
import plotly.graph_objs as go


def plot_signals(list_df, outfile, xlabel='', ylabel='', title='', mode='lines', sig_names=None):
    data = []
    idx = -1

    if isinstance(list_df, (pd.DataFrame, pd.Series)):
        list_df = [list_df]

    for df_s in list_df:
        idx += 1
        if isinstance(df_s, pd.Series):
            df_s = pd.DataFrame(df_s)
        for sig in df_s.columns:
            if sig_names is not None:
                sig_name = sig_names[idx]
            else:
                sig_name = sig

            tr = go.Scatter(name=sig_name, x=df_s[sig].index, y=df_s[sig].astype(float).round(2), mode=mode)
            data.append(tr)

    layout = go.Layout(
        title=title,
        hovermode='closest',

        xaxis=dict(
            title=xlabel,
        ),
        yaxis=dict(
            title=ylabel,
        ),
    )

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=outfile, auto_open=False)
    # py.plot(fig, filename=outfile, image='svg', image_width=700, image_height=350)
