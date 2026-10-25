#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Input Validation Utilities
Validates user inputs before processing
"""

from typing import Tuple, Optional
from PyQt5.QtWidgets import QWidget, QMessageBox, QLineEdit

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Validates user inputs with helpful error messages"""
    
    @staticmethod
    def validate_positive_number(
        value: str, 
        field_name: str,
        min_value: float = 0.0,
        max_value: Optional[float] = None,
        allow_zero: bool = False
    ) -> Tuple[bool, Optional[float], str]:
        """
        Validate a positive number input
        
        Returns:
            (is_valid, parsed_value, error_message)
        """
        if not value or value.strip() == "":
            return (False, None, f"{field_name} is required")
        
        try:
            num = float(value)
        except ValueError:
            return (False, None, f"{field_name} must be a valid number")
        
        if not allow_zero and num <= min_value:
            return (False, None, f"{field_name} must be greater than {min_value}")
        
        if allow_zero and num < min_value:
            return (False, None, f"{field_name} must be at least {min_value}")
        
        if max_value is not None and num > max_value:
            return (False, None, f"{field_name} must be less than {max_value}")
        
        return (True, num, "")
    
    @staticmethod
    def validate_field_dimension(value: str, field_name: str) -> Tuple[bool, Optional[float], str]:
        """Validate field dimensions (1-10000 meters)"""
        return InputValidator.validate_positive_number(
            value, field_name, min_value=1.0, max_value=10000.0
        )
    
    @staticmethod
    def validate_emitter_flow(value: str) -> Tuple[bool, Optional[float], str]:
        """Validate emitter flow rate (0.5-10 L/hr)"""
        return InputValidator.validate_positive_number(
            value, "Emitter Flow Rate", min_value=0.5, max_value=10.0
        )
    
    @staticmethod
    def validate_spacing(value: str, field_name: str) -> Tuple[bool, Optional[float], str]:
        """Validate spacing (0.1-10 meters)"""
        return InputValidator.validate_positive_number(
            value, field_name, min_value=0.1, max_value=10.0
        )
    
    @staticmethod
    def validate_pressure(value: str) -> Tuple[bool, Optional[float], str]:
        """Validate operating pressure (50-300 kPa)"""
        return InputValidator.validate_positive_number(
            value, "Operating Pressure", min_value=50.0, max_value=300.0
        )
    
    @staticmethod
    def validate_area(value: str) -> Tuple[bool, Optional[float], str]:
        """Validate area (0.01-1000 hectares)"""
        return InputValidator.validate_positive_number(
            value, "Area", min_value=0.01, max_value=1000.0
        )
    
    @staticmethod
    def validate_percentage(value: str, field_name: str) -> Tuple[bool, Optional[float], str]:
        """Validate percentage (0-100)"""
        return InputValidator.validate_positive_number(
            value, field_name, min_value=0.0, max_value=100.0, allow_zero=True
        )
    
    @staticmethod
    def validate_required_field(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate that a field is not empty"""
        if not value or value.strip() == "":
            return (False, f"{field_name} is required")
        return (True, "")
    
    @staticmethod
    def validate_line_edit(
        line_edit: QLineEdit,
        field_name: str,
        min_value: float = 0.0,
        max_value: Optional[float] = None,
        allow_zero: bool = False,
        parent: Optional[QWidget] = None
    ) -> Optional[float]:
        """
        Validate a QLineEdit and show error message if invalid
        
        Returns:
            Parsed value if valid, None if invalid (and shows error dialog)
        """
        is_valid, value, error_msg = InputValidator.validate_positive_number(
            line_edit.text(),
            field_name,
            min_value,
            max_value,
            allow_zero
        )
        
        if not is_valid:
            QMessageBox.warning(
                parent or line_edit,
                "Invalid Input",
                error_msg + f"\n\nPlease enter a valid value for {field_name}."
            )
            line_edit.setFocus()
            line_edit.selectAll()
            return None
        
        return value


# Convenience functions for common validations
def validate_design_inputs(
    field_length: QLineEdit,
    field_width: QLineEdit,
    emitter_spacing: QLineEdit,
    lateral_spacing: QLineEdit,
    parent: Optional[QWidget] = None
) -> Optional[dict]:
    """
    Validate common design inputs
    
    Returns:
        Dictionary with validated values, or None if validation failed
    """
    validator = InputValidator()
    
    # Validate field length
    length = validator.validate_line_edit(
        field_length, "Field Length", min_value=1.0, max_value=10000.0, parent=parent
    )
    if length is None:
        return None
    
    # Validate field width
    width = validator.validate_line_edit(
        field_width, "Field Width", min_value=1.0, max_value=10000.0, parent=parent
    )
    if width is None:
        return None
    
    # Validate emitter spacing
    e_spacing = validator.validate_line_edit(
        emitter_spacing, "Emitter Spacing", min_value=0.1, max_value=10.0, parent=parent
    )
    if e_spacing is None:
        return None
    
    # Validate lateral spacing
    l_spacing = validator.validate_line_edit(
        lateral_spacing, "Lateral Spacing", min_value=0.1, max_value=10.0, parent=parent
    )
    if l_spacing is None:
        return None
    
    # Check logical constraints
    if e_spacing >= length:
        QMessageBox.warning(
            parent,
            "Invalid Design",
            "Emitter spacing must be less than field length."
        )
        emitter_spacing.setFocus()
        return None
    
    if l_spacing >= width:
        QMessageBox.warning(
            parent,
            "Invalid Design",
            "Lateral spacing must be less than field width."
        )
        lateral_spacing.setFocus()
        return None
    
    return {
        'field_length': length,
        'field_width': width,
        'emitter_spacing': e_spacing,
        'lateral_spacing': l_spacing
    }
