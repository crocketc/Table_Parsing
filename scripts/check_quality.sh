#!/bin/bash
# 质量检查脚本
# 运行 mypy、pytest 和 radon 进行代码质量检查

set -e  # 遇到错误立即退出

echo "================================"
echo "代码质量检查脚本"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}错误: $1 未安装${NC}"
        echo "请运行: pip install $1"
        exit 1
    fi
}

# 检查必要的工具
echo "检查必要的工具..."
check_command mypy
check_command pytest
check_command radon
echo -e "${GREEN}✓ 所有工具已安装${NC}"
echo ""

# 1. mypy 类型检查（先使用基本模式）
echo "================================"
echo "1. 运行 mypy 类型检查"
echo "================================"
if mypy src/table_parsing; then
    echo -e "${GREEN}✓ mypy 检查通过${NC}"
else
    echo -e "${RED}✗ mypy 检查失败${NC}"
    echo "注意: 类型错误需要修复，详见上方输出"
    # 不退出，继续其他检查
fi
echo ""

# 2. pytest --cov 测试覆盖率检查
echo "================================"
echo "2. 运行 pytest --cov 测试覆盖率检查 (目标: ≥80%)"
echo "================================"
if pytest --cov=src/table_parsing --cov-report=term-missing --cov-fail-under=80 tests/; then
    echo -e "${GREEN}✓ 测试覆盖率 ≥80%${NC}"
else
    echo -e "${RED}✗ 测试覆盖率 <80%${NC}"
    echo "注意: 这是严格的质量要求，如果覆盖率不足，请添加更多测试"
    exit 1
fi
echo ""

# 3. radon McCabe 复杂度检查
echo "================================"
echo "3. 运行 radon McCabe 复杂度检查 (目标: ≤10)"
echo "================================"
if radon cc src/table_parsing -a --min C; then
    # radon 返回 0 表示没有超过阈值的复杂度
    echo -e "${GREEN}✓ McCabe 复杂度检查通过 (所有函数 ≤10)${NC}"
else
    echo -e "${RED}✗ 发现高复杂度函数 (>10)${NC}"
    echo "请考虑重构高复杂度的函数"
    exit 1
fi
echo ""

# 4. radon 可维护性指数（可选）
echo "================================"
echo "4. 运行 radon 可维护性指数检查"
echo "================================"
radon mi src/table_parsing
echo ""

echo "================================"
echo -e "${GREEN}✓ 所有质量检查通过！${NC}"
echo "================================"
