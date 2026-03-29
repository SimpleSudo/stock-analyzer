#!/usr/bin/env bash
# ============================================================
#  A股智能分析系统 - 一键停止脚本
#  用法: ./stop.sh
# ============================================================
set -euo pipefail

# ── 项目根目录 ──────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"

# ── 颜色定义 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[  OK]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }

# ── 停止单个服务 ────────────────────────────────────────────
stop_service() {
    local name=$1
    local pid_file="$PIDS_DIR/${name}.pid"
    local port=$2

    echo -e "${BOLD}── 停止 $name ──${NC}"

    local stopped=false

    # 方式1: 通过 PID 文件停止
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            # 终止进程及其子进程
            kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
            # 等待进程退出 (最多 5 秒)
            for _ in $(seq 1 5); do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # 如果还在运行，强制终止
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            ok "$name 已停止 (PID: $pid)"
            stopped=true
        else
            info "$name PID $pid 已不在运行"
            stopped=true
        fi
        rm -f "$pid_file"
    fi

    # 方式2: 通过端口查找残留进程
    if [ -n "$port" ]; then
        local pids
        pids=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 1
            # 强制终止残留
            pids=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo "$pids" | xargs kill -9 2>/dev/null || true
            fi
            ok "$name 端口 $port 上的进程已终止"
            stopped=true
        fi
    fi

    if [ "$stopped" = false ]; then
        info "$name 未在运行"
    fi
}

# ── Banner ──────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     📈 A股智能分析系统 - 停止中       ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── 停止服务 ────────────────────────────────────────────────
stop_service "frontend" "5173"
echo ""
stop_service "backend"  "8000"
echo ""

# ── 清理 ────────────────────────────────────────────────────
rmdir "$PIDS_DIR" 2>/dev/null || true

echo -e "${GREEN}${BOLD}  ✅ 所有服务已停止${NC}"
echo ""
