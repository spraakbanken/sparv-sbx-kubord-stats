"""Install script for the Kubord stats Sparv plugin."""

import setuptools

setuptools.setup(
    name="sparv-sbx-kubord-stats",
    version="1.0",
    description="Sparv exporter for kubord stats files",
    license="MIT",
    author="Språkbanken",
    author_email="sb-info@svenska.gu.se",
    packages=["sbx_kubord_stats"],
    python_requires=">=3.6.2",
    install_requires=["sparv-pipeline>=5.0.0,<6"],
    entry_points={"sparv.plugin": ["sbx_kubord_stats = sbx_kubord_stats"]}
)
