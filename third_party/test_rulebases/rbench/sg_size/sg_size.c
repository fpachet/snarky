#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

main()
{
	printf("Please enter height h of the inverse binary tree: ");
	int h;
	if(scanf("%d", &h) != 1) {
		printf("Error while reading tree height.\n");
		exit(1);
	}

	// Auxiliary Variables:
	int i;
	int j;
	int64_t power;

	// Compute SG Size:
	int64_t sg_size = 0;
	for(i = 0; i <= h-1; i++) {
		power = 1;
		for(j = 1; j <= 2*i; j++)
			power *= 2;
		sg_size += power;
	}
	printf("SG Size = %lld\n", sg_size);

	// Compute SG Instances:
	int64_t sg_cost = 0;
	for(i = 0; i <= h-2; i++) {
		power = 1;
		for(j = 1; j <= 2*i; j++)
			power *= 2;
		sg_cost += power;
	}
	sg_cost *= 4;
	power = 1;
	for(j = 1; j <= h; j++)
		power *= 2;
	sg_cost += power;
	sg_cost -= 2;
	printf("SG Cost = %lld\n", sg_cost);

	// Compute Number of nodes and edges:
	int64_t num_nodes = 1;
	for(i = 1; i <= h; i++)
		num_nodes *= 2;
	num_nodes--;
	printf("Nodes   = %lld\n", num_nodes);
	int64_t num_edges = num_nodes - 1;
	printf("Edges   = %lld\n", num_edges);

	// Compute TC Size:
	int64_t tc_size = 1;
	for(i = 1; i <= h; i++)
		tc_size *= 2;
	tc_size *= (h-2);
	tc_size += 2;
	printf("TC Size = %lld\n", tc_size);
}
