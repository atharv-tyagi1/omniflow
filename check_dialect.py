import asyncio
import os
import sys

# Ensure omniflow is in python path
sys.path.append(r"C:\Users\athar\OneDrive\Documents\Custom Office Templates\omniflow")

from backend.app.core.database import engine

print('ENGINE DIALECT:', engine.dialect.name)
