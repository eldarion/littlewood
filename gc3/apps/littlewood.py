"""
Open Questions

1. How do I send {}.poly to a single Roots instance?
2. How do I merge all the roots.dat from all the Roots instances?
3. Is there a way to push out the code that is needed to execute or
   does it have to be pre-installed?
"""
import gc3libs

from gc3libs import Run
from gc3libs.workflow import SequentialTaskCollection, ParallelTaskCollection


class Polynomials(gc3libs.Application):
    def __init__(self, degree):
        self.degree = degree
        super(Polynomials, self).__init__(
            arguments=["python", "polynomials.py", degree],
            inputs=[],
            outputs=["{}.poly".format(x) for x in range(10)]
        )


class Roots(gc3libs.Application):
    def __init__(self):
        super(Roots, self).__init__(
            arguments=["python", "roots.py"],
            inputs=["polys.dat"],
            outputs=["roots.dat"],
            stdout="stdout.txt",
            join=True
        )


class Heatmap(gc3libs.Application):
    def __init__(self, size):
        self.size = size
        super(Heatmap, self).__init__(
            arguments=["python", "heatmap.py", size],
            inputs=[],
            outputs=["littlewood.png"],
            stdout="stdout.txt",
            join=True
        )


class RootsCollection(ParallelTaskCollection):
    def __init__(self):
        self.tasks = [Roots() for x in range(10)]
        super(RootsCollection, self).__init__(self.tasks)


class Littlewood(SequentialTaskCollection):
    def __init__(self, size, degree):
        self.size = size
        self.degree = degree
        self.tasks = [
            Polynomials(degree)
        ]
        super(Littlewood, self).__init__(self.tasks)
    
    def next(self, iteration):
        last_application = self.tasks[iteration]
        if isinstance(last_application, Polynomials):
            self.add(
                RootsCollection()
            )
            return Run.State.RUNNING
        elif isinstance(last_application, RootsCollection):
            self.add(
                Heatmap(self.size)
            )
            return Run.State.RUNNING
        else:
            self.execution.returncode = last_application.execution.returncode
            return Run.State.TERMINATED
