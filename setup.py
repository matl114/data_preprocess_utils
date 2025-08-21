from setuptools import setup, find_packages
# setup(
#     name= "data_preprocess_utils",
#     version= "v1.0.0",
#     packages= ["data_preprocess_utils"]
# )
setup(
    name="data_preprocess_utils",
    version="v1.0.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "requests",
        "pypdfium2",
        "lxml",
        "langchain",
        "langchain-community",
        "langchain-core",
        "langchain-ollama",
        "matplotlib",
        "pillow",
        "pydantic",
        "pyarrow"
    ],
)