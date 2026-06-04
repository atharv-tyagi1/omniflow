from backend.app.main import app
import json

routes = []
for route in app.routes:
    if hasattr(route, "methods"):
        for method in route.methods:
            routes.append(f"{method} {route.path}")

print("\n--- FASTAPI ROUTES ---")
for r in sorted(routes):
    print(r)
print("--- END FASTAPI ROUTES ---")
