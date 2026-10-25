#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import numpy as np
import pyvista as pv
import plotly.graph_objects as go

def main():
    out_dir = Path("/home/yiki-yiris/dissertation/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Enable offscreen rendering
    try:
        pv.start_xvfb()
    except Exception as e:
        print(f"xvfb start note: {e}")
        
    print("Generating 3D Terrain visualization...")
    
    # Create a 50x50m terrain with 16.4% slope
    x = np.linspace(0, 50, 50)
    y = np.linspace(0, 50, 50)
    X, Y = np.meshgrid(x, y)
    Z = Y * 0.164 # 16.4% slope
    
    grid = pv.StructuredGrid(X, Y, Z)
    plotter = pv.Plotter(off_screen=True, window_size=[1920, 1080])
    
    # Terrain
    plotter.add_mesh(grid, scalars=Z, cmap='terrain', show_edges=False, opacity=0.85)
    
    # Main line
    main_pipe = pv.Line((25, 0, 0), (25, 50, 50*0.164))
    plotter.add_mesh(main_pipe, color='darkblue', line_width=8, label='Main Line (50mm)')
    
    # Laterals
    for i, y_pos in enumerate(np.arange(0, 50, 1.2)):
        z_pos = y_pos * 0.164
        lateral = pv.Line((0, y_pos, z_pos), (50, y_pos, z_pos))
        if i == 0:
            plotter.add_mesh(lateral, color='cyan', line_width=3, label='Laterals (12mm)')
        else:
            plotter.add_mesh(lateral, color='cyan', line_width=3)
            
    # Add a point for water source
    plotter.add_mesh(pv.Sphere(radius=1.0, center=(25, 50, 50*0.164)), color='blue', label='Water Source')
    
    plotter.add_legend()
    plotter.camera_position = 'iso'
    
    plot3d_path = out_dir / "busogo_3d_terrain.png"
    plotter.screenshot(str(plot3d_path))
    print(f"Saved 3D visualization to {plot3d_path}")
    
    print("Generating 2D Layout visualization...")
    fig = go.Figure()
    
    # Field boundary
    fig.add_trace(go.Scatter(x=[0, 50, 50, 0, 0], y=[0, 0, 50, 50, 0], mode='lines', 
                             line=dict(color='black', width=2), name='Field Boundary'))
                             
    # Main line
    fig.add_trace(go.Scatter(x=[25, 25], y=[0, 50], mode='lines', 
                             line=dict(color='blue', width=4), name='Main Line (50mm)'))
                             
    # Laterals
    for i, y_pos in enumerate(np.arange(0, 50, 1.2)):
        if i == 0:
            fig.add_trace(go.Scatter(x=[0, 50], y=[y_pos, y_pos], mode='lines', 
                                     line=dict(color='cyan', width=1.5), name='Laterals (12mm)'))
        else:
            fig.add_trace(go.Scatter(x=[0, 50], y=[y_pos, y_pos], mode='lines', 
                                     line=dict(color='cyan', width=1.5), showlegend=False))
                                     
    # Water Source
    fig.add_trace(go.Scatter(x=[25], y=[50], mode='markers', 
                             marker=dict(color='darkblue', size=12, symbol='star'), name='Water Source'))

    fig.update_layout(
        title="Busogo Reference Case: 2D Irrigation Layout",
        xaxis_title="Width (m)",
        yaxis_title="Length (m)",
        width=1000,
        height=1000,
        plot_bgcolor='white'
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    plot2d_path = out_dir / "busogo_2d_layout.png"
    
    # Requires kaleido
    try:
        fig.write_image(str(plot2d_path))
        print(f"Saved 2D visualization to {plot2d_path}")
    except Exception as e:
        print(f"Failed to write plotly image (kaleido missing?): {e}")

if __name__ == "__main__":
    main()
