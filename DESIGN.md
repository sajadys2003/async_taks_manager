
1. Scaling (very high Traffic)
solution: Scale Deployment using contaners

2. Worker Failure
solution: Acknowledgments. Workers only ACK the message to RabbitMQ after job finishes. If worker crashes, un-acked message auto-requeues.

3. Duplicate Processing
solutin: Execute: `UPDATE jobs SET status = 'running' WHERE id = X AND status = 'pending'`. If 0 rows updated, drop the job (another worker took it before).

4. Redis Failure
solution: Using try/except. If Redis fails, use db.

5. Large Scale Database (too many Records)
solution: Create composite index on user_id, id DESC.
