# Generated manually to fix null values in has_unread field

from django.db import migrations


def fix_null_has_unread(apps, schema_editor):
    """
    Set has_unread to False for conversations where it's null
    """
    StaffConversation = apps.get_model('staff_chat', 'StaffConversation')
    
    # Update all null has_unread values to False
    StaffConversation.objects.filter(
        has_unread__isnull=True
    ).update(has_unread=False)


class Migration(migrations.Migration):

    dependencies = [
        ('staff_chat', '0002_staffchatattachment_thumbnail_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_null_has_unread,
            reverse_code=migrations.RunPython.noop
        ),
    ]
