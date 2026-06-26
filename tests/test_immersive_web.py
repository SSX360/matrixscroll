import unittest
from matrixscroll.immersive_web import is_immersive_web_context, build_realism_playbook

class ImmersiveWebTests(unittest.TestCase):
    def test_context_matching(self):
        profile = {"frameworks": ["threejs"], "languages": ["javascript"]}
        self.assertTrue(is_immersive_web_context(profile, "build a WebGL scene"))
        
        profile_plain = {"frameworks": ["django"], "languages": ["python"]}
        self.assertFalse(is_immersive_web_context(profile_plain, "build a blog"))
        
    def test_build_playbook(self):
        playbook = build_realism_playbook({}, "")
        self.assertIn("layers", playbook)
        self.assertGreater(len(playbook["layers"]), 0)
        for layer in playbook["layers"]:
            self.assertIn("layer", layer)
            self.assertIn("build", layer)
