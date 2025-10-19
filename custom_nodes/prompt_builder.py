"""
PromptBuilder - Construct structured rendering prompts from FactsV3 + CCJ

This node combines:
1. FactsV3 garment description
2. CCJ Core Contract (mandatory specs)
3. CCJ Rendering Hints (soft guidance)
4. System prompt template

Output: Final text prompt ready for image generation models
"""

import json
import os
from typing import Dict, Any, Optional


class PromptBuilder:
    """
    ComfyUI custom node for building structured rendering prompts.
    
    Combines garment facts with CCJ contract to create deterministic,
    high-quality prompts for ghost mannequin generation.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "facts_description": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "facts_dict": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
                "ccj_path": ("STRING", {
                    "default": "input/test_ccj_controlblock.json",
                    "multiline": False
                })
            },
            "optional": {
                "custom_additions": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "include_chinese": ("BOOLEAN", {
                    "default": True
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("final_prompt", "core_contract", "rendering_hints")
    FUNCTION = "build_prompt"
    CATEGORY = "photostudio/prompting"
    
    def build_prompt(
        self,
        facts_description: str,
        facts_dict: str,
        ccj_path: str,
        custom_additions: str = "",
        include_chinese: bool = True
    ) -> tuple[str, str, str]:
        """
        Build the final rendering prompt.
        
        Args:
            facts_description: Concise garment description from LoadFactsNode
            facts_dict: Full FactsV3 dictionary
            ccj_path: Path to CCJ ControlBlock JSON
            custom_additions: Optional user prompt additions
            include_chinese: Include Chinese ghost mannequin terms for Seedream
            
        Returns:
            Tuple of (final_prompt, core_contract_text, rendering_hints_text)
        """
        # Load CCJ
        ccj = self._load_ccj(ccj_path)
        
        # Extract components
        core = ccj.get("core_contract", {})
        hints = ccj.get("rendering_hints", {})
        
        # Build core contract text
        core_text = self._build_core_contract(core)
        
        # Build rendering hints text
        hints_text = self._build_rendering_hints(hints)
        
        # Parse facts_dict if it's a string
        parsed_facts = facts_dict
        if isinstance(facts_dict, str):
            try:
                parsed_facts = json.loads(facts_dict)
            except json.JSONDecodeError:
                parsed_facts = {}  # Fallback to empty dict
        
        # Build ghost mannequin specification
        ghost_spec = self._build_ghost_mannequin_spec(parsed_facts, core, include_chinese)
        
        # Combine into final prompt
        final_prompt = self._assemble_final_prompt(
            facts_description=facts_description,
            ghost_spec=ghost_spec,
            core_contract=core_text,
            rendering_hints=hints_text,
            custom_additions=custom_additions
        )
        
        return (final_prompt, core_text, hints_text)
    
    def _load_ccj(self, ccj_path: str) -> Dict[str, Any]:
        """Load CCJ ControlBlock JSON."""
        if not os.path.isabs(ccj_path):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ccj_path = os.path.join(base_path, ccj_path)
        
        with open(ccj_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_core_contract(self, core: Dict[str, Any]) -> str:
        """Build core contract text from CCJ."""
        mandatory = core.get("mandatory_specs", {})
        forbidden = core.get("forbidden_elements", [])
        
        lines = ["CORE CONTRACT (MANDATORY):"]
        
        # Background specs
        bg = mandatory.get("background", {})
        if bg:
            lines.append(f"- Background: {bg.get('color', '#FFFFFF')}, {bg.get('type', 'solid')}")
            lines.append(f"- Edge treatment: {bg.get('edge_treatment', 'clean alpha')}")
        
        # Silhouette specs
        silhouette = mandatory.get("silhouette", {})
        if silhouette:
            lines.append(f"- Garment type: {silhouette.get('garment_type', 'unknown')}")
            lines.append(f"- Fit: {silhouette.get('fit', 'natural')}")
            lines.append(f"- Symmetry: {silhouette.get('symmetry', 'bilateral')}")
        
        # Interior rendering
        interior = mandatory.get("interior_rendering", {})
        if interior:
            visible_parts = []
            if interior.get("neckline_visible"):
                visible_parts.append("neckline")
            if interior.get("cuff_visible"):
                visible_parts.append("cuffs")
            if interior.get("hem_visible"):
                visible_parts.append("hem")
            if visible_parts:
                lines.append(f"- Interior visible: {', '.join(visible_parts)}")
        
        # Color accuracy
        color = mandatory.get("color_accuracy", {})
        if color:
            lines.append(f"- Color: {color.get('primary_hex', '#000000')} (ΔE ≤ {color.get('delta_e_max', 2.0)})")
        
        # Resolution
        resolution = mandatory.get("resolution", {})
        if resolution:
            w = resolution.get("min_width", 2048)
            h = resolution.get("min_height", 2048)
            lines.append(f"- Resolution: {w}x{h}px minimum")
        
        # Forbidden elements
        if forbidden:
            lines.append(f"- FORBIDDEN: {', '.join(forbidden)}")
        
        return "\n".join(lines)
    
    def _build_rendering_hints(self, hints: Dict[str, Any]) -> str:
        """Build rendering hints text from CCJ."""
        lines = ["RENDERING HINTS (GUIDANCE):"]
        
        # Lighting
        lighting = hints.get("lighting", {})
        if lighting:
            lines.append(f"- Lighting setup: {lighting.get('setup', 'three-point studio')}")
            lines.append(f"- Key light: {lighting.get('key_light', 'soft 45-degree')}")
            lines.append(f"- Shadows: {lighting.get('shadows', 'soft contact only')}")
        
        # Fabric behavior
        fabric = hints.get("fabric_behavior", {})
        if fabric:
            lines.append(f"- Material: {fabric.get('material_type', 'unknown')}")
            lines.append(f"- Drape: {fabric.get('drape_weight', 'natural')}")
            lines.append(f"- Texture visibility: {fabric.get('texture_visibility', 'clear')}")
        
        # Critical details
        critical = hints.get("critical_details", {})
        if critical:
            preserve = critical.get("preserve", [])
            if preserve:
                lines.append(f"- Preserve: {', '.join(preserve)}")
            
            enhance = critical.get("enhance", [])
            if enhance:
                lines.append(f"- Enhance: {', '.join(enhance)}")
            
            avoid = critical.get("avoid", [])
            if avoid:
                lines.append(f"- Avoid: {', '.join(avoid)}")
        
        return "\n".join(lines)
    
    def _build_ghost_mannequin_spec(
        self,
        facts: Dict[str, Any],
        core: Dict[str, Any],
        include_chinese: bool
    ) -> str:
        """Build ghost mannequin specification with optional Chinese terms."""
        lines = ["GHOST MANNEQUIN SPECIFICATION:"]
        
        # Get ghost mannequin requirements from facts
        ghost_req = facts.get("ghost_mannequin_requirements", {})
        
        # Primary instruction
        lines.append("- Create professional ghost mannequin effect (invisible mannequin)")
        
        if include_chinese:
            lines.append("- 隐形人台效果 (yǐnxíng réntái xiàoguǒ)")
            lines.append("- 空心人效果 with natural garment volume")
        
        # Interior visibility
        if ghost_req.get("interior_visibility_needed"):
            lines.append("- Interior neck/cuff openings must be clearly visible")
            lines.append("- Show hollow interior depth with subtle shadows")
        
        # Volume preservation
        volume = ghost_req.get("volume_preservation", "high")
        lines.append(f"- Volume preservation: {volume}")
        
        # Drape
        if ghost_req.get("drape_natural"):
            lines.append("- Natural fabric drape and fall")
        
        # Symmetry
        if ghost_req.get("symmetry_critical"):
            lines.append("- Bilateral symmetry critical - perfect left-right alignment")
        
        # Edge precision
        edge = ghost_req.get("edge_precision", "high")
        lines.append(f"- Edge precision: {edge} (no halos, clean alpha)")
        
        # Rendering hints from facts
        rendering = facts.get("rendering_hints", {})
        if rendering:
            behavior = rendering.get("fabric_behavior")
            if behavior:
                lines.append(f"- Fabric behavior: {behavior}")
            
            critical = rendering.get("critical_features", [])
            if critical:
                lines.append(f"- Critical features: {', '.join(critical)}")
        
        return "\n".join(lines)
    
    def _assemble_final_prompt(
        self,
        facts_description: str,
        ghost_spec: str,
        core_contract: str,
        rendering_hints: str,
        custom_additions: str
    ) -> str:
        """Assemble all components into final prompt."""
        
        # System instruction
        system = """Professional product photography for fashion e-commerce.
