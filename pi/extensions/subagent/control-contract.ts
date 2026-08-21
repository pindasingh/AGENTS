export interface CancellableJob {
	controller: AbortController;
}

export function cancelOwnedJob<T extends CancellableJob>(jobs: Map<string, T>, id: string): boolean {
	const job = jobs.get(id);
	if (!job) return false;
	job.controller.abort();
	return true;
}

export function terminalJobStatus(aborted: boolean): "aborted" | "failed" {
	return aborted ? "aborted" : "failed";
}

export function cancelAllOwnedJobs<T extends CancellableJob>(jobs: Map<string, T>): string[] {
	const ids = Array.from(jobs.keys());
	for (const job of jobs.values()) job.controller.abort();
	return ids;
}
