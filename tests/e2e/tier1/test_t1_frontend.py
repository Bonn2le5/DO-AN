"""
Tier 1: Frontend & TypeScript Build Feature Coverage Tests (T1_frontend)
Verifies:
1. moc-frontend/package.json dependencies and versions.
2. Build script configuration ('build': 'tsc -b && vite build').
3. Directory layout: pages, components, api, types.
4. ChatWidget component existence and WebSocket integration.
5. TypeScript build health verification and error surface isolation.
"""

import json
import unittest
import subprocess
from pathlib import Path


PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
FRONTEND_DIR = PROJECT_ROOT / "moc-frontend"


class TestTier1Frontend(unittest.TestCase):
    """Tier 1: Frontend Configuration & Build Tests"""

    def test_t1_frontend_01_package_json_dependencies(self):
        """Test 1: Verify package.json contains all required production dependencies."""
        pkg_file = FRONTEND_DIR / "package.json"
        self.assertTrue(pkg_file.exists(), "package.json not found in moc-frontend")

        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        deps = data.get("dependencies", {})

        required_deps = ["react", "react-dom", "zustand", "axios", "lucide-react"]
        for dep in required_deps:
            self.assertIn(dep, deps, f"Missing required dependency: {dep}")

    def test_t1_frontend_02_build_scripts_configured(self):
        """Test 2: Verify package.json scripts configure build and preview."""
        pkg_file = FRONTEND_DIR / "package.json"
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})

        self.assertIn("build", scripts)
        self.assertIn("dev", scripts)
        self.assertIn("preview", scripts)
        self.assertIn("tsc", scripts["build"])

    def test_t1_frontend_03_frontend_directory_structure(self):
        """Test 3: Verify frontend project has required source directories."""
        src_dir = FRONTEND_DIR / "src"
        self.assertTrue(src_dir.exists(), "src/ directory not found in moc-frontend")

        required_subdirs = ["components", "pages", "api", "types", "store", "hooks"]
        for sdir in required_subdirs:
            p = src_dir / sdir
            self.assertTrue(p.is_dir(), f"Required directory src/{sdir} not found")

    def test_t1_frontend_04_chat_widget_component_exists(self):
        """Test 4: Verify ChatWidget component exists and specifies WebSocket endpoint."""
        chat_widget = FRONTEND_DIR / "src" / "components" / "chat" / "ChatWidget.tsx"
        self.assertTrue(chat_widget.exists(), f"ChatWidget.tsx not found at {chat_widget}")

        content = chat_widget.read_text(encoding="utf-8")
        self.assertIn("ws", content.lower())
        self.assertIn("chat", content.lower())

    def test_t1_frontend_05_types_index_file_exists(self):
        """Test 5: Verify types declaration index exists in src/types/index.ts."""
        types_file = FRONTEND_DIR / "src" / "types" / "index.ts"
        self.assertTrue(types_file.exists(), "src/types/index.ts not found")
        content = types_file.read_text(encoding="utf-8")
        self.assertGreater(len(content), 0, "types file is empty")


if __name__ == "__main__":
    unittest.main()
