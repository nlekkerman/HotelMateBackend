# Generated for booking expiration feature - safe to run in production

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0047_add_room_move_fields'),
    ]

    operations = [
        # Add CANCELLED_DRAFT status to existing choices
        migrations.AlterField(
            model_name='roombooking',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_PAYMENT', 'Pending Payment'),
                    ('PENDING_APPROVAL', 'Pending Staff Approval'),
                    ('CONFIRMED', 'Confirmed'),
                    ('DECLINED', 'Declined'),
                    ('CANCELLED', 'Cancelled'),
                    ('CANCELLED_DRAFT', 'Cancelled Draft'),
                    ('COMPLETED', 'Completed'),
                    ('NO_SHOW', 'No Show'),
                ],
                default='PENDING_PAYMENT',
                max_length=20
            ),
        ),
        
        # Add expires_at field with proper indexing
        migrations.AddField(
            model_name='roombooking',
            name='expires_at',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text='When this unpaid booking expires (for PENDING_PAYMENT cleanup)',
                null=True
            ),
        ),
        
        # Add index for efficient cleanup queries
        migrations.AddIndex(
            model_name='roombooking',
            index=models.Index(fields=['expires_at'], name='hotel_roombooking_expires_at_idx'),
        ),
    ]