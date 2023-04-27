# Generated by Django 3.2.18 on 2023-04-27 07:48
# Edited manual
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def run_copy_field(apps, app_label, model_name, field_src: str, field_dst: str):
    model = apps.get_model(app_label, model_name)
    records = model.objects.all()

    for rec in records:
        rec[field_dst] = rec[field_src]

    model.objects.bulk_update(records, [field_dst])


def run_fill_field(apps, app_label, model_name, field: str, value):
    model = apps.get_model(app_label, model_name)
    kw = {
        field: value
    }
    model.objects.update(**kw)  # type: ignore


def migrations_update_field_value(app_label, model_name, field: str, value):
    return [
        migrations.RunPython(lambda apps, schema_editor: run_fill_field(
            apps, app_label, model_name, field, value)
        ),
    ]


def migrations_update_field_copy(app_label, model_name, field_src: str, field_dst: str):
    return [
        migrations.RunPython(lambda apps, schema_editor: run_copy_field(
            apps, app_label, model_name,
            field_src=field_src,
            field_dst=field_dst)
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cml', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exchange',
            options={'ordering': ['-dt_action'], 'verbose_name': 'Exchange log entry', 'verbose_name_plural': 'Exchange logs'},
        ),

        # filename -> file_name
        migrations.RenameField(
            model_name='exchange',
            old_name='filename',
            new_name='file_name',
        ),
        migrations.AlterField(
            model_name='exchange',
            name='file_name',
            field=models.CharField(max_length=250, default=''),
        ),

        # timestamp -> dt_start
        # dt_action = dt_start
        migrations.RenameField(
            model_name='exchange',
            old_name='timestamp',
            new_name='dt_start',
        ),
        migrations.AddField(
            model_name='exchange',
            name='dt_action',
            field=models.DateTimeField(auto_now=True, blank=True),
        ),
        *migrations_update_field_copy('cml', 'exchange', field_dst='dt_action', field_src='dt_start'),

        # Statistic
        migrations.AddField(
            model_name='exchange',
            name='c_exp_doc',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_imp_catalogue',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_imp_classifier',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_imp_doc',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_imp_offers_pack',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_up',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_up_img',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='exchange',
            name='c_up_xml',
            field=models.IntegerField(default=0),
        ),

        # State
        migrations.AddField(
            model_name='exchange',
            name='state',
            field=models.CharField(
                choices=[('init', 'INIT'), ('DONE', 'DONE'), ('abort', 'ABORT')],
                default='init',
                max_length=15,
                null=True,
                blank=True,
            ),
        ),
        # All entries in the previous version mean DONE
        *migrations_update_field_value('cml', 'exchange', 'state', 'DONE'),
        migrations.AlterField(
            model_name='exchange',
            name='state',
            field=models.CharField(
                choices=[('init', 'INIT'), ('DONE', 'DONE'), ('abort', 'ABORT')],
                default='init',
                max_length=15,
            ),
        ),

        # exchange_type -> report
        migrations.RenameField(
            model_name='exchange',
            old_name='exchange_type',
            new_name='report',
        ),
        migrations.AlterField(
            model_name='exchange',
            name='report',
            field=models.CharField(max_length=2048, default=''),
        ),

        # If user deleted, their past activity is saved
        migrations.AlterField(
            model_name='exchange',
            name='user',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
            ),
        ),
    ]