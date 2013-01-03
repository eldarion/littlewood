import glob
import os

import gc3libs

from gc3libs import Run
from gc3libs.cmdline import SessionBasedScript
from gc3libs.workflow import SequentialTaskCollection, ParallelTaskCollection


class PolynomialsApplication(gc3libs.Application):
    def __init__(self, degree, output_dir):
        self.degree = degree
        super(PolynomialsApplication, self).__init__(
            arguments=["python", "polynomials.py", degree],
            inputs=["../bin/polynomials.py"],
            outputs=["{}.poly".format(x) for x in range(10)],
            output_dir=output_dir,
            stdout="stdout.txt",
            join=True
        )


class RootsApplication(gc3libs.Application):
    def __init__(self, input_file, output_file, output_dir):
        super(RootsApplication, self).__init__(
            arguments=[
                "python",
                "roots.py",
                os.path.basename(input_file),
                os.path.basename(output_file)
            ],
            inputs=["../bin/roots.py", input_file],
            outputs=[output_file],
            output_dir=output_dir,
            stdout="stdout.txt",
            join=True
        )


class HeatmapApplication(gc3libs.Application):
    def __init__(self, size, output_dir):
        self.size = size
        inputs = ["../bin/heatmap.py"]
        inputs.extend(
            glob.glob(os.path.join(output_dir, "*.root"))
        )
        super(HeatmapApplication, self).__init__(
            arguments=["python", "heatmap.py", size],
            inputs=inputs,
            outputs=["littlewood.png"],
            output_dir=output_dir,
            stdout="stdout.txt",
            join=True
        )


class RootsCollection(ParallelTaskCollection):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        tasks = []
        for path in glob.glob(os.path.join(output_dir, "*.poly")):
            tasks.append(
                RootsApplication(
                    input_file=path,
                    output_file=os.path.basename(path.replace("poly", "root")),
                    output_dir=output_dir
                )
            )
        super(RootsCollection, self).__init__(tasks)


class LittlewoodWorkflow(SequentialTaskCollection):
    def __init__(self, size, degree):
        self.size = size
        self.degree = degree
        self.output_dir = "littlewood_{}_{}".format(size, degree)
        self.tasks = [
            PolynomialsApplication(degree, self.output_dir)
        ]
        super(LittlewoodWorkflow, self).__init__(self.tasks)
    
    def next(self, iteration):
        last_application = self.tasks[iteration]
        if isinstance(last_application, PolynomialsApplication):
            self.add(
                RootsCollection(self.output_dir)
            )
            return Run.State.RUNNING
        elif isinstance(last_application, RootsCollection):
            self.add(
                HeatmapApplication(self.size, self.output_dir)
            )
            return Run.State.RUNNING
        else:
            self.execution.returncode = last_application.execution.returncode
            return Run.State.TERMINATED


class LittlewoodScript(SessionBasedScript):
    """
    Script to make Littlewood fractals by generating roots in parallel.
    """
    version = "0.1"
    
    def setup_options(self):
        self.add_param("--size", default=400, type=int,
                       help="The size of the Littlewood fractal to generate")
        self.add_param("--degree", default=18, type=int,
                       help="The degree of the Littlewood fractal to generate")
    
    def new_tasks(self, extra):
        tasks = [
            LittlewoodWorkflow(self.params.size, self.params.degree)
        ]
        return [ParallelTaskCollection(tasks, **extra)]


if __name__ == "__main__":
    LittlewoodScript().run()
