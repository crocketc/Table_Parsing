# 质量检查脚本 (PowerShell 版本)
# 运行 mypy、pytest 和 radon 进行代码质量检查

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "代码质量检查脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查函数
function Check-Command {
    param([string]$Command)

    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        Write-Host "错误: $Command 未安装" -ForegroundColor Red
        Write-Host "请运行: pip install $Command" -ForegroundColor Yellow
        return $false
    }
}

# 检查必要的工具
Write-Host "检查必要的工具..." -ForegroundColor Yellow
$tools = @("mypy", "pytest", "radon")
$allToolsInstalled = $true

foreach ($tool in $tools) {
    if (-not (Check-Command $tool)) {
        $allToolsInstalled = $false
    }
}

if (-not $allToolsInstalled) {
    exit 1
}

Write-Host "✓ 所有工具已安装" -ForegroundColor Green
Write-Host ""

# 1. mypy 类型检查（先使用基本模式）
Write-Host "================================" -ForegroundColor Cyan
Write-Host "1. 运行 mypy 类型检查" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
try {
    mypy src/table_parsing
    Write-Host "✓ mypy 检查通过" -ForegroundColor Green
}
catch {
    Write-Host "✗ mypy 检查失败" -ForegroundColor Red
    Write-Host "注意: 类型错误需要修复，详见上方输出" -ForegroundColor Yellow
    # 不退出，继续其他检查
}
Write-Host ""

# 2. pytest --cov 测试覆盖率检查
Write-Host "================================" -ForegroundColor Cyan
Write-Host "2. 运行 pytest --cov 测试覆盖率检查 (目标: ≥80%)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
try {
    pytest --cov=src/table_parsing --cov-report=term-missing --cov-fail-under=80 tests/
    Write-Host "✓ 测试覆盖率 ≥80%" -ForegroundColor Green
}
catch {
    Write-Host "✗ 测试覆盖率 <80%" -ForegroundColor Red
    Write-Host "注意: 这是严格的质量要求，如果覆盖率不足，请添加更多测试" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 3. radon McCabe 复杂度检查
Write-Host "================================" -ForegroundColor Cyan
Write-Host "3. 运行 radon McCabe 复杂度检查 (目标: ≤10)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
try {
    $result = radon cc src/table_parsing -a --min C 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ McCabe 复杂度检查通过 (所有函数 ≤10)" -ForegroundColor Green
    }
    else {
        Write-Host "✗ 发现高复杂度函数 (>10)" -ForegroundColor Red
        Write-Host "请考虑重构高复杂度的函数" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "✗ radon 检查失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. radon 可维护性指数（可选）
Write-Host "================================" -ForegroundColor Cyan
Write-Host "4. 运行 radon 可维护性指数检查" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
radon mi src/table_parsing
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "✓ 所有质量检查通过！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
