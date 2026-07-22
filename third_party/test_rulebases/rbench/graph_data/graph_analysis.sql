-- ============================================================================
-- Project:	Deductive Database
-- Filename:	sql/tc_graph_stat
-- Purpose:	Compute statistical data for input graph to tc benchmark
-- Last Change:	16.06.2018
-- Language:	psql script (SQL for PostgreSQL)
-- Author:	Stefan Brass
-- EMail:	brass@informatik.uni-halle.de
-- WWW:		http://www.informatik.uni-halle.de/~brass/
-- Address:	Feldschloesschen 15, D-06120 Halle (Saale), GERMANY
-- Note:	There is no warranty at all - this code may contain bugs.
-- Copyright:	You can use this as you wish, but don't make me responsible!
--		I would be interested to hear about improved versions.
-- ============================================================================

-- This script must be called with the following variables defined on the
-- command line:
--   - input_file: Input file name without the extenstion '.tsv' and without
--		the directory
--   - file_id: Short file ID.
--		It is only used in the generated row for the data table.
--   - max_iter: Limit for tc computation with levels.
--		This does not influence the correct computation of the
--		transitive closure, only the maximal number of iterations shown.
--		The tc computation with levels may take a lot of time
--		if this limit is chosen too high.
--
-- E.g., the following call would be possible:
--
-- psql -f tc_graph_stat.sql -v file_id=rn2 -v input_file=tc_rn2_n1k_e500k \
--	-v max_iter=10

-- If you do not want to specify the data on the command line,
-- you can set it here (uncomment the next lines):
--	\set file_id rn2
--	\set input_file tc_rn2_n1k_e500k
--	\set max_iter 10

-- The input file must consist of lines that contain two integers
-- separated by a tab (tsv: tab-separated values).
-- For other formats, the \copy command below must be adapted.

-- Define here a directory where the data file can be found:
\set input_dir ../data_tsv

-- Note: The script overwrites the file load_cmd.sql!
-- Note: The script also overwrites the files with the results, i.e.
--	graph_data_part.tex
--	graph_data_part.sql
--	graph_indeg_part.sql
--	graph_outdeg_part.sql
--	graph_iter_part.sql


\echo
\echo '======================================================================='
\echo 'Input File: ' :'input_file' '(with extension .tsv)'
\echo '======================================================================='

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Drop old version of views and tables:'
\echo '-----------------------------------------------------------------------'
\echo

\echo 'Note: It is ok if the tables or views do not exist in the first run'
\echo
drop view if exists graph_statistics;
drop view if exists num_nodes;
drop view if exists num_edges;
drop view if exists duplicate_edges;
drop view if exists num_loops;
drop view if exists in_degree_statistics;
drop view if exists out_degree_statistics;
drop view if exists in_degree_distribution;
drop view if exists out_degree_distribution;
drop view if exists nodes_with_in_degree;
drop view if exists nodes_with_out_degree;
drop view if exists nodes;

drop view if exists cost_measure;
drop view if exists cycles;
drop view if exists tc_view;
-- drop view if exists connections_2_edges;
-- drop view if exists connections_1_2_edges;
-- drop view if exists connections_3_edges;

drop table if exists par;
drop table if exists tc;
drop table if exists tc_size;
drop table if exists tc_num_cycles;
drop table if exists tc_dist;
drop table if exists tc_iter;
drop table if exists tc_max_iter;
drop table if exists tc_more_iter;
drop table if exists tc_cost;

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create tables:'
\echo '-----------------------------------------------------------------------'
\echo

create table par(x integer not null, y integer not null);
create table tc(x integer not null, y integer not null);
create table tc_size(tc_size integer not null);
create table tc_num_cycles(nodes_in_cycles integer not null);
create table tc_dist(x integer not null, y integer not null,
	distance integer not null);
create index tc_dist_xy on tc_dist(x,y);
create table tc_iter(iter integer not null, num_tuples integer not null);
create table tc_max_iter(max_iter_below_limit integer not null);
create table tc_more_iter(tc_tuples_with_more_iterations integer not null);
create table tc_cost(cost integer not null);

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
select concat('\copy par from ''', :'input_dir', '/', :'input_file', '.tsv'';');
-- Standard output again:
\o
-- Normal decoration of tables:
\t off


\echo 'LOAD DATA'
\timing on
--\copy par from 'tc_rn2_n1k_e500k.tsv';
\i load_cmd.sql
create index par_yx on par(y,x);
analyze par;
\timing off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Create views to analyze the graph:'
\echo '-----------------------------------------------------------------------'
\echo

create view nodes as
select x as node from par
union
select y as node from par
order by node;

create view num_nodes as
select count(*) as num_nodes
from nodes;

create view num_edges as
select count(*) as num_edges
from par;

create view duplicate_edges as
select count(*) as duplicate_edges
from (select x, y from par group by x, y having count(*)>1) var;

create view num_loops as
select count(*) as num_loops
from par
where x = y;

