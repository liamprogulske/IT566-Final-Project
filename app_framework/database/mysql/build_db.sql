-- ============================================================
--  BUILD DATABASE FOR IT566 CAMPAIGNS & CHANNELS PROJECT
--  Creates schema, loads seed data (optional), views & procs
-- ============================================================

DROP DATABASE IF EXISTS it566_project_db;

CREATE DATABASE it566_project_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE it566_project_db;

-- --------------------
-- CORE TABLES & METRICS
-- --------------------
SOURCE tests/schema/01_schema.sql;

-- --------------------
-- SAMPLE DATA
-- --------------------
SOURCE 02_seed.sql;

-- --------------------
-- VIEWS
-- --------------------
SOURCE 03_views.sql;

-- --------------------
-- STORED PROCS
-- --------------------
SOURCE 04_procs.sql;

-- ============================================================
-- END OF BUILD SCRIPT
-- ============================================================
