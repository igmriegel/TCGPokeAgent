# Tasks

Use [`TASK_INDEX.md`](TASK_INDEX.md) as the only task-status registry.

Before working:

1. choose the highest-priority unblocked task;
2. read its linked sprint and contract;
3. preserve unrelated worktree changes;
4. freeze the applicable gate before implementation.

Before marking a task done:

1. run its focused verification and the required quality gates;
2. record immutable evidence;
3. update the task row;
4. update `PROJECT_STATUS.md` only if a headline decision changed;
5. create an atomic commit.
