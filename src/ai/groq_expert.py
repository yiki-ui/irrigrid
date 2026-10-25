#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Groq AI Integration for Irrigation Design Expert
Provides AI-powered recommendations and analysis for irrigation systems
"""

import os
import urllib.request
import socket
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DesignParameters:
    """Design parameters for AI analysis"""
    system_type: str
    area_ha: float
    crop_type: str
    soil_type: str
    climate_zone: str
    emitter_flow_rate: float
    emitter_spacing: float
    lateral_spacing: float
    water_source: str = "Municipal"
    budget_rwf: Optional[float] = None
    location: str = "Rwanda"


@dataclass
class AIRecommendation:
    """AI recommendation response"""
    recommendation: str
    confidence: float
    reasoning: str
    improvements: List[str]
    warnings: List[str]
    estimated_efficiency: float
    timestamp: datetime


class GroqIrrigationExpert:
    """
    Groq AI-powered irrigation design expert
    Provides intelligent recommendations and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, use_fallback: bool = False):
        """
        Initialize Groq expert
        
        Args:
            api_key: Groq API key (if None, reads from environment)
            use_fallback: If True, uses rule-based fallback instead of AI (default: False)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = "qwen/qwen3.8-27b"  # Fast and accurate model
        self.client = None
        self.use_fallback = use_fallback
        self.last_error = None
        
        if self.api_key and not use_fallback:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                print("✅ Groq AI Expert initialized successfully")
                print(f"   Using model: {self.model}")
            except ImportError:
                print("❌ Groq package not installed. Run: pip install groq")
                self.last_error = "Groq package not installed"
            except Exception as e:
                print(f"❌ Groq initialization failed: {e}")
                self.last_error = str(e)
        elif not self.api_key:
            print("⚠️ No Groq API key found. Set GROQ_API_KEY environment variable.")
            self.last_error = "No API key provided"
        elif use_fallback:
            print("ℹ️ Using rule-based fallback mode (no AI)")
            self.last_error = "Fallback mode enabled"
    
    def is_available(self) -> bool:
        """Check if Groq AI is available"""
        if self.use_fallback:
            return False
        return self.client is not None
    
    def check_internet_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.error, socket.timeout):
            try:
                # Fallback: try to reach a URL
                urllib.request.urlopen('https://www.google.com', timeout=3)
                return True
            except:
                return False
    
    def get_status_message(self) -> str:
        """Get detailed status message"""
        if self.use_fallback:
            return "Using rule-based fallback (AI disabled)"
        elif not self.api_key:
            return "No API key configured"
        elif not self.client:
            return f"Not initialized: {self.last_error}"
        elif not self.check_internet_connection():
            return "No internet connection"
        else:
            return "AI Expert Online"
    
    def analyze_design(self, params: DesignParameters) -> AIRecommendation:
        """
        Analyze irrigation design and provide recommendations
        
        Args:
            params: Design parameters
            
        Returns:
            AI recommendation with analysis
        """
        if not self.is_available():
            print(f"⚠️ AI not available: {self.get_status_message()}")
            if self.use_fallback:
                print("   Using rule-based analysis...")
                return self._fallback_analysis(params)
            else:
                raise Exception(f"AI not available: {self.get_status_message()}. Enable fallback mode or fix AI connection.")
        
        # Check internet connection first
        if not self.check_internet_connection():
            error_msg = "No internet connection detected"
            print(f"❌ {error_msg}")
            if self.use_fallback:
                print("   Using rule-based fallback...")
                return self._fallback_analysis(params)
            else:
                raise Exception(f"{error_msg}. Check your network or enable fallback mode.")
        
        try:
            # Create detailed prompt
            prompt = self._create_analysis_prompt(params)
            
            print("🤖 Calling Groq AI for design analysis...")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent recommendations
                max_tokens=2000,
                top_p=0.9
            )
            
            print("✅ AI response received successfully")
            
            # Parse response
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response, params)
            
        except Exception as e:
            error_msg = f"Groq API error: {str(e)}"
            print(f"❌ {error_msg}")
            self.last_error = error_msg
            
            if self.use_fallback:
                print("   Falling back to rule-based analysis...")
                return self._fallback_analysis(params)
            else:
                raise Exception(f"{error_msg}. Enable fallback mode or fix API connection.")
    
    def get_quick_recommendation(self, question: str, context: Dict[str, Any]) -> str:
        """
        Get quick AI recommendation for specific question
        
        Args:
            question: User's question
            context: Current system context
            
        Returns:
            AI response
        """
        if not self.is_available():
            return f"❌ AI Expert is not available: {self.get_status_message()}\n\nPlease:\n1. Set GROQ_API_KEY environment variable\n2. Check internet connection\n3. Verify Groq package is installed (pip install groq)"
        
        # Check internet
        if not self.check_internet_connection():
            return "❌ No internet connection detected. Please check your network."
        
        try:
            # Detect if this is a greeting or casual message (no technical context needed)
            question_lower = question.lower().strip()
            casual_phrases = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay']
            is_casual = any(phrase in question_lower for phrase in casual_phrases) and len(question_lower) < 30
            
            # Only include system context for technical questions
            if is_casual:
                prompt = question
            else:
                prompt = f"""
