#!/usr/bin/env bash
# End-to-end pipeline test for delta-squad-project.
# Usage:
#   ./test_e2e.sh           # run tests, leave services running
#   ./test_e2e.sh --cleanup # tear down services after tests

set -uo pipefail

# -------------------------------------------------
# Colours
# -------------------------------------------------
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSES=$((PASSES+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILS=$((FAILS+1)); }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

PASSES=0; FAILS=0
CLEANUP=false
[[ "${1:-}" == "--cleanup" ]] && CLEANUP=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"
EXEC_ENV="$SCRIPT_DIR/service/execution_service/.env"

KAFKA_READY_TIMEOUT=90     # seconds to wait for Kafka
PIPELINE_TIMEOUT=120       # seconds to wait for each pipeline stage

echo ""
echo "================================================"
echo "  Delta Squad — End-to-End Pipeline Test"
echo "================================================"
echo ""

# -------------------------------------------------
# 1. Prerequisites
# -------------------------------------------------
info "Checking prerequisites..."

if ! command -v docker &>/dev/null; then
    fail "Docker not installed"; exit 1
fi
if ! docker info &>/dev/null 2>&1; then
    fail "Docker daemon is not running"; exit 1
fi
if [ ! -f "$EXEC_ENV" ]; then
    fail "Missing $EXEC_ENV — create it with BINANCE_API_KEY and BINANCE_API_SECRET"; exit 1
fi
if ! grep -q "BINANCE_API_KEY" "$EXEC_ENV" || ! grep -q "BINANCE_API_SECRET" "$EXEC_ENV"; then
    fail "$EXEC_ENV is missing BINANCE_API_KEY or BINANCE_API_SECRET"; exit 1
fi
if grep -qE "BINANCE_API_(KEY|SECRET)=$" "$EXEC_ENV"; then
    fail "$EXEC_ENV has empty API key or secret — paste your Binance testnet credentials"; exit 1
fi
pass "Prerequisites OK"

# -------------------------------------------------
# 2. Start services
# -------------------------------------------------
info "Starting services (this may take a minute for Docker builds)..."
cd "$INFRA_DIR"
docker compose down --remove-orphans 2>/dev/null || true
docker compose up --build -d
echo ""

# -------------------------------------------------
# 3. Wait for Kafka
# -------------------------------------------------
info "Waiting for Kafka to be ready (up to ${KAFKA_READY_TIMEOUT}s)..."
DEADLINE=$((SECONDS + KAFKA_READY_TIMEOUT))
until docker exec kafka /opt/kafka/bin/kafka-topics.sh \
        --bootstrap-server localhost:9092 --list &>/dev/null 2>&1; do
    if [ $SECONDS -ge $DEADLINE ]; then
        fail "Kafka did not become ready in time"
        echo "--- kafka logs ---"
        docker compose logs kafka | tail -20
        exit 1
    fi
    sleep 3
done
pass "Kafka is ready"

# -------------------------------------------------
# Helper: wait for a log pattern with timeout
# -------------------------------------------------
wait_for_log() {
    local container="$1" pattern="$2" label="$3"
    local deadline=$((SECONDS + PIPELINE_TIMEOUT))
    while ! docker logs "$container" 2>&1 | grep -qE "$pattern"; do
        if [ $SECONDS -ge $deadline ]; then
            fail "$label (no match for '$pattern' in $container after ${PIPELINE_TIMEOUT}s)"
            echo "--- last 10 lines of $container ---"
            docker logs "$container" 2>&1 | tail -10
            echo "---"
            return 1
        fi
        sleep 2
    done
    pass "$label"
    return 0
}

# -------------------------------------------------
# Helper: check a Kafka topic has at least 1 message
# -------------------------------------------------
topic_has_messages() {
    local topic="$1"
    local result
    result=$(docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
        --bootstrap-server localhost:9092 \
        --topic "$topic" \
        --from-beginning \
        --max-messages 1 \
        --timeout-ms 8000 2>/dev/null)
    [ -n "$result" ]
}

# -------------------------------------------------
# 4. Service startup checks
# -------------------------------------------------
echo ""
info "--- Stage 1: Service startup ---"

wait_for_log "market-data-service" "Published market_data" \
    "market-data-service publishing to Kafka"

wait_for_log "producer-service" "Initial market price received" \
    "producer-service received first market price"

wait_for_log "kill-switch-service" "Kill-switch service started|Trade APPROVED|Trade BLOCKED|Incomplete trade signal" \
    "kill-switch-service processing signals"

wait_for_log "execution-service" "Execution service started|Received approved order" \
    "execution-service started"

# -------------------------------------------------
# 5. Kafka topic flow
# -------------------------------------------------
echo ""
info "--- Stage 2: Kafka message flow ---"

if topic_has_messages "market_data"; then
    pass "Kafka topic 'market_data' has messages"
else
    fail "Kafka topic 'market_data' is empty — market-data-service may not be running"
fi

if topic_has_messages "trade_signal"; then
    pass "Kafka topic 'trade_signal' has messages"
else
    fail "Kafka topic 'trade_signal' is empty — producer-service may not be generating signals"
fi

if topic_has_messages "approved_order"; then
    pass "Kafka topic 'approved_order' has messages — kill-switch is approving trades"
else
    warn "Kafka topic 'approved_order' is empty (all trades may be blocked by cooldown/risk limits)"
fi

if topic_has_messages "blocked_order"; then
    pass "Kafka topic 'blocked_order' has messages — kill-switch is blocking some trades (expected)"
else
    info "Kafka topic 'blocked_order' is empty — no trades have been blocked yet"
fi

# -------------------------------------------------
# 6. Execution check
# -------------------------------------------------
echo ""
info "--- Stage 3: Binance execution ---"

if docker logs execution-service 2>&1 | grep -q "Order SUCCESS"; then
    pass "Binance Testnet: orders confirmed (Order SUCCESS seen)"
elif docker logs execution-service 2>&1 | grep -q "Order FAILED"; then
    warn "Binance Testnet: order attempts reached Binance but were rejected — check testnet balance or API key permissions"
elif docker logs execution-service 2>&1 | grep -q "Received approved order"; then
    warn "Execution service received orders but no Binance response yet — may still be in flight"
else
    fail "Execution service has not received any approved orders yet"
fi

# -------------------------------------------------
# 7. Sample messages from each topic
# -------------------------------------------------
echo ""
info "--- Stage 4: Sample messages ---"

for topic in trade_signal approved_order blocked_order; do
    echo ""
    echo "  [$topic]"
    docker exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
        --bootstrap-server localhost:9092 \
        --topic "$topic" \
        --from-beginning \
        --max-messages 2 \
        --timeout-ms 5000 2>/dev/null \
    | sed 's/^/    /' || true
done

# -------------------------------------------------
# Summary
# -------------------------------------------------
echo ""
echo "================================================"
echo -e "  Results: ${GREEN}${PASSES} passed${NC}  ${RED}${FAILS} failed${NC}"
echo "================================================"
echo ""

if [ $FAILS -eq 0 ]; then
    echo -e "${GREEN}Pipeline is healthy.${NC}"
else
    echo -e "${RED}Some checks failed. Tail all logs with:${NC}"
    echo "  docker compose -f $INFRA_DIR/docker-compose.yml logs -f"
fi

echo ""
info "Useful commands:"
echo "  # Tail all service logs"
echo "  docker compose -f $INFRA_DIR/docker-compose.yml logs -f"
echo ""
echo "  # Watch a specific Kafka topic live"
echo "  docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \\"
echo "    --bootstrap-server localhost:9092 --topic approved_order"
echo ""

if $CLEANUP; then
    info "Tearing down services (--cleanup)..."
    docker compose -f "$INFRA_DIR/docker-compose.yml" down
fi

[ $FAILS -eq 0 ] && exit 0 || exit 1
