from setuptools import find_packages, setup

setup(
    name="dsg_updater",
    version="0.0.1",
    url="",
    author="Aaron Ray, Toya Takahashi",
    author_email="aray.york@gmail.com, toyatakahashi522@gmail.com",
    description="Natural language and planner updates to SparkDSG Scene Graphs",
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"": ["*.yaml", "*.pddl", "*.lark"]},
    install_requires=[
        "lark",
        "pydantic-settings",
        "spark-dsg",
        "tiktoken",
        "heracles @ git+https://github.com/GoldenZephyr/heracles.git#subdirectory=heracles",
        "heracles_agents @ git+https://github.com/GoldenZephyr/heracles_agents.git",
    ],
    extras_require={
        "openai": ["openai"],
        "anthropic": ["anthropic"],
        "ollama": ["ollama"],
        "bedrock": ["boto3"],
        "all": [
            "openai",
            "anthropic",
            "ollama",
            "boto3",
        ],
    },
)
