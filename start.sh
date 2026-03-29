#!/usr/bin/env bash
# ============================================================
#  A股智能分析系统 - 一键启动脚本
#  用法: ./start.sh
# ============================================================
set -euo pipefail

# ── 项目根目录 ──────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"
LOGS_DIR="$PROJECT_DIR/logs"

# ── 颜色定义 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[  OK]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }

# ── 创建必要目录 ────────────────────────────────────────────
mkdir -p "$PIDS_DIR" "$LOGS_DIR"

# ── 端口检测 ────────────────────────────────────────────────
check_port() {
    local port=$1
    if lsof -iTCP:"$port" -sTCP:LISTEN -t &>/dev/null; then
        return 0  # 端口被占用
    fi
    return 1  # 端口空闲
}

# ── Banner ──────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     📈 A股智能分析系统 - 启动中       ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
#  1. 启动后端 (FastAPI + Uvicorn)
# ============================================================
echo -e "${BOLD}── 后端服务 (FastAPI) ──${NC}"

if check_port 8000; then
    warn "端口 8000 已被占用，跳过后端启动"
    warn "如需重启，请先运行 ./stop.sh"
else
    # 查找可用的虚拟环境（优先 .venv，其次 backend/venv）
    if [ -f "$PROJECT_DIR/.venv/bin/python3" ]; then
        VENV_DIR="$PROJECT_DIR/.venv"
    elif [ -f "$PROJECT_DIR/backend/venv/bin/python3" ]; then
        VENV_DIR="$PROJECT_DIR/backend/venv"
    else
        fail "未找到虚拟环境 (.venv 或 backend/venv)"
        info "请先执行: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"
        exit 1
    fi

    PYTHON="$VENV_DIR/bin/python3"
    info "使用虚拟环境: $VENV_DIR"
    info "启动后端服务..."
    (
        cd "$PROJECT_DIR/backend"
        export PYTHONPATH="$PROJECT_DIR/backend"
        nohup "$PYTHON" -m uvicorn src.main:app --host 0.0.0.0 --port 8000 \
            >> "$LOGS_DIR/backend.log" 2>&1 &
        echo $! > "$PIDS_DIR/backend.pid"
    )

    # 等待后端就绪 (最多 30 秒，模型加载可能较慢)
    info "等待后端服务就绪 (首次启动需加载AI模型，请耐心等待)..."
    for i in $(seq 1 30); do
        if check_port 8000; then
            ok "后端已启动  PID=$(cat "$PIDS_DIR/backend.pid")  http://localhost:8000"
            break
        fi
        sleep 1
        if [ "$i" -eq 30 ]; then
            warn "后端启动超时 (30s)，模型加载中可能仍在启动，请稍后执行 ./status.sh 检查"
            warn "日志: $LOGS_DIR/backend.log"
        fi
    done
fi

echo ""

# ============================================================
#  2. 启动前端 (Vite Dev Server)
# ============================================================
echo -e "${BOLD}── 前端服务 (Vite + React) ──${NC}"

if check_port 5173; then
    warn "端口 5173 已被占用，跳过前端启动"
    warn "如需重启，请先运行 ./stop.sh"
else
    # 检查 node_modules
    if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
        info "未检测到 node_modules，正在安装依赖..."
        (cd "$PROJECT_DIR/frontend" && npm install)
    fi

    info "启动前端服务..."
    (
        cd "$PROJECT_DIR/frontend"
        nohup npm run dev >> "$LOGS_DIR/frontend.log" 2>&1 &
        echo $! > "$PIDS_DIR/frontend.pid"
    )

    # 等待前端就绪 (最多 15 秒)
    info "等待前端服务就绪..."
    for i in $(seq 1 15); do
        if check_port 5173; then
            ok "前端已启动  PID=$(cat "$PIDS_DIR/frontend.pid")  http://localhost:5173"
            break
        fi
        sleep 1
        if [ "$i" -eq 15 ]; then
            warn "前端启动超时，请检查日志: $LOGS_DIR/frontend.log"
        fi
    done
fi

echo ""

# ============================================================
#  3. 启动完成
# ============================================================
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║          ✅ 启动完成!                 ║"
echo "  ╠═══════════════════════════════════════╣"
echo "  ║  前端地址: http://localhost:5173      ║"
echo "  ║  后端API:  http://localhost:8000      ║"
echo "  ║  API文档:  http://localhost:8000/docs ║"
echo "  ╠═══════════════════════════════════════╣"
echo "  ║  停止服务: ./stop.sh                  ║"
echo "  ║  查看状态: ./status.sh                ║"
echo "  ║  后端日志: logs/backend.log           ║"
echo "  ║  前端日志: logs/frontend.log          ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"
