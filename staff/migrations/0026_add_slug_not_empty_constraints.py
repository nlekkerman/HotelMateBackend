"""
Add DB-level integrity constraints for Department.slug and Role.slug.

Split out from 0025 because AddConstraint cannot run in the same
transaction as the data-cleanup RunPython on Postgres (pending trigger
events error).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0025_seed_canonical_departments_and_fixups'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='department',
            constraint=models.CheckConstraint(
                check=~models.Q(slug=''),
                name='department_slug_not_empty',
            ),
        ),
        migrations.AddConstraint(
            model_name='role',
            constraint=models.CheckConstraint(
                check=~models.Q(slug=''),
                name='role_slug_not_empty',
            ),
        ),
    ]
