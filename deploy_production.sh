#!/bin/bash
# PRODUCTION DEPLOYMENT QUICK-START SCRIPT
# M-Pesa Payment Integration - Charlady Platform
# Usage: bash deploy_production.sh [backup|migrate|deploy|rollback|health]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/charlady/housekeeper_connect"
BACKUP_DIR="/backups/charlady"
LOG_DIR="/var/log/charlady"
APP_USER="charlady"
VENV_PATH="/home/charlady/venv"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ============================================================================
# BACKUP FUNCTION
# ============================================================================

backup_database() {
    log_info "Starting database backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/charlady_db_${TIMESTAMP}.sql.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    # PostgreSQL backup
    pg_dump -U charlady charlady_db | gzip > "$BACKUP_FILE"
    
    if [ -f "$BACKUP_FILE" ]; then
        log_success "Database backup created: $BACKUP_FILE"
        echo "$(du -h $BACKUP_FILE | cut -f1) backup saved"
        return 0
    else
        log_error "Database backup failed"
        return 1
    fi
}

# ============================================================================
# MIGRATION FUNCTION
# ============================================================================

run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Show pending migrations
    log_info "Checking for pending migrations..."
    python manage.py showmigrations --plan | head -20
    
    # Run migrations
    log_info "Applying migrations..."
    python manage.py migrate --no-input
    
    if [ $? -eq 0 ]; then
        log_success "All migrations applied successfully"
        return 0
    else
        log_error "Migration failed"
        return 1
    fi
}

# ============================================================================
# COLLECT STATIC FILES
# ============================================================================

collect_static() {
    log_info "Collecting static files..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    python manage.py collectstatic --no-input --clear
    
    if [ $? -eq 0 ]; then
        log_success "Static files collected"
        return 0
    else
        log_error "Static files collection failed"
        return 1
    fi
}

# ============================================================================
# DEPLOY FUNCTION
# ============================================================================

deploy() {
    log_info "Starting production deployment..."
    
    # Step 1: Backup
    log_info "Step 1/6: Creating database backup..."
    if ! backup_database; then
        log_error "Backup failed, aborting deployment"
        return 1
    fi
    
    # Step 2: Pull latest code
    log_info "Step 2/6: Pulling latest code..."
    cd "$PROJECT_DIR"
    git pull origin main
    if [ $? -ne 0 ]; then
        log_error "Git pull failed"
        return 1
    fi
    log_success "Code pulled"
    
    # Step 3: Install dependencies
    log_info "Step 3/6: Installing Python dependencies..."
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        log_error "Dependency installation failed"
        return 1
    fi
    log_success "Dependencies installed"
    
    # Step 4: Run migrations
    log_info "Step 4/6: Running migrations..."
    if ! run_migrations; then
        log_error "Migrations failed"
        return 1
    fi
    
    # Step 5: Collect static files
    log_info "Step 5/6: Collecting static files..."
    if ! collect_static; then
        log_error "Static files collection failed"
        return 1
    fi
    
    # Step 6: Restart services
    log_info "Step 6/6: Restarting services..."
    
    log_info "  - Restarting Django application..."
    sudo systemctl restart charlady_app
    
    log_info "  - Restarting Celery worker..."
    sudo systemctl restart celery_worker
    
    log_info "  - Restarting Celery Beat..."
    sudo systemctl restart celery_beat
    
    # Wait for services to start
    sleep 5
    
    log_success "Deployment completed successfully!"
    
    # Health check
    log_info "Running health check..."
    health_check
    
    return 0
}

# ============================================================================
# HEALTH CHECK FUNCTION
# ============================================================================

health_check() {
    log_info "Performing health checks..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    echo ""
    log_info "1. Database Connection..."
    python manage.py dbshell <<< "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "  ✓ Database connected"
    else
        log_error "  ✗ Database connection failed"
    fi
    
    echo ""
    log_info "2. M-Pesa Service..."
    python manage.py shell <<'EOF'
from payments.mpesa_service import get_mpesa_client
try:
    client = get_mpesa_client()
    print(f"  ✓ M-Pesa client initialized (Env: {client.environment})")
except Exception as e:
    print(f"  ✗ M-Pesa initialization failed: {e}")
EOF
    
    echo ""
    log_info "3. Redis Connection..."
    python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping()" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_success "  ✓ Redis connected"
    else
        log_error "  ✗ Redis connection failed"
    fi
    
    echo ""
    log_info "4. Services Status..."
    
    # Check Django
    sudo systemctl is-active --quiet charlady_app
    if [ $? -eq 0 ]; then
        log_success "  ✓ Django app running"
    else
        log_error "  ✗ Django app not running"
    fi
    
    # Check Celery Worker
    sudo systemctl is-active --quiet celery_worker
    if [ $? -eq 0 ]; then
        log_success "  ✓ Celery worker running"
    else
        log_error "  ✗ Celery worker not running"
    fi
    
    # Check Celery Beat
    sudo systemctl is-active --quiet celery_beat
    if [ $? -eq 0 ]; then
        log_success "  ✓ Celery Beat running"
    else
        log_error "  ✗ Celery Beat not running"
    fi
    
    echo ""
    log_info "5. Integration Tests..."
    python test_integration.py 2>&1 | tail -5
}