Current System Context:
- System Type: {context.get('system_type', 'Drip')}
- Area: {context.get('area', '2.5')} ha
- Crop: {context.get('crop', 'Various')}
- Soil: {context.get('soil', 'Loam')}

User Question: {question}

Provide a helpful, concise answer (max 200 words).
"""
            
            print(f"🤖 Asking Groq AI: {question[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 if is_casual else 0.5,  # More creative for casual, precise for technical
                max_tokens=300 if is_casual else 500
            )
            
            print("✅ AI response received")
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"Error getting recommendation: {str(e)}"
            print(f"❌ {error_msg}")
            self.last_error = error_msg
            return f"❌ {error_msg}\n\nTroubleshooting:\n• Check API key\n• Verify internet connection\n• Ensure Groq service is accessible"
    
    def optimize_parameters(self, params: DesignParameters) -> Dict[str, float]:
        """
        Suggest optimized parameters
        
        Args:
            params: Current design parameters
            
        Returns:
            Dictionary of optimized parameters
        """
        if not self.is_available():
            print(f"⚠️ AI not available: {self.get_status_message()}")
            if self.use_fallback:
                return self._fallback_optimization(params)
            else:
                raise Exception(f"AI not available: {self.get_status_message()}")
        
        if not self.check_internet_connection():
            print("❌ No internet connection")
            if self.use_fallback:
                return self._fallback_optimization(params)
            else:
                raise Exception("No internet connection. Check your network.")
        
        try:
            prompt = f"""
Optimize these irrigation parameters for maximum efficiency:

System: {params.system_type}
Area: {params.area_ha} ha
Crop: {params.crop_type}
Soil: {params.soil_type}
Current flow rate: {params.emitter_flow_rate} L/hr
Current emitter spacing: {params.emitter_spacing} m
Current lateral spacing: {params.lateral_spacing} m

