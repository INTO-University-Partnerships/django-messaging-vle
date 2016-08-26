from django_cron import CronJobBase, Schedule

from .sync import full_sync


class FullSync(CronJobBase):
    RUN_AT_TIMES = ['22:00', '06:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'vle.full_sync'

    def do(self):
        result = full_sync()
        return result
