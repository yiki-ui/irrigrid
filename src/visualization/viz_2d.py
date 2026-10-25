# ============= src/visualization/viz_2d.py =============
# REFACTORED: matplotlib → plotly
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict


class DripSystem2DVisualizer:
    """2D charts and plots (Plotly)"""

    @staticmethod
    def plot_soil_moisture(dates: List, moisture: List, taw: float, raw: float):
        """Plot soil moisture over time"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates, y=moisture, mode='lines',
            name='Soil Moisture',
            line=dict(color='#4a90e2', width=2),
        ))
        fig.add_hline(y=raw, line_dash='dash', line_color='orange',
                      annotation_text='RAW Threshold', annotation_position='top left')
        fig.add_hline(y=taw, line_dash='dash', line_color='red',
                      annotation_text='TAW', annotation_position='top left')

        fig.update_layout(
            xaxis_title='Date', yaxis_title='Soil Moisture Depletion (mm)',
            title=dict(text='Soil Water Balance Over Time', font=dict(size=14)),
            template='plotly_dark',
        )
        return fig

    @staticmethod
    def plot_etc_eto(dates: List, eto: List, etc: List):
        """Plot ETo and ETc comparison"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates, y=eto, mode='lines', name='ETo (Reference)',
            line=dict(color='#ff6b6b', width=2),
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=etc, mode='lines', name='ETc (Crop)',
            line=dict(color='#4ec9b0', width=2),
        ))

        fig.update_layout(
            xaxis_title='Date', yaxis_title='Evapotranspiration (mm/day)',
            title=dict(text='Evapotranspiration Comparison', font=dict(size=14)),
            template='plotly_dark',
        )
        return fig

    @staticmethod
    def plot_irrigation_schedule(schedule: List[Dict]):
        """Visualize irrigation schedule"""
        if not schedule:
            return None

        dates = [s['date'] for s in schedule]
        amounts = [s['amount_mm'] for s in schedule]

        fig = go.Figure(go.Bar(
            x=dates, y=amounts,
            marker_color='steelblue', opacity=0.8,
            name='Irrigation Amount',
        ))

        fig.update_layout(
            xaxis_title='Date', yaxis_title='Irrigation Amount (mm)',
            title=dict(text='Recommended Irrigation Schedule', font=dict(size=14)),
            template='plotly_dark',
            xaxis=dict(tickangle=45),
        )
        return fig
