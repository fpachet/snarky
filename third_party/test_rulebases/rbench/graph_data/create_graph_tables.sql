
create table graph_data (
	file_id        varchar(10) not null primary key,
	file_name      varchar(80) not null unique,
	num_nodes      integer     not null check(num_nodes >= 0),
	num_edges      integer     not null check(num_edges >= 0),
	dup_edges      integer     not null check(dup_edges >= 0),
	loops          char(1)     not null check(loops  in ('Y','N')),
	min_in_degree  integer     not null check(min_in_degree >= 0),
	max_in_degree  integer     not null check(max_in_degree >= 0),
	min_out_degree integer     not null check(min_out_degree >= 0),
	max_out_degree integer     not null check(max_out_degree >= 0),
	cycles         char(1)     not null check(cycles in ('Y','N')),
	tc_size        integer     not null check(tc_size >= 0),
	num_iter       integer     not null check(num_iter >= 0),
	max_iter       integer     not null check(max_iter >= 0),
	limit_reached  char(1)     not null check(limit_reached in ('Y','N')),
	missing_rows   integer     not null check(missing_rows >= 0),
	cost           bigint      not null check(cost >= 0)
);

create table graph_iter (
	file_id        varchar(10) not null references graph_data,
	iter           integer     not null check(iter >= 0),
	num_rows       integer     not null check(num_rows >= 0),
	primary key (file_id, iter)
);

create table graph_indeg (
	file_id        varchar(10) not null references graph_data,
	in_degree      integer     not null check(in_degree >= 0),
	num_nodes      integer     not null check(num_nodes >= 0),
	primary key (file_id, in_degree)
);

create table graph_outdeg (
	file_id        varchar(10) not null references graph_data,
	out_degree     integer     not null check(out_degree >= 0),
	num_nodes      integer     not null check(num_nodes >= 0),
	primary key (file_id, out_degree)
);

