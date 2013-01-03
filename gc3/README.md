# Running Littlewood in Parallel using gc3pie

## Executables

* `polynomials.py <degree>`
  Outputs files containing batches of polynomials for the given degree
* `roots.py <input file> <output file> [<inner_only>]`
  Input files are the polynamial batches
  Outputs a file containing 
* `heatmap.py <size>`
  Takes input files from the calculation of roots in parallel


## Applications

* PolynomialsApplication
* RootsApplication
* HeatmapApplication


## Workflow

* LittlewoodWorkflow(SequentialTaskCollection)
    * PolynomialsApplication
    * RootsCollection(ParallelTaskCollection)
    * HeatmapApplication


## Getting Started

To create a quick runtime environment you can setup [StarCluster](). Install
it by running:

    pip install starcluster

You'll need to setup a key and other configuration details like your Amazon
AWS account details. One small caveat in working with current star cluster
images is that you will need to login with the user you'll be connecting
with (in this example, it's `sgeadmin`) and add the following at the top
of that user's `~/.bashrc` file:

    if [[ $- != *i* ]]; then
        . /etc/profile.d/sge.sh
    fi

This is so that the SGE environment gets loaded with gc3pie connects and
attempts to queue up jobs.

Next you'll need to install gc3pie:

    pip install gc3pie

To get gc3pie working with your SGE star cluster, you'll want to setup some
configuration under `~/.gc3/gc3pie.conf`. Something that looks like this:

    [auth/mycluster]
    type=ssh
    username=sgeadmin
    
    [resource/mycluster]
    type=sge
    auth=mycluster
    transport=ssh
    frontend=ec2-23-20-140-108.compute-1.amazonaws.com
    architecture=i686
    max_cores=30
    max_cores_per_job=6
    max_memory_per_core=2
    max_walltime=2

The `frontend` key should be the hostname of the master node of your cluster.

Now you can run the demo script by running:

    python littlewood.py -C 5 -v -N

This will run a job to produce a default size of 400 and default degree of 18.
The rest of the flags are part of gc3pie. `-C 5` will continually iterate every
5 seconds until all jobs are complete, `-v` is for verbose output, and `-N`
forces a new session on every run.



