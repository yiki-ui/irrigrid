# ============= src/visualization/layout_designer.py =============
# REFACTORED: matplotlib → plotly
import plotly.graph_objects as go
from typing import List, Tuple


class LayoutDesigner:
    """Design 2D irrigation system layout (Plotly)"""

    def __init__(self, area_width: float, area_length: float):
        self.width = area_width   # meters
        self.length = area_length  # meters
        self.fig = go.Figure()

    def draw_field_boundary(self):
        """Draw field boundary"""
        self.fig.add_shape(
            type='rect', x0=0, y0=0, x1=self.width, y1=self.length,
            fillcolor='rgba(144, 238, 144, 0.3)',
            line=dict(color='black', width=2),
        )

    def draw_crop_rows(self, row_spacing: float, orientation: str = 'horizontal'):
        """Draw crop rows"""
        if orientation == 'horizontal':
            num_rows = int(self.length / row_spacing)
            for i in range(num_rows):
                y = i * row_spacing
                self.fig.add_shape(
                    type='line', x0=0, y0=y, x1=self.width, y1=y,
                    line=dict(color='green', width=0.5, dash='dash'),
                    opacity=0.5,
                )
        else:
            num_rows = int(self.width / row_spacing)
            for i in range(num_rows):
                x = i * row_spacing
                self.fig.add_shape(
                    type='line', x0=x, y0=0, x1=x, y1=self.length,
                    line=dict(color='green', width=0.5, dash='dash'),
                    opacity=0.5,
                )

    def draw_laterals(
        self, lateral_spacing: float, lateral_length: float,
        orientation: str = 'horizontal'
    ):
        """Draw drip laterals"""
        lat_x, lat_y = [], []
        if orientation == 'horizontal':
            num_laterals = int(self.length / lateral_spacing)
            for i in range(num_laterals):
                y = i * lateral_spacing
                lat_x.extend([0, min(lateral_length, self.width), None])
                lat_y.extend([y, y, None])
        else:
            num_laterals = int(self.width / lateral_spacing)
            for i in range(num_laterals):
                x = i * lateral_spacing
                lat_x.extend([x, x, None])
                lat_y.extend([0, min(lateral_length, self.length), None])

        self.fig.add_trace(go.Scatter(
            x=lat_x, y=lat_y, mode='lines',
            line=dict(color='dodgerblue', width=2),
            name='Lateral',
        ))

    def draw_emitters(
        self, lateral_spacing: float, emitter_spacing: float,
        orientation: str = 'horizontal'
    ):
        """Draw emitter points"""
        em_x, em_y = [], []
        if orientation == 'horizontal':
            num_laterals = int(self.length / lateral_spacing)
            for i in range(num_laterals):
                y = i * lateral_spacing
                num_emitters = int(self.width / emitter_spacing)
                for j in range(num_emitters):
                    em_x.append(j * emitter_spacing)
                    em_y.append(y)

        self.fig.add_trace(go.Scatter(
            x=em_x, y=em_y, mode='markers',
            marker=dict(color='red', size=4),
            name='Emitters',
        ))

    def draw_mainline(self, start: Tuple[float, float], end: Tuple[float, float]):
        """Draw mainline"""
        self.fig.add_trace(go.Scatter(
            x=[start[0], end[0]], y=[start[1], end[1]],
            mode='lines', line=dict(color='red', width=4),
            name='Mainline',
        ))

    def draw_water_source(self, position: Tuple[float, float], label: str = 'Pump'):
        """Draw water source"""
        self.fig.add_trace(go.Scatter(
            x=[position[0]], y=[position[1]], mode='markers+text',
            marker=dict(color='blue', size=14, symbol='square'),
            text=[label], textposition='top center',
            name=label,
        ))

    def finalize_layout(self, title: str = "Drip Irrigation System Layout"):
        """Finalize and return figure"""
        self.fig.update_layout(
            xaxis=dict(
                title='Width (m)', range=[-5, self.width + 5],
                scaleanchor='y', scaleratio=1,
            ),
            yaxis=dict(title='Length (m)', range=[-5, self.length + 5]),
            title=dict(text=title, font=dict(size=14)),
            template='plotly_dark',
            legend=dict(x=0.85, y=0.98),
        )
        return self.fig
