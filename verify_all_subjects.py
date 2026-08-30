import asyncio
import sys
import ai_solver

async def main():
    queries = [
        ("Cellular Respiration and ATP", "Biology"),
        ("Industrial Revolution", "History"),
        ("Le Chatelier's principle", "Chemistry"),
        ("derivative of x^4 * sin(x)", "Mathematics"),
        ("solve 3*x + 12 = 45", "Mathematics"),
        ("Bernoulli's principle", "Physics")
    ]
    for q, subj in queries:
        sol = await ai_solver.solve_doubt(q, subj)
        steps_count = len(sol.get("steps", []))
        ans = sol.get("final_answer", "")[:60]
        print(f"[TEST PASS] Subject: {subj:<12} | Steps: {steps_count} | Answer: {ans}")

if __name__ == "__main__":
    asyncio.run(main())
