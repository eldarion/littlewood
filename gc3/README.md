# Running Littlewood in Parallel using gc3pie

## Executables

* `polynomials.py <degree>`
  Outputs files containing batches of polynomials for the given degree
* `roots.py [<inner_only>]`
  Input files are the polynamial batches
  Outputs a file containing 
* `heatmap.py <size>`
  Takes input files from the calculation of roots in parallel


## Applications

* PolynomialChunksApplication
* RootsApplication
* HeatmapApplication


## Workflow

* Littlewood(SequentialTaskCollection)
    * PolynomialChunksApplication
    * RootsCollection(ParallelTaskCollection)
    * HeatmapApplication
