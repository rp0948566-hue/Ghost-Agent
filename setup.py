from setuptools import setup, find_packages

setup(
    name="ghost-agent",
    version="1.0.0",
    description="AI-powered browser automation in plain English",
    author="Ghost-Agent Contributors",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.44.0",
        "openai>=1.30.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "typer>=0.12.0",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "ghost=ghost_agent.cli:main",
        ],
    },
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
