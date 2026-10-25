#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agentic AI Expert for Irrigation Design
Uses Groq function calling to interact with PyQt5 UI
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.ai.function_registry import (
    get_function_definitions_for_groq,
    get_function_descriptions_text,
    get_function_by_name
)


class AgenticIrrigationExpert:
    """
    AI agent that can chat and call UI functions via Groq function calling.
    
    The agent decides autonomously when to:
    - Answer questions directly (chat only)
    - Call UI functions to interact with the application
    """
    
    def __init__(self, api_key: Optional[str] = None, main_window=None):
        """
        Initialize agentic expert.
        
        Args:
            api_key: Groq API key (if None, reads from environment)
            main_window: Reference to MainWindow for calling UI methods
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = "qwen/qwen3.8-27b"
        self.client = None
        self.main_window = main_window
        self.conversation_history: List[Dict[str, str]] = []
        self.last_error = None
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                print("✅ Agentic AI Expert initialized successfully")
                print(f"   Using model: {self.model}")
            except ImportError:
                print("❌ Groq package not installed. Run: pip install groq")
                self.last_error = "Groq package not installed"
            except Exception as e:
                print(f"❌ Groq initialization failed: {e}")
                self.last_error = str(e)
        else:
            print("⚠️ No Groq API key found. Set GROQ_API_KEY environment variable.")
            self.last_error = "No API key provided"
    
    def is_available(self) -> bool:
        """Check if Groq AI is available"""
        return self.client is not None
    
    def chat(self, user_message: str) -> str:
        """
        Process user message. AI decides to chat or call functions.
        
        Args:
            user_message: User's message
            
        Returns:
            AI response (may include function call results)
        """
        if not self.is_available():
            return "❌ AI not available. Please set GROQ_API_KEY environment variable."
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Build system prompt with current UI state
        system_prompt = self._build_system_prompt()
        
        try:
            # Call Groq with function definitions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *self.conversation_history
                ],
                tools=get_function_definitions_for_groq(),
                tool_choice="auto",  # Let LLM decide when to call functions
                max_tokens=1024,
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            # Check if LLM wants to call functions
            if message.tool_calls:
                return self._execute_tool_calls(message.tool_calls)
            else:
                # Just chat response
                ai_response = message.content
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                return ai_response
                
        except Exception as e:
            error_msg = f"❌ AI error: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _execute_tool_calls(self, tool_calls) -> str:
        """
        Execute function calls on the PyQt5 UI.
        
        Args:
            tool_calls: List of tool calls from Groq
            
        Returns:
            Formatted results string
        """
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                results.append(f"❌ {function_name}: Invalid arguments JSON")
                continue
            
            # Find function definition
            func_def = get_function_by_name(function_name)
            if not func_def:
                results.append(f"❌ {function_name}: Function not found")
                continue
            
            # Get UI method name
            ui_method_name = func_def.get("ui_method")
            if not ui_method_name:
                results.append(f"❌ {function_name}: No UI method mapped")
                continue
            
            # Call the method on main window
            if self.main_window and hasattr(self.main_window, ui_method_name):
                try:
                    method = getattr(self.main_window, ui_method_name)
                    result = method(**arguments)
                    results.append(f"✅ {function_name}: {result}")
                except Exception as e:
                    results.append(f"❌ {function_name}: {str(e)}")
            else:
                results.append(f"❌ {function_name}: UI method '{ui_method_name}' not found")
        
        # Add function results to conversation
        result_text = "\n".join(results)
        self.conversation_history.append({"role": "tool", "content": result_text})
        
        # Get AI's response after function execution
        try:
            system_prompt = self._build_system_prompt()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *self.conversation_history
                ],
                max_tokens=512,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
            
        except Exception as e:
            return f"{result_text}\n\n❌ Error getting AI response: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt with available functions and current UI state.
        
        Returns:
            Formatted system prompt
        """
        # Get current UI state
        ui_state = self._get_ui_state()
        
        prompt = f"""You are an expert irrigation design assistant for Rwanda.

You can:
1. Answer questions about irrigation design, crops, soil, climate, and hydraulics
2. Call functions to interact with the UI when needed

AVAILABLE FUNCTIONS:
{get_function_descriptions_text()}

CURRENT UI STATE:
{json.dumps(ui_state, indent=2)}

RULES:
- If user asks a question → answer directly (no function call)
- If user wants to change something in UI → call the appropriate function
- If user wants to see something → call visualization functions
- Always explain what you're doing when calling functions
- Be concise and helpful
- Use the current UI state to provide context-aware responses
- If a function call fails, explain what went wrong and suggest alternatives

EXAMPLES:
- "Set location to Kigali" → call set_location(province="Kigali", district="Nyarugenge")
- "Show me the slope" → call toggle_slope_heatmap(enabled=true)
- "What crop is best?" → answer directly without function call
- "Calculate design" → call run_design_calculation()
"""
        return prompt
    
    def _get_ui_state(self) -> Dict[str, Any]:
        """
        Get current UI state from MainWindow.
        
        Returns:
            Dictionary with current UI state
        """
        if not self.main_window:
            return {"error": "No main window reference"}
        
        try:
            # Try to get state via dedicated method
            if hasattr(self.main_window, 'get_state_for_ai'):
                return self.main_window.get_state_for_ai()
            
            # Fallback: extract state from widgets
            state = {}
            
            # Location
            if hasattr(self.main_window, 'province_combo'):
                state['location'] = {
                    'province': self.main_window.province_combo.currentText(),
                    'district': self.main_window.district_combo.currentText() if hasattr(self.main_window, 'district_combo') else ''
                }
            
            # Crop
            if hasattr(self.main_window, 'crop_type'):
                state['crop'] = self.main_window.crop_type.currentText()
            
            # Area
            if hasattr(self.main_window, 'field_area'):
                try:
                    state['area_ha'] = float(self.main_window.field_area.text())
                except ValueError:
                    state['area_ha'] = None
            
            # Soil
            if hasattr(self.main_window, 'soil_type'):
                state['soil_type'] = self.main_window.soil_type.currentText()
            
            # Water source
            if hasattr(self.main_window, 'water_source'):
                state['water_source'] = self.main_window.water_source.currentText()
            
            # Terrain
            if hasattr(self.main_window, '_terrain_slope'):
                state['terrain_slope'] = self.main_window._terrain_slope
            
            return state
            
        except Exception as e:
            return {"error": f"Failed to get UI state: {str(e)}"}
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🗑️ Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()
