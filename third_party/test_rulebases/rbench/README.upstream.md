rbench - A Benchmark Package for Checking Query Performance
===========================================================

This is a set of programs/scripts and a relational database to check the
query evaluation performance of
* Logic Programming Systems (e.g. Prolog with Tabling such as XSB)
* Deductive Databases / Datalog Systems
* Relational Databases (with SQL)
* Graph Databases / RDF Stores

The benchmarks were inspired by the
[OpenRuleBench](http://rulebench.semwebcentral.org/),
see also
[OpenRuleBench Download](http://www3.cs.stonybrook.edu/~pfodor/openrulebench/download.html).

Currently, our set of benchmarks is much smaller than those of OpenRuleBench,
but
* We support executing the same benchmark multiple times
  (this should be standard practice, but is not supported by OpenRuleBench)
* We support storing and comparing runtimes for different implementation
  variants of the same benchmark on the same system
  (wish, e.g., different indexes or different option settings)
* We support storing and comparing results for different versions of a system,
  or performance measurements on different computers.
* We invested work to generate more input datafiles with different
  characteristics.

How to get rbench:
------------------

* The rbench software package is available via git:

    `git clone git@gitlab.informatik.uni-halle.de:brass/rbench`

* For more information see the project webpage:

    [http://dbs.informatik.uni-halle.de/rbench/]

Current developers:
------------------
* Stefan Brass (brass@informatik.uni-halle.de)
* Mario Wenzel (mario.wenzel@informatik.uni-halle.de)

If you should find this software useful,
or want to contribute something,
please send us an email.
In particular,
if you are an expert on one of the tested systems,
and have suggestions for other options settings to improve performance
for a benchmark,
please let us know.
We will run the benchmark with your settings,
and if it is better than our previous settings,
the results on the project webpage will be updated.
In any case,
the database will contain the alternative settings
and the runtime results.

Directories:
-----------

* db:
  This contains the SQL code for the central database to store the runtime
  measurements.
  It has also many views to evaluate the data.
* db/results:
  The data of the single runtime measurements that we did.
* www:
  Code to generate our webpage
* xsb:
  Scripts (classic version) to run the benchmarks for
  [XSB](http://xsb.sourceforge.net/)
* yap:
  Scripts (classic version) to run the benchmarks for
  [YAProlog](https://www.dcc.fc.up.pt/~vsc/Yap/)
* bam:
  Scripts (classic version) to run the benchmarks for
  for our Bottom-Up Abstract Machine
  [BAM](http://users.informatik.uni-halle.de/~brass/push/bam.html)
* ydb:
  Scripts (classic version) to run the benchmarks for
  for our older Push Method Test Software
  [ydb](http://users.informatik.uni-halle.de/~brass/push/)
* swipl:
  Code to run the benchmarks for
  [SWI Prolog](http://www.swi-prolog.org/)
* jena:
  Code to run the benchmarks for
  [Apache Jena](https://jena.apache.org/)
* sqlite:
  Code to run the benchmarks for
  [SQLite3](https://www.sqlite.org/index.html)
* mariadb:
  Code to run the benchmarks for
  [MariaDB](https://www.mariadb.com)
* pg:
  Code to run the benchmarks for
  [PostgreSQL](https://www.postgresql.org)
* sql:
  The SQL queries used by the relational databases.
  The CREATE TABLE statements are system-specific.
* souffle
  Code to run the benchmarks for
  [Souffle](http://souffle-lang.org/)
* datascript
  Code to run the benchmarks for
  [DataScript](https://github.com/tonsky/datascript)
* graph_data:
  SQL scripts to analyze the data files for the tc benchmark
* graph_data_pl:
  A small Prolog program to find the number of iterations
  for the bottom-up computation of the transitive closure.
  Our current SQL solution in graph_data sometimes takes very long
  for this task.
* opt:
  A C++ program to find good parameters for runtime estimation
  of the transitive closure benchmark.
  This is part of our research, but not necessary for our benchmarking suite.
* hsqldb:
  Code to run the benchmarks for
  [HSQLDB](http://hsqldb.org/)
  This is currently under construction.
* misc:
  These are files that are no longer used,
  but somehow we could not decide to delete them.
  You may delete them.

Input Data Files:
----------------

One also has to get the input data files in a format required by the
system to be tested:
* [Prolog](http://dbs.informatik.uni-halle.de/rbench/instances/inst_P.tar.gz)
  These should be stored in the directory data_p.
* [tsv](http://dbs.informatik.uni-halle.de/rbench/instances/inst_tsv.tar.gz)
  These should be stored in the directory data_tsv.
* [csv](http://dbs.informatik.uni-halle.de/rbench/instances/inst_csv.tar.gz)
* [json](http://dbs.informatik.uni-halle.de/rbench/instances/inst_json.tar.gz)
* [SQL](http://dbs.informatik.uni-halle.de/rbench/instances/inst_sql.tar.gz)
* [RDF ttl](http://dbs.informatik.uni-halle.de/rbench/instances/inst_ttl.tar.gz)
* [dot](http://dbs.informatik.uni-halle.de/rbench/instances/inst_dot.tar.gz)
* See also the old data files:
  [data](http://users.informatik.uni-halle.de/~brass/push/data/)
* The graph data files were generated with our program
  [graphgen](https://gitlab.informatik.uni-halle.de/mwenzel/graphgen)

Software dependencies:
---------------------

* Our SQL code (e.g., for the benchmark database) was tested with
  PostgreSQL 9.2.24.
  We would be interested to hear about compatibility problems with other RDBMS
  and would try to solve them.
* We also use many shell scripts (that work under bash on Linux).
* db/conv_sql is an AWK script.
* Of course, the programs to be tested must be installed.
  However, in a related project,
  we are developing software to automate the benchmarking further.
  That software also automatically installs the systems to be tested.

More Documentation:
------------------

* Documentation of the database is in
    db/db_doc.md
* We are working on a README file in each subdirectory

How to Use This Software:
------------------------

* If you are just interested in the main benchmark results,
  you don't need to install anything,
  we publish the results on the
  [Project Webpage](http://dbs.informatik.uni-halle.de/rbench/)

* If you want to check more details of our measurements,
  get PostgreSQL (or another relational database),
  and execute the script `db/load_data`.
  If that does not work,
  run the SQL commands in
    - `db/drop_db.sql` (unless this is the first run)
    - `db/create_db.sql`
    - `db/input_files.sql`
    - `db/input_sets.sql`
    - `db/input_graphs.sql`
    - all files with the single measurements: `db/results/*.sql`
  You should also read the database documentation in `db/db_doc.md`.

* If you want to do your own measurements with one of the existing systems,
    - get the data files,
    - create a symbolic link e.g. from `data_p` to where you unpacked
      the Prolog facts version of the data files,
    - run the `run_bench_list` in the subdirectory for the system
      of your choice, this produces a file of the form
      `<SYSTEM>_<INSTALL_NUMBER>_<MACHINE>_<YEAR>_<MONTH>_<DAY>.tsv`
      with the measurements.
      Move these to the `db/results` directory.
    - Execute `../conv_sql <FILE>.tsv` in the `db/results` directory
      to turn the .tsv-file to SQL INSERT statements.
    - These can be loaded to the database.
      Actually, `db/load_data` will automatically do that
      (the existing tables will be deleted first, and all data in the
       `db/results` directory will be imported again).

* Some Examples of SQL Queries:
    - select * from benchmark;
    - select * from xsb;

* If you want to add your own system:
  Stay tuned. More information will be added soon.
  Send us an email to get it faster.

