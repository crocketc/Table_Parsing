"""测试 IR 模块无 pandas 依赖

这些测试确保 IR 模块是完全独立的，不依赖 pandas。
这是架构设计的重要约束：IR 是纯 Python 数据结构。
"""

import sys
import subprocess
from pathlib import Path


class TestIRModuleNoPandasImport:
    """测试导入 IR 模块不会导入 pandas"""

    def test_ir_module_no_pandas_import(self):
        """测试导入 table_parsing.ir.model 不会导入 pandas

        这个测试通过在子进程中导入 IR 模块并检查 sys.modules 来验证
        pandas 没有被自动导入。
        """
        # 在子进程中运行导入测试
        test_code = """
import sys

# 导入 IR 模块
from table_parsing.ir import Cell, MediaObject, Sheet, Workbook

# 检查 pandas 是否在 sys.modules 中
pandas_imported = 'pandas' in sys.modules

if pandas_imported:
    # 打印所有 pandas 相关的模块
    pandas_modules = [name for name in sys.modules.keys() if 'pandas' in name.lower()]
    print(f"PANDAS_IMPORTED:{pandas_modules}")
else:
    print("PANDAS_NOT_IMPORTED")
"""

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        # 如果子进程出错，显示错误信息
        if result.returncode != 0:
            pytest_fail = f"子进程执行失败:\nstdout: {output}\nstderr: {stderr}"
            raise AssertionError(pytest_fail)

        # 验证 pandas 没有被导入
        if output.startswith("PANDAS_IMPORTED:"):
            pandas_modules = output.split(":", 1)[1]
            raise AssertionError(
                f"导入 IR 模块时意外导入了 pandas 模块: {pandas_modules}\n"
                f"IR 模块应该是完全独立的，不应该依赖 pandas"
            )

        assert output == "PANDAS_NOT_IMPORTED", (
            f"期望输出 'PANDAS_NOT_IMPORTED'，但得到: {output}"
        )


class TestIRPackageNoPandasRequirement:
    """测试 IR 包可以在没有 pandas 的情况下使用"""

    def test_ir_package_no_pandas_requirement(self):
        """测试 IR 模块的基本功能不依赖 pandas

        这个测试验证即使 pandas 不可用，IR 模块的核心功能仍然工作。
        """
        # 在子进程中模拟 pandas 不可用的情况
        test_code = """
import sys

# 阻止 pandas 导入
class BlockPandasImport:
    def find_spec(self, name, path, target=None):
        if name == 'pandas' or name.startswith('pandas.'):
            raise ImportError(f"Blocked import of {name} (simulating pandas not installed)")
        return None

# 在导入任何模块之前插入导入拦截器
sys.meta_path.insert(0, BlockPandasImport())

# 现在尝试导入和使用 IR 模块
from table_parsing.ir import Cell, MediaObject, Sheet, Workbook

# 测试基本功能
cell = Cell(value="测试", data_type="string")
assert cell.value == "测试"
assert cell.to_dict() == {"value": "测试"}

media = MediaObject(type="image", anchor_row=0, anchor_col=0)
assert media.type == "image"
assert media.to_dict() == {"type": "image", "anchor_row": 0, "anchor_col": 0}

sheet = Sheet(name="测试表")
assert sheet.name == "测试表"
assert sheet.cells == []

workbook = Workbook()
assert workbook.sheets == []
assert workbook.metadata == {}

print("SUCCESS: IR module works without pandas")
"""

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        # 如果子进程出错，显示错误信息
        if result.returncode != 0:
            error_msg = f"IR 模块在无 pandas 环境下执行失败:\nstdout: {output}\nstderr: {stderr}"
            raise AssertionError(error_msg)

        # 验证成功
        assert "SUCCESS: IR module works without pandas" in output, (
            f"期望成功消息，但得到: {output}"
        )

    def test_ir_model_file_content_no_pandas(self):
        """测试 IR 模型源代码文件不包含 pandas 导入

        这是一个静态检查，确保源代码中没有 'import pandas' 或 'from pandas'
        """
        ir_model_path = Path(__file__).parent.parent / "src" / "table_parsing" / "ir" / "model.py"

        if not ir_model_path.exists():
            raise FileNotFoundError(f"IR 模型文件不存在: {ir_model_path}")

        content = ir_model_path.read_text(encoding="utf-8")

        # 检查是否有 pandas 导入
        pandas_imports = [
            "import pandas",
            "import pandas as",
            "from pandas",
            "import pd",
        ]

        found_imports = []
        for imp in pandas_imports:
            if imp in content:
                found_imports.append(imp)

        if found_imports:
            raise AssertionError(
                f"IR 模型文件包含 pandas 导入: {', '.join(found_imports)}\n"
                f"文件路径: {ir_model_path}\n"
                f"IR 模块应该是完全独立的，不应该导入 pandas"
            )

    def test_ir_init_file_content_no_pandas(self):
        """测试 IR __init__.py 源代码文件不包含 pandas 导入"""
        ir_init_path = Path(__file__).parent.parent / "src" / "table_parsing" / "ir" / "__init__.py"

        if not ir_init_path.exists():
            raise FileNotFoundError(f"IR __init__ 文件不存在: {ir_init_path}")

        content = ir_init_path.read_text(encoding="utf-8")

        # 检查是否有 pandas 导入
        pandas_imports = [
            "import pandas",
            "import pandas as",
            "from pandas",
            "import pd",
        ]

        found_imports = []
        for imp in pandas_imports:
            if imp in content:
                found_imports.append(imp)

        if found_imports:
            raise AssertionError(
                f"IR __init__ 文件包含 pandas 导入: {', '.join(found_imports)}\n"
                f"文件路径: {ir_init_path}\n"
                f"IR 模块应该是完全独立的，不应该导入 pandas"
            )
