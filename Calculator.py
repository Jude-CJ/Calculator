from pathlib import Path
import ast
import math
import operator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Calculator API")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CalculationRequest(BaseModel):
	expression: str = Field(min_length=1, max_length=100)


class CalculationResponse(BaseModel):
	expression: str
	result: float | int


BINARY_OPERATORS = {
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
	ast.Pow: operator.pow,
	ast.Mod: operator.mod,
}
UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
SCIENTIFIC_FUNCTIONS = {
	"sin": math.sin,
	"cos": math.cos,
	"tan": math.tan,
	"sqrt": math.sqrt,
	"log": math.log10,
	"ln": math.log,
	"abs": abs,
	"floor": math.floor,
	"ceil": math.ceil,
}
SCIENTIFIC_CONSTANTS = {"pi": math.pi, "e": math.e}


def evaluate_expression(expression: str) -> float | int:
	try:
		tree = ast.parse(expression, mode="eval")
		return evaluate_node(tree.body)
	except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
		raise ValueError("Invalid calculation") from error


def evaluate_node(node: ast.AST) -> float | int:
	if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
		if isinstance(node.value, bool):
			raise ValueError("Boolean values are not supported")
		return node.value

	if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
		left = evaluate_node(node.left)
		right = evaluate_node(node.right)
		if isinstance(node.op, ast.Pow) and abs(right) > 100:
			raise ValueError("Exponent is too large")
		return BINARY_OPERATORS[type(node.op)](left, right)

	if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
		return UNARY_OPERATORS[type(node.op)](evaluate_node(node.operand))

	if isinstance(node, ast.Name) and node.id in SCIENTIFIC_CONSTANTS:
		return SCIENTIFIC_CONSTANTS[node.id]

	if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in SCIENTIFIC_FUNCTIONS:
		if len(node.args) != 1 or node.keywords:
			raise ValueError("Scientific functions accept one value")
		return SCIENTIFIC_FUNCTIONS[node.func.id](evaluate_node(node.args[0]))

	raise ValueError("Only numbers and calculator operators are supported")


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
	return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/calc", response_model=CalculationResponse)
async def calculate(request: CalculationRequest) -> CalculationResponse:
	try:
		result = evaluate_expression(request.expression)
	except ValueError as error:
		raise HTTPException(status_code=400, detail=str(error)) from error
	return CalculationResponse(expression=request.expression, result=result)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("Calculator:app", host="127.0.0.1", port=8000, reload=True)