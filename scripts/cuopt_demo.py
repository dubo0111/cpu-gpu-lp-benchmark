from cuopt.linear_programming.problem import Problem, CONTINUOUS, MAXIMIZE
from cuopt.linear_programming.solver_settings import SolverSettings

# Create a new problem
problem = Problem("Simple LP")

# Add variables
x = problem.addVariable(lb=0, vtype=CONTINUOUS, name="x")
y = problem.addVariable(lb=0, vtype=CONTINUOUS, name="y")

# Add constraints
problem.addConstraint(x + y <= 10, name="c1")
problem.addConstraint(x - y >= 0, name="c2")

# Set objective function
problem.setObjective(x + y, sense=MAXIMIZE)

# Configure solver settings
settings = SolverSettings()
settings.set_parameter("time_limit", 60)

# Solve the problem
problem.solve(settings)

# Check solution status
if problem.Status.name == "Optimal":
    print(f"Optimal solution found in {problem.SolveTime:.2f} seconds")
    print(f"x = {x.getValue()}")
    print(f"y = {y.getValue()}")
    print(f"Objective value = {problem.ObjValue}")