Provide optimized values in this exact format:
FLOW_RATE: [value]
EMITTER_SPACING: [value]
LATERAL_SPACING: [value]
EXPECTED_EFFICIENCY: [percentage]
REASONING: [brief explanation]
"""
            
            print("🤖 Requesting parameter optimization from AI...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            print("✅ Optimization received")
            return self._parse_optimization(response.choices[0].message.content)
            
        except Exception as e:
            error_msg = f"Error optimizing parameters: {str(e)}"
            print(f"❌ {error_msg}")
            self.last_error = error_msg
            
            if self.use_fallback:
                print("   Using rule-based optimization...")
                return self._fallback_optimization(params)
            else:
                raise Exception(error_msg)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI expert"""
        return """You are a friendly and expert irrigation engineer specializing in drip, sprinkler, and surface irrigation systems for African agriculture, particularly Rwanda.

IMPORTANT: First, determine if the user is:
1. Greeting you (hi, hello, thanks) - Respond warmly and briefly
2. Making small talk - Engage naturally and steer toward irrigation topics
3. Asking an irrigation question - Provide detailed technical advice

Your expertise includes:
- Irrigation system design and optimization
- Water use efficiency and conservation
- Crop water requirements
- Soil-water-plant relationships
- Climate adaptation strategies
- Cost-benefit analysis
- Sustainable farming practices

When answering irrigation questions, provide practical recommendations based on:
- FAO guidelines for irrigation
- Local climate conditions in Rwanda
- Soil characteristics
- Crop requirements
- Economic feasibility
- Water availability

Always consider:
- Water scarcity and conservation
- Farmer budget constraints
- Local materials availability
- Maintenance requirements
- Long-term sustainability

Be conversational, helpful, and encouraging. If someone greets you, greet them back warmly before offering help with irrigation questions."""
    
    def _create_analysis_prompt(self, params: DesignParameters) -> str:
        """Create detailed analysis prompt"""
        return f"""
Analyze this irrigation system design:

SYSTEM SPECIFICATIONS:
- Type: {params.system_type}
- Area: {params.area_ha} hectares
- Location: {params.location}
- Climate Zone: {params.climate_zone}

CROP & SOIL:
- Crop Type: {params.crop_type}
- Soil Type: {params.soil_type}

DESIGN PARAMETERS:
- Emitter Flow Rate: {params.emitter_flow_rate} L/hr
- Emitter Spacing: {params.emitter_spacing} m
- Lateral Spacing: {params.lateral_spacing} m
- Water Source: {params.water_source}
{f"- Budget: {params.budget_rwf:,.0f} RWF" if params.budget_rwf else ""}

ANALYSIS REQUIRED:
1. Overall design assessment (Good/Fair/Poor)
2. Key strengths of this design
3. Potential improvements (3-5 specific suggestions)
4. Warnings or concerns (if any)
5. Estimated water use efficiency (percentage)
6. Cost-effectiveness rating

Provide detailed, practical recommendations for a Rwandan farmer.
"""
    
    def _parse_ai_response(self, response: str, params: DesignParameters) -> AIRecommendation:
        """Parse AI response into structured recommendation"""
        lines = response.split('\n')
        
        # Extract key information (simple parsing)
        recommendation = response[:500] if len(response) > 500 else response
        improvements = []
        warnings = []
        
        for line in lines:
            line_lower = line.lower()
            if 'improvement' in line_lower or 'suggest' in line_lower or 'recommend' in line_lower:
                improvements.append(line.strip('- •*'))
            elif 'warning' in line_lower or 'concern' in line_lower or 'issue' in line_lower:
                warnings.append(line.strip('- •*'))
        
        # Estimate confidence and efficiency from response
        confidence = 0.85 if 'good' in response.lower() else 0.70
        efficiency = 85.0  # Default, could be extracted from response
        
        return AIRecommendation(
            recommendation=recommendation,
            confidence=confidence,
            reasoning=response,
            improvements=improvements[:5] if improvements else ["No specific improvements suggested"],
            warnings=warnings[:3] if warnings else [],
            estimated_efficiency=efficiency,
            timestamp=datetime.now()
        )
    
    def _parse_optimization(self, response: str) -> Dict[str, float]:
        """Parse optimization response"""
        optimized = {}
        
        try:
            for line in response.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'flow_rate' in key:
                        optimized['flow_rate'] = float(value.split()[0])
                    elif 'emitter_spacing' in key:
                        optimized['emitter_spacing'] = float(value.split()[0])
                    elif 'lateral_spacing' in key:
                        optimized['lateral_spacing'] = float(value.split()[0])
                    elif 'efficiency' in key:
                        optimized['efficiency'] = float(value.split()[0])
        except:
            pass
        
        return optimized
    
    def _fallback_analysis(self, params: DesignParameters) -> AIRecommendation:
        """Fallback analysis when AI is not available"""
        # Rule-based recommendations
        improvements = []
        warnings = []
        efficiency = 75.0
        
        # Check spacing
        if params.system_type == "Drip":
            if params.emitter_spacing > 0.5:
                improvements.append("Consider reducing emitter spacing to 0.3-0.4m for better coverage")
            if params.emitter_spacing < 0.2:
                warnings.append("Emitter spacing might be too close, increasing costs")
            efficiency = 85.0
        
        # Check flow rate
        if params.emitter_flow_rate < 1.5:
            warnings.append("Low flow rate may cause clogging issues")
        elif params.emitter_flow_rate > 4.0:
            warnings.append("High flow rate may cause runoff")
        
        # Area considerations
        if params.area_ha > 5:
            improvements.append("Consider zone-based irrigation for better control")
        
        recommendation = f"""
Design Assessment: {"Good" if not warnings else "Fair"}

Your {params.system_type} system for {params.area_ha} ha shows {"promising" if not warnings else "acceptable"} characteristics.

Key Points:
- System type is appropriate for {params.crop_type}
- {params.soil_type} soil requires careful water management
- Current spacing: {params.emitter_spacing}m × {params.lateral_spacing}m

Estimated Efficiency: {efficiency}%
"""
        
        if not improvements:
            improvements = [
                "Monitor soil moisture regularly",
                "Implement filtration system",
                "Schedule maintenance checks"
            ]
        
        return AIRecommendation(
            recommendation=recommendation,
            confidence=0.75,
            reasoning="Rule-based analysis (AI not available)",
            improvements=improvements,
            warnings=warnings if warnings else ["No major concerns"],
            estimated_efficiency=efficiency,
            timestamp=datetime.now()
        )
    
    def _fallback_optimization(self, params: DesignParameters) -> Dict[str, float]:
        """Fallback optimization when AI is not available"""
        # Rule-based optimization
        optimized = {
            'flow_rate': params.emitter_flow_rate,
            'emitter_spacing': params.emitter_spacing,
            'lateral_spacing': params.lateral_spacing,
            'efficiency': 80.0
        }
        
        # Optimize based on system type
        if params.system_type == "Drip":
            optimized['flow_rate'] = 2.0
            optimized['emitter_spacing'] = 0.3
            optimized['lateral_spacing'] = 1.2
            optimized['efficiency'] = 85.0
        elif params.system_type == "Sprinkler":
            optimized['flow_rate'] = 150.0
            optimized['emitter_spacing'] = 12.0
            optimized['lateral_spacing'] = 18.0
            optimized['efficiency'] = 75.0
        
        return optimized


# Convenience function
def create_groq_expert(api_key: Optional[str] = None) -> GroqIrrigationExpert:
    """Create and return Groq expert instance"""
    return GroqIrrigationExpert(api_key=api_key)
