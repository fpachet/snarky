-- ============================================================================
-- Project:	Deductive Database
-- Filename:	join1_data/join1_analysis.sql
-- Purpose:	Compute statistical data for input data to Join1 benchmark
-- Last Change:	23.03.2019
-- Language:	psql script (SQL for PostgreSQL)
-- Author:	Stefan Brass
-- EMail:	brass@informatik.uni-halle.de
-- WWW:		http://www.informatik.uni-halle.de/~brass/
-- Address:	Feldschloesschen 15, D-06120 Halle (Saale), GERMANY
-- Note:	There is no warranty at all - this code may contain bugs.
-- Copyright:	You can use this as you wish, but don't make me responsible!
--		I would be interested to hear about improved versions.
-- ============================================================================

-- The Benchmark contains the following Joins:
--	a(X, Y)  :- b1(X, Z), b2(Z, Y).
--	b1(X, Y) :- c1(X, Z), c2(Z, Y).
--	b2(X, Y) :- c3(X, Z), c4(Z, Y).
--	c1(X, Y) :- d1(X, Z), d2(Z, Y).
-- The query is a(X, Y). The database predicates are d1, d2, c2, c3, c4.

-- This script must be called with the following variables defined on the
-- command line:
--   - file_id: Input file name without the part for the predicate
--               and without the extenstion '.tsv', e.g. j1k10k
--
-- E.g., the following call would be possible:
--
-- psql -f join1_analysis.sql -v file_id=j1k10k

-- If you do not want to specify the data on the command line,
-- you can set it here (uncomment the next line):
-- \set file_id j1k10k
-- \set file_id j1k50k
\set file_id j1k250k

-- The input files must consist of lines that contain two integers
-- separated by a tab (tsv: tab-separated values).
-- There must be files with suffix _c2.tsv, _c3.tsv, _c4.tsv, _d1.tsv, _d2.tsv
-- For other formats, the \copy command below must be adapted.

-- Define here a directory where the data file can be found:
-- \set input_dir ../data_tsv
\set input_dir .

-- Note: The script overwrites the file load_cmd.sql!
-- Note: The script also overwrites the files with the results, i.e.
--	join1_data.sql


\echo
\echo '======================================================================='
\echo 'Input File: ' :'file_id' '(with suffix _pred.tsv)'
\echo '======================================================================='

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Drop old version of views and tables:'
\echo '-----------------------------------------------------------------------'
\echo

\echo 'Note: It is ok if the tables or views do not exist in the first run'
\echo

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

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create tables:'
\echo '-----------------------------------------------------------------------'
\echo

create table c2(x integer not null, y integer not null);
create table c3(x integer not null, y integer not null);
create table c4(x integer not null, y integer not null);
create table d1(x integer not null, y integer not null);
create table d2(x integer not null, y integer not null);

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Load the data:'
\echo '-----------------------------------------------------------------------'
\echo

\echo 'Write command to load the data to load_cmd.sql:'

-- The problem is that variables are not replaced in the copy command.
-- Therefore, we write a file with the command to load the par table
-- from the input file.

-- Tuples only:
\t on
-- Output file:
\o load_cmd.sql
select concat('\copy c2 from ''', :'input_dir', '/', :'file_id', '_c2.tsv'';');
select concat('\copy c3 from ''', :'input_dir', '/', :'file_id', '_c3.tsv'';');
select concat('\copy c4 from ''', :'input_dir', '/', :'file_id', '_c4.tsv'';');
select concat('\copy d1 from ''', :'input_dir', '/', :'file_id', '_d1.tsv'';');
select concat('\copy d2 from ''', :'input_dir', '/', :'file_id', '_d2.tsv'';');
-- Standard output again:
\o
-- Normal decoration of tables:
\t off


\echo 'LOAD DATA'
\timing on
-- Execute the \copy commands that were generated above:
\i load_cmd.sql
create index d2_xy on d2(x,y);
create index c4_xy on c4(x,y);
create index c2_xy on c2(x,y);
analyze d1;
analyze d2;
analyze c2;
analyze c3;
analyze c4;
\timing off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create views for derived predicates:'
\echo '-----------------------------------------------------------------------'
\echo

--	a(X, Y)  :- b1(X, Z), b2(Z, Y).
--	b1(X, Y) :- c1(X, Z), c2(Z, Y).
--	b2(X, Y) :- c3(X, Z), c4(Z, Y).
--	c1(X, Y) :- d1(X, Z), d2(Z, Y).

create view c1_nodup as
select distinct d1.x, d2.y
from   d1, d2
where  d1.y = d2.x;

create view b1_nodup as
select distinct c1_nodup.x, c2.y
from   c1_nodup, c2
where  c1_nodup.y = c2.x;

create view b2_nodup as
select distinct c3.x, c4.y
from   c3, c4
where  c3.y = c4.x;

create view a_nodup as
select distinct b1_nodup.x, b2_nodup.y
from   b1_nodup, b2_nodup
where  b1_nodup.y = b2_nodup.x;

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create view for main cost computation (rule_instances):'
\echo '-----------------------------------------------------------------------'
\echo

create view rule_instances as
select 'a' as rule, count(*) as instances
from   b1_nodup, b2_nodup
where  b1_nodup.y = b2_nodup.x
union all
select 'b1' as rule, count(*) as instances
from   c1_nodup, c2
where  c1_nodup.y = c2.x
union all
select 'b2' as rule, count(*) as instances
from   c3, c4
where  c3.y = c4.x
union all
select 'c1' as rule, count(*) as instances
from   d1, d2
where  d1.y = d2.x;

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create view to compute the number of derived facts (num_facts):'
\echo '-----------------------------------------------------------------------'
\echo

create view num_facts as
select 'a' as pred, count(*) as facts
from a_nodup
union all
select 'b1' as pred, count(*) as facts
from b1_nodup
union all
select 'b2' as pred, count(*) as facts
from b2_nodup
union all
select 'c1' as pred, count(*) as facts
from c1_nodup;

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create additional views to analyze the data:'
\echo '-----------------------------------------------------------------------'
\echo

create view nodes as
select x as node from c2
union
select y as node from c2
union
select x as node from c3
union
select y as node from c3
union
select x as node from c4
union
select y as node from c4
union
select x as node from d1
union
select y as node from d1
union
select x as node from d2
union
select y as node from d2
order by node;

create view num_nodes as
select count(*) as num_nodes
from nodes;

create view num_edges as
select 'c2' as pred, count(*) as num_edges
from c2
union
select 'c3' as pred, count(*) as num_edges
from c3
union
select 'c4' as pred, count(*) as num_edges
from c4
union
select 'd1' as pred, count(*) as num_edges
from d1
union
select 'd2' as pred, count(*) as num_edges
from d2;

create view duplicate_edges as
select 'c2' as pred, count(*) as duplicate_edges
from (select x, y from c2 group by x, y having count(*)>1) var
union
select 'c3' as pred, count(*) as duplicate_edges
from (select x, y from c3 group by x, y having count(*)>1) var
union
select 'c4' as pred, count(*) as duplicate_edges
from (select x, y from c4 group by x, y having count(*)>1) var
union
select 'd1' as pred, count(*) as duplicate_edges
from (select x, y from d1 group by x, y having count(*)>1) var
union
select 'd2' as pred, count(*) as duplicate_edges
from (select x, y from d2 group by x, y having count(*)>1) var;
