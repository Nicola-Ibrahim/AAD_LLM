from typing import Any, Callable
from func_timeout import func_timeout


class AlgorithmExecutor:
    """
    Responsible for dynamically compiling and executing candidate algorithms 
    under strict timeout constraints.
    """

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def execute_algorithm(
        self, 
        code: str, 
        name: str, 
        dim: int, 
        problem: Callable[[Any], float], 
        budget: int
    ) -> float:
        """
        Dynamically execute (compile) candidate algorithm code, instantiate the class, 
        and execute it with budget and wall-clock timeout protection.
        
        Parameters
        ----------
        code : str
            The raw python code of the optimization algorithm.
        name : str
            The class name of the optimization algorithm to instantiate.
        dim : int
            The dimensionality of the search space, to be injected into the algorithm.
        problem : Callable
            The objective function to be minimized.
        budget : int
            The maximum number of evaluations allowed.
            
        Returns
        -------
        algorithm_returned_fitness : float
            The best fitness value reported by the candidate algorithm.
        """
        # --- 1. Compile candidate code & instantiate algorithm class ---
        # Execute the candidate code in a fresh local dictionary to avoid polluting globals
        local_scope: dict[str, Any] = {}
        exec(code, globals(), local_scope)
        
        # Verify the algorithm class exists in the execution scope
        if name not in local_scope:
            raise KeyError(
                f"Algorithm class '{name}' was not found after execution. "
                "Make sure the class name in your code exactly matches your proposed name."
            )
            
        algorithm_cls = local_scope[name]
        algorithm = algorithm_cls()

        # Inject search space dimensionality if the algorithm class expects it
        if hasattr(algorithm, 'dim'):
            algorithm.dim = dim
            
        # --- 2. Execute candidate run with timeout protection ---
        algorithm_returned_fitness = func_timeout(
            self.timeout_seconds, 
            algorithm, 
            args=(problem, budget)
        )
        
        if algorithm_returned_fitness is None:
            raise TypeError(
                "The algorithm did not return a valid fitness/objective value. "
                "Make sure your __call__ method returns the best found float value."
            )
            
        return float(algorithm_returned_fitness)
