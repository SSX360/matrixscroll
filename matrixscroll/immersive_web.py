"""Immersive WebGL and WebXR context matching and playbooks for Digital Rain."""

from __future__ import annotations
from typing import Any

def is_immersive_web_context(profile: dict[str, Any], goal: str) -> bool:
    goal_low = goal.lower()
    signals = {str(v).lower() for v in profile.get("signals") or []}
    frameworks = {str(v).lower() for v in profile.get("frameworks") or []}
    
    three_context = (
        "threejs" in frameworks
        or "webgl" in frameworks
        or "three.js" in goal_low
        or "webgl" in goal_low
        or "shader" in goal_low
        or "immersive" in goal_low
        or "realism" in goal_low
        or "3d" in goal_low
    )
    return three_context

def build_realism_playbook(profile: dict[str, Any], goal: str) -> dict[str, Any]:
    return {
        "layers": [
            {
                "layer": "Environment & Void Setup",
                "build": [
                    "Scaffold a dark void using CSS background: #000000 or custom skybox.",
                    "Initialize Three.js WebGLRenderer with antialias and alpha=true.",
                    "Configure PerspectiveCamera and OrbitControls."
                ]
            },
            {
                "layer": "Materials & Shader Motion",
                "build": [
                    "Implement a custom ShaderMaterial with a uTime uniform loop.",
                    "Use PBR MeshStandardMaterial with metallic and roughness parameters.",
                    "Animate portal vertices or particle stars in the requestAnimationFrame loop."
                ]
            },
            {
                "layer": "Post-Processing & Bloom effects",
                "build": [
                    "Setup EffectComposer to chain render passes.",
                    "Add UnrealBloomPass with high threshold, strength=1.5, and radius=0.4.",
                    "Verify performance is constant at 60fps."
                ]
            }
        ]
    }
