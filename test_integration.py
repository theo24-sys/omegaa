#!/usr/bin/env python
"""
Integration test for M-Pesa payment flow
Tests model creation, signal handlers, and M-Pesa service
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from payments.models import Payment, PaymentPlan, UserSubscription, MonthlyContribution
from payments.mpesa_service import get_mpesa_client
from datetime import datetime, timedelta
import json

User = get_user_model()

def test_models():
    """Test that all models exist and have correct fields"""
    print("\n" + "=" * 60)
    print("TEST 1: MODEL STRUCTURE")
    print("=" * 60)
    
    # Check CustomUser
    user_fields = {f.name for f in User._meta.get_fields()}
    required_user_fields = {'is_paid_verified', 'paid_verification_date', 'paid_verification_expires_at'}
    assert required_user_fields.issubset(user_fields), f"Missing CustomUser fields: {required_user_fields - user_fields}"
    print("✓ CustomUser model: All membership fields present")
    
    # Check Payment
    payment_fields = {f.name for f in Payment._meta.get_fields()}
    required_payment_fields = {'is_mpesa_stk', 'stk_initiated_at', 'stk_reference_id', 'mpesa_transaction_id', 'payment_verified_at'}
    assert required_payment_fields.issubset(payment_fields), f"Missing Payment fields: {required_payment_fields - payment_fields}"
    print("✓ Payment model: All M-Pesa fields present")
    
    # Check UserSubscription
    sub_fields = {f.name for f in UserSubscription._meta.get_fields()}
    required_sub_fields = {'user', 'plan', 'started_at', 'expires_at', 'status'}
    assert required_sub_fields.issubset(sub_fields), f"Missing UserSubscription fields: {required_sub_fields - sub_fields}"
    print("✓ UserSubscription model: All fields present")
    
    # Check MonthlyContribution
    contrib_fields = {f.name for f in MonthlyContribution._meta.get_fields()}
    required_contrib_fields = {'worker', 'year', 'month', 'calculated_salary', 'amount_due', 'payment_status', 'payment_date'}
    assert required_contrib_fields.issubset(contrib_fields), f"Missing MonthlyContribution fields: {required_contrib_fields - contrib_fields}"
    print("✓ MonthlyContribution model: All fields present")

def test_mpesa_service():
    """Test M-Pesa service initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: M-PESA SERVICE")
    print("=" * 60)
    
    client = get_mpesa_client()
    assert client is not None, "Failed to initialize MpesaClient"
    print(f"✓ MpesaClient initialized")
    print(f"  - Environment: {client.environment}")
    print(f"  - Short Code: {client.short_code}")
    print(f"  - Consumer Key: {client.consumer_key[:10]}...")
    
    # Verify credentials are set
    assert client.consumer_key, "Consumer key not set"
    assert client.consumer_secret, "Consumer secret not set"
    assert client.passkey, "Passkey not set"
    print("✓ All M-Pesa credentials configured")

def test_payment_plan():
    """Test payment plan creation"""
    print("\n" + "=" * 60)
    print("TEST 3: PAYMENT PLANS")
    print("=" * 60)
    
    # Check verification plan exists or can be created
    plan, created = PaymentPlan.objects.get_or_create(
        plan_type='verification',
        target_group='worker',
        defaults={
            'name': 'Verification Badge',
            'description': 'Annual verification badge for workers',
            'price': 250,
            'duration_days': 365,
            'is_active': True
        }
    )
    print(f"✓ Verification plan: {plan.name} (KES {plan.price})")
    
    # Check monthly contribution
    contrib_plan, created = PaymentPlan.objects.get_or_create(
        plan_type='monthly_contribution',
        target_group='worker',
        defaults={
            'name': 'Monthly 3% Contribution',
            'description': '3% of monthly earnings',
            'price': 0,
            'duration_days': 1,
            'is_active': True
        }
    )
    print(f"✓ Monthly contribution plan: {contrib_plan.name}")

def test_signals():
    """Test signal handlers"""
    print("\n" + "=" * 60)
    print("TEST 4: SIGNAL HANDLERS")
    print("=" * 60)
    
    from django.db.models.signals import post_save
    listeners = list(post_save._live_receivers(Payment))
    print(f"✓ {len(listeners)} signal listener(s) connected to Payment model")
    assert len(listeners) > 0, "No signal listeners connected"

def test_views():
    """Test that views can be imported"""
    print("\n" + "=" * 60)
    print("TEST 5: VIEW FUNCTIONS")
    print("=" * 60)
    
    from payments import views
    required_views = [
        'membership_checkout',
        'contribution_pay',
        'payment_status',
        'mpesa_callback',
        'contribution_payment',
        'contribution_history',
        'payment_success',
        'payment_failed',
    ]
    
    for view_name in required_views:
        assert hasattr(views, view_name), f"Missing view: {view_name}"
    print(f"✓ All {len(required_views)} payment views present")

def test_admin_views():
    """Test admin views"""
    print("\n" + "=" * 60)
    print("TEST 6: ADMIN VIEWS")
    print("=" * 60)
    
    from payments import admin_views
    required_views = [
        'contribution_dashboard',
        'contribution_details',
        'mark_contribution_paid',
    ]
    
    for view_name in required_views:
        assert hasattr(admin_views, view_name), f"Missing admin view: {view_name}"
    print(f"✓ All {len(required_views)} admin views present")

def main():
    """Run all tests"""
    try:
        test_models()
        test_mpesa_service()
        test_payment_plan()
        test_signals()
        test_views()
        test_admin_views()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nIntegration ready for:")
        print("  1. M-Pesa STK push testing (sandbox)")
        print("  2. Signal handler verification")
        print("  3. Admin dashboard testing")
        print("  4. End-to-end payment flow testing")
        print("\nNext: Deploy to production with M-Pesa credentials")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
