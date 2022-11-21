import flask
import collections

from ortools.linear_solver import pywraplp
from json import JSONEncoder

app = flask.Flask(__name__)

alias = [
    "john",
    "kevin",
    "larry",
    "steve",
    "mathew",
    "justin",
    "joseph",
    "carol",
    "hussein",
    "ronak",
]

chime = [
    ''
]

count = 0
discussions = dict()

encoder = JSONEncoder()

@app.route('/ui')
def ui():
    return flask.send_file("ui.htm")

@app.route('/schedule-ui')
def scheduleUi():
    return flask.send_file("schedule-ui.htm")

@app.route('/team')
def team():
    return encoder.encode(alias)

@app.route('/reset')
def reset():
    global count
    global discussions

    count = 0
    discussions = dict()

    return flask.redirect("/ui")


@app.route('/update', methods = ['POST'])
def update():
    r = flask.request.get_json()

    global discussions
    global count

    count += 1
    discussions[r["carName"] + str(count)] = r["carParticipants"]

    return flask.redirect("/ui")

@app.route('/cars')
def cars():
    global discussions

    return encoder.encode(discussions)

@app.route('/solve')
def solve():
    global discussions
    return (
        graphColor(
            createConflictGraph(discussions)
        )
    )

def createConflictGraph(schedule):
  inv = collections.defaultdict(lambda:set())
  for v, es in schedule.items():
    for e in es:
      inv[e].add(v)

  conflictGraph = collections.defaultdict(lambda:set())
  for v, es in schedule.items():
    for e in es:
      conflictGraph[v] = conflictGraph[v].union(inv[e])

    conflictGraph[v].remove(v)

  return conflictGraph

def graphColor(graph):
  solver = pywraplp.Solver.CreateSolver('SCIP')

  color = len(graph)
  var = collections.defaultdict(lambda:[None for _ in range(color)])

  for v in graph.keys():
    for c in range(color):
      var[v][c] = solver.BoolVar(v + str(c))

  # we must color each vertex exactly one color
  for v in graph.keys():
    constraint = solver.Constraint(1, 1)
    for e in var[v]:
      constraint.SetCoefficient(e, 1)

  # we cannot color two adjacent vertices the same color
  for v, es in graph.items():
    for e in es:
      for c in range(color):
        constraint = solver.Constraint(-solver.infinity(), 1)
        constraint.SetCoefficient(var[v][c], 1)
        constraint.SetCoefficient(var[e][c], 1)

  # we use the least number of colors
  colorVars = list()
  for c in range(color):
    colorVars.append(solver.BoolVar(str(c)))

    for v in graph.keys():
      constraint = solver.Constraint(-solver.infinity(), 0)
      constraint.SetCoefficient(var[v][c], 1)
      constraint.SetCoefficient(colorVars[c], -1)

  objective = solver.Objective()
  for cConstraint in colorVars:
    objective.SetCoefficient(cConstraint, 1)

  objective.SetMinimization()

  solver.Solve()

  toReturn = collections.defaultdict(lambda:list())

  for c in range(color):
    for v in graph.keys():
      if var[v][c].solution_value() > 0.99:
        toReturn[c].append(v)

  return [
      value for value in toReturn.values()
  ]

app.run(host="0.0.0.0")