Generate a high-fidelity ghost mannequin image that looks like a professional studio shoot.
Follow all specifications exactly."""
        
        # Build sections
        sections = [
            "=== SYSTEM ===",
            system,
            "",
            "=== GARMENT ===",
            facts_description,
            "",
            "=== " + "=" * 40,
            ghost_spec,
            "",
            "=== " + "=" * 40,
            core_contract,
            "",
            "=== " + "=" * 40,
            rendering_hints,
        ]
        
        # Add custom additions if provided
        if custom_additions.strip():
            sections.extend([
                "",
                "=== CUSTOM ADDITIONS ===",
                custom_additions.strip()
            ])
        
        # Add technical footer
        sections.extend([
            "",
            "=== TECHNICAL ===",
            "- Style: IMG_2094.CR2 (DSLR quality, sharp, professional)",
            "- Output: Pure white background, clean alpha edges",
            "- Quality: Production-ready, marketplace-compliant",
            "",
            "Render now with maximum fidelity to specifications."
        ])
        
        return "\n".join(sections)
    
    @classmethod
    def IS_CHANGED(cls, facts_description, facts_dict, ccj_path, custom_additions="", include_chinese=True):
        """Force re-evaluation if CCJ file changes."""
        if os.path.isfile(ccj_path):
            return os.path.getmtime(ccj_path)
        return float("nan")


# ComfyUI node registration
NODE_CLASS_MAPPINGS = {
    "PromptBuilder": PromptBuilder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptBuilder": "Build Render Prompt 🏗️"
}