create view nodes_with_in_degree as
select node, count(par.y) as in_degree
from nodes left join par on nodes.node = par.y
group by node;

-- Alternative solution:
-- select y as node, count(*) as in_degree
-- from par
-- group by y
-- union all
-- select node, 0 as in_degree
-- from nodes
-- where not exists (select * from par where nodes.node = par.y)
-- order by node;

create view nodes_with_out_degree as
select node, count(par.x) as out_degree
from nodes left join par on nodes.node = par.x
group by node;

-- Alternative solution, takes a very long time: Problem with not in
-- select x as node, count(*) as out_degree
-- from par
-- group by x
-- union all
-- select node, 0 as out_degree
-- from nodes
-- where node not in (select x from par)
-- order by node;

create view in_degree_distribution as
select in_degree, count(*) as num_nodes
from nodes_with_in_degree
group by in_degree
order by in_degree;

create view out_degree_distribution as
select out_degree, count(*) as num_nodes
from nodes_with_out_degree
group by out_degree
order by out_degree;

create view in_degree_statistics as
select min(in_degree) as min_in_degree,
	max(in_degree) as max_in_degree,
	avg(in_degree) as avg_in_degree,
	count(distinct in_degree) as distinct_in_degrees
from nodes_with_in_degree;

create view out_degree_statistics as
select min(out_degree) as min_out_degree,
	max(out_degree) as max_out_degree,
	avg(out_degree) as avg_out_degree,
	count(distinct out_degree) as distinct_out_degrees
from nodes_with_out_degree;

create view graph_statistics as
select
	num_nodes.num_nodes,
	num_edges.num_edges,
	duplicate_edges.duplicate_edges,
	num_loops.num_loops,
	in_degree_statistics.min_in_degree,
	in_degree_statistics.max_in_degree,
	out_degree_statistics.min_out_degree,
	out_degree_statistics.max_out_degree
from
	num_nodes,
	num_edges,
	duplicate_edges,
	num_loops,
	in_degree_statistics,
	out_degree_statistics;

\echo
\echo '-----------------------------------------------------------------------'
\echo 'GRAPH STATISTICS:'
\echo '-----------------------------------------------------------------------'
\echo

\timing on
select num_nodes, num_edges, duplicate_edges, num_loops
from graph_statistics;
select min_in_degree, max_in_degree, min_out_degree, max_out_degree
from graph_statistics;
\timing off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Transitive Closure:'
\echo '-----------------------------------------------------------------------'
\echo

create view tc_view(x, y) as
        with recursive tc_tmp as
        (select par.x, par.y
        from   par
        union
        select par.x, tc_tmp.y
        from   par, tc_tmp
        where  par.y = tc_tmp.x)
select * from tc_tmp;

\echo 'Compute Transitive Closure (this may take a while ...):'
\timing on
insert into tc select * from tc_view;
analyze tc;

\echo
\echo 'Size of transitive closure:'
\echo

insert into tc_size
select count(*) as tc_size from tc;

select * from tc_size;

\echo 'Compute Cost Measure:'
create view cost_measure as
select rule_1.n as rule_1, rule_2.n as rule_2,
	rule_1.n + rule_2.n as total_cost
from	(select count(*) as n from par) rule_1,
	(select count(*) as n
	 from par, tc
	 where par.y = tc.x) rule_2;

\echo
\echo 'Cost measure for transitive closure computation:'
\echo

select * from cost_measure;

insert into tc_cost
select total_cost as cost
from cost_measure;

\echo 'Compute Nodes that participate in cycles:'
create view cycles as
select x as node from tc where x=y;

\echo
\echo 'The graph contains cycles if the following query returns a value > 0:'
\echo

insert into tc_num_cycles
select count(*) as nodes_in_cycles from cycles;

select * from tc_num_cycles;

\timing off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Compute Transitive Closure with levels (max.' :max_iter 'iterations):'
\echo '-----------------------------------------------------------------------'
\echo

\timing on
\echo 'This will take a long time ...'
with recursive tc_levels as
	(select par.x, par.y, 1 as distance
	from   par
	union
	select par.x, tc_levels.y, tc_levels.distance + 1
	from   par, tc_levels
	where  par.y = tc_levels.x and tc_levels.distance < :max_iter)
insert into tc_dist select x, y, min(distance) from tc_levels group by x, y;

\echo
\echo 'tc tuples computed in each iteration (<=' :max_iter '):'
\echo

insert into tc_iter
select distance as iteration, count(*)
from tc_dist
group by distance;

select * from tc_iter
order by iter;

\echo
\echo 'Number of iterations (limited to' :max_iter 'iterations):'
\echo

insert into tc_max_iter
select max(iter) from tc_iter;

select * from tc_max_iter;

\echo
\echo 'tc tuples not computed in' :max_iter 'iterations:'
\echo

insert into tc_more_iter
select count(*)
from tc
where not exists
	(select * from tc_dist where tc.x=tc_dist.x and tc.y=tc_dist.y);

