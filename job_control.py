import os
import signal
import subprocess


class Job:
    def __init__(self, job_id, pid, command, status="running"):
        self.job_id = job_id
        self.pid = pid
        self.command = command
        self.status = status
        self.process = None


class JobManager:
    def __init__(self, shell):
        self.shell = shell
        self.jobs = {}
        self.next_id = 1

    def add_job(self, pid, command, process=None, status="running"):
        job_id = self.next_id
        self.next_id += 1
        job = Job(job_id, pid, command, status)
        job.process = process
        self.jobs[job_id] = job
        return job_id

    def remove_job(self, job_id):
        return self.jobs.pop(job_id, None)

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_jobs(self):
        self.update_statuses()
        result = []
        for jid in sorted(self.jobs.keys()):
            job = self.jobs[jid]
            result.append((jid, job.pid, job.status, job.command))
        return result

    def update_statuses(self):
        done_ids = []
        for jid, job in list(self.jobs.items()):
            if job.status == "done":
                continue
            if job.process is not None:
                ret = job.process.poll()
                if ret is not None:
                    job.status = "done"
                else:
                    try:
                        pgid = os.getpgid(job.pid)
                    except (ProcessLookupError, OSError):
                        job.status = "done"
        return done_ids

    def check_done_jobs(self):
        notifications = []
        for jid, job in list(self.jobs.items()):
            if job.status == "done":
                continue
            if job.process is not None:
                ret = job.process.poll()
                if ret is not None:
                    job.status = "done"
                    notifications.append((jid, job.command))
        return notifications

    def bring_to_foreground(self, job_id):
        job = self.get_job(job_id)
        if job is None:
            return None, f"minibash: fg: %{job_id}: no such job"
        if job.status == "done":
            self.remove_job(job_id)
            return None, f"minibash: fg: %{job_id}: job has finished"
        if job.process is None:
            return None, f"minibash: fg: %{job_id}: no process"
        job.status = "running"
        try:
            os.kill(job.pid, signal.SIGCONT)
        except (ProcessLookupError, OSError):
            pass
        try:
            job.process.wait()
            exit_code = job.process.returncode
            job.status = "done"
            self.remove_job(job_id)
            return exit_code, None
        except Exception as e:
            return None, f"minibash: fg: {e}"

    def resume_background(self, job_id):
        job = self.get_job(job_id)
        if job is None:
            return f"minibash: bg: %{job_id}: no such job"
        if job.status == "done":
            self.remove_job(job_id)
            return f"minibash: bg: %{job_id}: job has finished"
        job.status = "running"
        try:
            os.kill(job.pid, signal.SIGCONT)
        except (ProcessLookupError, OSError):
            pass
        return None

    def wait_all(self):
        for jid, job in list(self.jobs.items()):
            if job.process is not None and job.status != "done":
                job.process.wait()
                job.status = "done"

    def format_jobs_output(self):
        lines = []
        for jid, pid, status, command in self.list_jobs():
            lines.append(f"[{jid}] {status:>7}  {pid}  {command}")
        return '\n'.join(lines)

    def cleanup_done(self):
        to_remove = []
        for jid, job in self.jobs.items():
            if job.status == "done":
                to_remove.append(jid)
        for jid in to_remove:
            self.remove_job(jid)
