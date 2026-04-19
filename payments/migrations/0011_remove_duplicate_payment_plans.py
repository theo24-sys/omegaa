"""
Data migration to remove duplicate PaymentPlan entries
This runs after all previous migrations to clean up duplicate data
before the unique constraints can take effect.
"""
from django.db import migrations


def remove_duplicates(apps, schema_editor):
    """Remove duplicate PaymentPlans keeping the first one for each (plan_type, target_group) combo"""
    PaymentPlan = apps.get_model('payments', 'PaymentPlan')
    
    # Get all payment plans grouped by (plan_type, target_group)
    seen = {}
    duplicates_to_delete = []
    
    for plan in PaymentPlan.objects.all().order_by('id'):
        key = (plan.plan_type, plan.target_group)
        
        if key in seen:
            # This is a duplicate, mark for deletion
            print(f"Found duplicate: {plan.plan_type}/{plan.target_group} (ID: {plan.id})")
            duplicates_to_delete.append(plan.id)
        else:
            # First one we've seen, keep it
            seen[key] = plan.id
    
    # Delete all duplicates
    if duplicates_to_delete:
        print(f"\nRemoving {len(duplicates_to_delete)} duplicate PaymentPlan entries...")
        PaymentPlan.objects.filter(id__in=duplicates_to_delete).delete()
        print(f"Successfully removed duplicates. Remaining plans:")
        for plan in PaymentPlan.objects.all().order_by('plan_type'):
            print(f"  - {plan.plan_type}/{plan.target_group}: {plan.name} (ID: {plan.id})")
    else:
        print("No duplicates found - database is clean")


def reverse_remove_duplicates(apps, schema_editor):
    """This is a destructive data migration, so we can't really reverse it"""
    print("WARNING: Cannot reverse duplicate removal - data has been deleted")


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0010_merge_0002_add_unique_constraints_0009_payment_job'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates, reverse_remove_duplicates),
    ]