select * from tc_more_iter;

\timing off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Write result in LaTeX format to tc_stat_output.tex:'
\echo '-----------------------------------------------------------------------'
\echo

-- Tuples only:
\t on
-- Output file:
\o graph_data_part.tex
-- The query to generate one line of the statistics table:
select
	:'input_file' || '&' ||
	num_nodes.num_nodes || '&' ||
	num_edges.num_edges || '&' ||
	-- duplicate_edges.duplicate_edges || '&' ||
	-- case when num_loops.num_loops > 0 then 'yes' else 'no' end || '&' ||
	in_degree_statistics.min_in_degree || '&' ||
	in_degree_statistics.max_in_degree || '&' ||
	out_degree_statistics.min_out_degree || '&' ||
	out_degree_statistics.max_out_degree || '&' ||
	case when tc_num_cycles.nodes_in_cycles > 0 then 'yes' else 'no' end ||
		'&' ||
	tc_size.tc_size || '&' ||
	case when tc_more_iter.tc_tuples_with_more_iterations > 0 then '$>$'
		else '' end
		|| tc_max_iter.max_iter_below_limit || '&' ||
	tc_cost.cost ||
	'\\'
from
	num_nodes,
	num_edges,
	duplicate_edges,
	num_loops,
	in_degree_statistics,
	out_degree_statistics,
	tc_num_cycles,
	tc_size,
	tc_more_iter,
	tc_max_iter,
	tc_cost;

-- Standard output again:
\o
-- Normal decoration of tables:
\t off

\echo
\echo '-----------------------------------------------------------------------'
\echo 'Write result as SQL INSERT statements:'
\echo '-----------------------------------------------------------------------'
\echo

\echo "First graph_data_part.sql:"

-- Tuples only:
\t on
-- Output file:
\o graph_data_part.sql
-- The query to generate one INSERT statement for the GRAPH_DATA table:
select
	'INSERT INTO GRAPH_DATA VALUES(' ||
	'''' || :'file_id' || '''' || ',' ||
	'''' || :'input_file' || '''' || ',' ||
	num_nodes.num_nodes || ',' ||
	num_edges.num_edges || ',' ||
	duplicate_edges.duplicate_edges || ',' ||
	case when num_loops.num_loops > 0 then
		'''Y''' else '''N''' end || ',' ||
	in_degree_statistics.min_in_degree || ',' ||
	in_degree_statistics.max_in_degree || ',' ||
	out_degree_statistics.min_out_degree || ',' ||
	out_degree_statistics.max_out_degree || ',' ||
	case when tc_num_cycles.nodes_in_cycles > 0 then
		'''Y''' else '''N''' end || ',' ||
	tc_size.tc_size || ',' ||
	tc_max_iter.max_iter_below_limit || ',' ||
	:max_iter || ',' ||
	case when tc_more_iter.tc_tuples_with_more_iterations > 0 then
		'''Y''' else '''N''' end || ',' ||
	tc_more_iter.tc_tuples_with_more_iterations || ',' ||
	tc_cost.cost ||
	');'
from
	num_nodes,
	num_edges,
	duplicate_edges,
	num_loops,
	in_degree_statistics,
	out_degree_statistics,
	tc_num_cycles,
	tc_size,
	tc_more_iter,
	tc_max_iter,
	tc_cost;

-- Standard output again:
\o
-- Normal decoration of tables:
-- \t off

\echo "Now graph_indeg_part.sql:"

-- Tuples only:
-- \t on
-- Output file:
\o graph_indeg_part.sql
-- The query to generate one INSERT statement per occurring in degree:
select
	'INSERT INTO GRAPH_INDEG VALUES(' ||
	'''' || :'file_id' || '''' || ',' ||
	in_degree || ',' ||
	num_nodes ||
	');'
from in_degree_distribution
order by in_degree;

-- Standard output again:
\o
-- Normal decoration of tables:
-- \t off

\echo "Now graph_outdeg_part.sql:"

-- Tuples only:
-- \t on
-- Output file:
\o graph_outdeg_part.sql
-- The query to generate one INSERT statement per occurring out degree:
select
	'INSERT INTO GRAPH_OUTDEG VALUES(' ||
	'''' || :'file_id' || '''' || ',' ||
	out_degree || ',' ||
	num_nodes ||
	');'
from out_degree_distribution
order by out_degree;

-- Standard output again:
\o
-- Normal decoration of tables:
-- \t off

\echo "Finally graph_iter_part.sql:"

-- Tuples only:
-- \t on
-- Output file:
\o graph_iter_part.sql
-- The query to generate one INSERT statement per tc iteration (< :max_iter):
select
	'INSERT INTO GRAPH_ITER VALUES(' ||
	'''' || :'file_id' || '''' || ',' ||
	iter || ',' ||
	num_tuples ||
	');'
from tc_iter
order by iter;

-- Standard output again:
\o
-- Normal decoration of tables:
\t off