# ============================================================================
# ROLLBACK FUNCTION
# ============================================================================

rollback() {
    log_warning "ROLLBACK INITIATED"
    
    # Get most recent backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/charlady_db_*.sql.gz 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No backup found to restore"
        return 1
    fi
    
    log_warning "Restoring from: $LATEST_BACKUP"
    
    # Confirm rollback
    read -p "Are you sure you want to rollback? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Rollback cancelled"
        return 0
    fi
    
    # Stop services
    log_info "Stopping services..."
    sudo systemctl stop charlady_app
    sudo systemctl stop celery_worker
    sudo systemctl stop celery_beat
    
    # Restore database
    log_info "Restoring database..."
    gunzip -c "$LATEST_BACKUP" | psql -U charlady charlady_db
    
    # Revert code
    log_info "Reverting code to previous version..."
    cd "$PROJECT_DIR"
    git reset --hard HEAD~1
    
    # Restart services
    log_info "Starting services..."
    sudo systemctl start charlady_app
    sudo systemctl start celery_worker
    sudo systemctl start celery_beat
    
    log_success "Rollback completed"
    return 0
}

# ============================================================================
# MONITORING FUNCTION
# ============================================================================

monitor() {
    log_info "Starting real-time monitoring (Ctrl+C to exit)..."
    echo ""
    
    trap 'echo ""; log_info "Monitoring stopped"; exit 0' INT
    
    while true; do
        clear
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║           CHARLADY PAYMENT SYSTEM - LIVE MONITORING            ║"
        echo "║                  $(date '+%Y-%m-%d %H:%M:%S')                           ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        
        cd "$PROJECT_DIR"
        source "$VENV_PATH/bin/activate"
        
        # Payment Stats
        python manage.py shell <<'PYMEOF'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

hour_ago = timezone.now() - timedelta(hours=1)
recent = Payment.objects.filter(stk_initiated_at__gte=hour_ago)

print("📊 PAYMENT STATS (Last Hour)")
print("─" * 40)
print(f"  Total: {recent.count()}")
print(f"  Completed: {recent.filter(status='completed').count()}")
print(f"  Failed: {recent.filter(status='failed').count()}")
print(f"  Pending: {recent.filter(status='pending').count()}")

if recent.count() > 0:
    rate = (recent.filter(status='completed').count() / recent.count()) * 100
    print(f"  Success Rate: {rate:.1f}%")
print()

# System Status
import os
print("🔧 SYSTEM STATUS")
print("─" * 40)

# Show services
os.system("systemctl status charlady_app --no-pager | grep 'Active:'")
os.system("systemctl status celery_worker --no-pager | grep 'Active:' || echo '  Celery Worker: ?'")
os.system("systemctl status celery_beat --no-pager | grep 'Active:' || echo '  Celery Beat: ?'")
print()

PYMEOF
        
        # System resources
        echo "💾 SYSTEM RESOURCES"
        echo "─" * 40
        echo "  Memory: $(free -h | awk 'NR==2{printf "%.1f GB / %.1f GB", $3/1024, $2/1024}')"
        echo "  Disk: $(df -h / | awk 'NR==2{printf "%s free of %s", $4, $2}')"
        CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        echo "  CPU: ${CPU}%"
        
        echo ""
        echo "📋 NEXT UPDATE: $(date -d '+5 seconds' '+%H:%M:%S')"
        
        sleep 5
    done
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  backup      - Create database backup"
    echo "  migrate     - Run database migrations"
    echo "  deploy      - Full production deployment"
    echo "  health      - Run health checks"
    echo "  rollback    - Rollback to previous version"
    echo "  monitor     - Real-time system monitoring"
    echo "  help        - Show this help message"
}

# Check command
if [ -z "$1" ]; then
    show_help
    exit 1
fi

case "$1" in
    backup)
        backup_database
        ;;
    migrate)
        run_migrations
        ;;
    deploy)
        deploy
        ;;
    health)
        health_check
        ;;
    rollback)
        rollback
        ;;
    monitor)
        monitor
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit $?
