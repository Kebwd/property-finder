import { copyTo } from 'pg-copy-streams';
import pool from '../db';

// GET /stores/export
router.get('/export', async (req, res) => {
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader(
    'Content-Disposition',
    'attachment; filename="export.csv"'
  );
  const client = await pool.connect();
  try {
    const sql = 'COPY (SELECT l.province FROM stores) TO STDOUT WITH CSV HEADER';
    const stream = client.query(copyTo(sql));
    stream.pipe(res).on('end', () => client.release());
  } catch (err) {
    client.release();
    console.error(err);
    res.status(500).send('Export failed');
  }
});