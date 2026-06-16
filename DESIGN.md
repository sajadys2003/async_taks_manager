
1. Scaling (very high Traffic)
bottlenecks: API & DBconnection limit, 
solution: Scale Deployment using contaners

3. Worker Failure
solution: Acknowledgments. Workers only ACK the message to RabbitMQ after job finishes. If worker crashes, un-acked message auto-requeues.

4. Duplicate Processing
PostgreSQL Advisory Locks (`pg_advisory_xact_lock`).

5. Redis Failure
solution: Using try/except. If Redis fails, use db.
impacts: lowers the speed of system

6. Large Scale Database (too many Jobs)
indexing solution 1: Create composite index on user_id, id DESC.
indexing solution 2: Partial index on 'pending', 'queued' and 'running' tasks
partitioning solution: Configure Postgres to split the table by time (month for example) automatically
