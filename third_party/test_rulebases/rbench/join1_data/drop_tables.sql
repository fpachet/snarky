-- ============================================================================
-- Project:	Deductive Database
-- Filename:	join1_data/drop_tables.sql
-- Purpose:	Drop tables and view that were used in the Join1 data analysis.
-- Last Change:	22.03.2019
-- Language:	psql script (SQL for PostgreSQL)
-- Author:	Stefan Brass
-- EMail:	brass@informatik.uni-halle.de
-- WWW:		http://www.informatik.uni-halle.de/~brass/
-- Address:	Feldschloesschen 15, D-06120 Halle (Saale), GERMANY
-- Note:	There is no warranty at all - this code may contain bugs.
-- Copyright:	You can use this as you wish, but don't make me responsible!
--		I would be interested to hear about improved versions.
-- ============================================================================


drop view if exists num_facts;

drop view if exists num_nodes;
drop view if exists num_edges;
drop view if exists duplicate_edges;

drop view if exists nodes;

drop view if exists rule_instances;

drop view if exists a_nodup;
drop view if exists b1_nodup;
drop view if exists b2_nodup;
drop view if exists c1_nodup;

drop table if exists c2;
drop table if exists c3;
drop table if exists c4;
drop table if exists d1;
drop table if exists d2;

