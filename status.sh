#!/usr/bin/env bash
# ============================================================
#  A股智能分析系统 - 服务状态查看
#  用法: ./status.sh
# ============================================================
set -euo pipefail

# ── 项目根目录 ──────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"

# ── 颜色定义 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── 检查单个服务状态 ────────────────────────────────────────
check_service() {
    local name=$1
    local port=$2
    local pid_file="$PIDS_DIR/${name}.pid"
    local status_icon=""
    local status_text=""
    local pid_info=""

    # 检查 PID 文件
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            pid_info="PID: $pid"
        else
            pid_info="PID: $pid (已退出)"
        fi
    fi

    # 检查端口
    local port_pids
    port_pids=$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
    if [ -n "$port_pids" ]; then
        status_icon="${GREEN}●${NC}"
        status_text="${GREEN}运行中${NC}"
        if [ -z "$pid_info" ]; then
            pid_info="PID: $port_pids"
        fi
    else
        status_icon="${RED}●${NC}"
        status_text="${RED}已停止${NC}"
    fi

    printf "  %b %-12s %b  端口: %-6s  %s\n" "$status_icon" "$name" "$status_text" "$port" "$pid_info"
}

# ── Banner ──────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║     📈 A股智能分析系统 - 服务状态     ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

check_service "backend"  "8000"
check_service "frontend" "5173"

echo ""
echo -e "  ${BOLD}快捷命令:${NC}"
echo "    启动: ./start.sh"
echo "    停止: ./stop.sh"
echo ""
