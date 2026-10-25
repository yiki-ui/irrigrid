# ============= src/reports/export_utils.py =============
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime

class ExportUtils:
    """Export data to various formats"""
    
    @staticmethod
    def export_to_excel(data: Dict, filename: str):
        """Export project data to Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Project info
            if 'project' in data:
                df_project = pd.DataFrame([data['project']])
                df_project.to_excel(writer, sheet_name='Project Info', index=False)
            
            # System design
            if 'system_design' in data:
                df_design = pd.DataFrame([data['system_design']])
                df_design.to_excel(writer, sheet_name='System Design', index=False)
            
            # Irrigation schedule
            if 'schedule' in data:
                df_schedule = pd.DataFrame(data['schedule'])
                df_schedule.to_excel(writer, sheet_name='Irrigation Schedule', index=False)
            
            # Cost breakdown
            if 'costs' in data:
                df_costs = pd.DataFrame([data['costs']])
                df_costs.to_excel(writer, sheet_name='Cost Analysis', index=False)
        
        print(f"Data exported to {filename}")
    
    @staticmethod
    def export_to_json(data: Dict, filename: str):
        """Export data to JSON"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, default=str)
        print(f"Data exported to {filename}")
    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: str):
        """Export list of dicts to CSV"""
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
    
    @staticmethod
    def generate_bill_of_materials(system_design: Dict) -> pd.DataFrame:
        """Generate BOM from system design"""
        bom_data = [
            {'Item': 'Drip Emitters', 'Quantity': system_design.get('total_emitters', 0), 'Unit': 'pcs'},
            {'Item': 'Lateral Pipes (16mm)', 'Quantity': system_design.get('lateral_length', 0), 'Unit': 'm'},
            {'Item': 'Mainline Pipe (50mm)', 'Quantity': system_design.get('mainline_length', 0), 'Unit': 'm'},
            {'Item': 'Screen Filter', 'Quantity': 1, 'Unit': 'pcs'},
            {'Item': 'Fertilizer Tank', 'Quantity': 1, 'Unit': 'pcs'},
            {'Item': 'Control Valves', 'Quantity': system_design.get('num_valves', 2), 'Unit': 'pcs'},
            {'Item': 'Fittings Set', 'Quantity': 1, 'Unit': 'set'},
        ]
        
        if system_design.get('pump_required', False):
            bom_data.append({'Item': 'Water Pump', 'Quantity': 1, 'Unit': 'pcs'})
        
        return pd.DataFrame(bom_data)
