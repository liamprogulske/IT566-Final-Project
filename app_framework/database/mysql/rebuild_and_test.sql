-- ============================================================
--  REBUILD AND TEST SCRIPT
--  - Drops and recreates it566_project_db
--  - Runs schema, seed data, views, procs
--  - Executes smoketest and inspection queries
-- ============================================================

-- 1. Build the database (schema + seed + views + procs)
SOURCE build_db.sql;

-- 2. Make sure we are using the correct database
USE it566_project_db;

-- 3. Run smoke tests (basic sanity checks for channels/campaigns/xref)
SOURCE tests/smoke/campaign_channels_smoketest.sql;

-- 4. Run inspection script to print current state of tables
SOURCE tests/inspect/inspect_database.sql;

-- ============================================================
-- END OF REBUILD & TEST SCRIPT
-- ============================================================
