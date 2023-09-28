from pathlib import Path


class ConfigConstants:
    CT_KEY = "cell_type"


def _sanity_check_config(config: dict):
    for key in ["sdata_path"]:
        assert key in config.keys(), f"config['{key}'] is required to run the pipeline"

    if ConfigConstants.CT_KEY not in config["annotation"]:
        config["annotation"][ConfigConstants.CT_KEY] = ConfigConstants.CT_KEY

    return config


class WorkflowPaths:
    def __init__(self, config: dict) -> None:
        self.config = _sanity_check_config(config)

        self.sdata_path = Path(self.config["sdata_path"])
        self.sdata_zgroup = self.sdata_path / ".zgroup"  # trick to fix snakemake ChildIOException
        self.raw = self.sdata_path.with_suffix(".qptiff")  # TODO: make it general

        self.shapes_dir = self.sdata_path / "shapes"
        self.points_dir = self.sdata_path / "points"
        self.images_dir = self.sdata_path / "images"
        self.table_dir = self.sdata_path / "table"

        self.run_cellpose = "cellpose" in self.config["segmentation"]
        self.run_baysor = "baysor" in self.config["segmentation"]

        self.polygons = self.shapes_dir / "polygons"
        self.patches = self.shapes_dir / "patches"

        self.smk_files = self.sdata_path / ".smk_files"
        self.table = self.smk_files / "table"
        self.n_patches_path = self.smk_files / ".n_patches"

        self.annotations = (
            self.table_dir / "table" / "obs" / self.config["annotation"][ConfigConstants.CT_KEY]
        )

        self.temp_dir = self.sdata_path.parent / f"{self.sdata_path.name}_temp"
        self.cellpose_dir = self.temp_dir / "cellpose"
        self.baysor_dir = self.temp_dir / "baysor"

        self.explorer_directory = self.sdata_path.with_suffix(".explorer")
        self.explorer_directory.mkdir(parents=True, exist_ok=True)

        self.explorer_experiment = self.explorer_directory / "experiment.xenium"

    def cells_paths(self, n: int, name):
        if name == "cellpose":
            return [self.cellpose_dir / f"{i}.zarr.zip" for i in range(n)]
        if name == "baysor":
            return [self.baysor_dir / {i} / "segmentation_polygons.json" for i in range(n)]

    def dump_baysor_patchify(self):
        if not self.run_baysor:
            return ""

        return (
            dump_args(self.config["segmentation"]["baysor"], "baysor-")
            + f" --baysor-dir {self.baysor_dir}"
        )


def _dump_arg(key: str, value, prefix: str = ""):
    option = f"--{prefix}{key.replace('_', '-')}"
    if isinstance(value, list):
        for v in value:
            yield from (option, str(v))
    elif isinstance(value, dict):
        yield from (option, '"' + str(value).replace("{", "{{").replace("}", "}}") + '"')
    elif value is True:
        yield option
    elif value is False:
        yield f"--no-{prefix}{key.replace('_', '-')}"
    else:
        yield from (option, str(value))


def dump_args(args: dict, prefix: str = "") -> str:
    return " ".join((res for item in args.items() for res in _dump_arg(*item, prefix)))
