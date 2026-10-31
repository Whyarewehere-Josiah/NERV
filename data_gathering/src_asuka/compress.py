import datetime
import os
import shutil
import tarfile
import tempfile
from pathlib import Path


def main_compress() -> Path:
    day = datetime.date.today().isoformat()
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1]
    source_folder = script_dir / "data" / day
    output_filename = project_root / f"{day}.tar.gz"

    if not source_folder.is_dir():
        raise FileNotFoundError(f"Data folder does not exist: {source_folder}")

    file_descriptor, temporary_filename = tempfile.mkstemp(
        prefix=f".{output_filename.name}.",
        suffix=".tmp",
        dir=project_root,
    )
    os.close(file_descriptor)
    temporary_archive = Path(temporary_filename)

    try:
        with tarfile.open(temporary_archive, "w:gz") as tar:
            tar.add(
                source_folder,
                arcname=Path("data_gathering") / "src_asuka" / "data" / day,
            )
        os.replace(temporary_archive, output_filename)
    except Exception:
        if temporary_archive.exists():
            temporary_archive.unlink()
        raise

    shutil.rmtree(source_folder)
    return output_filename


if __name__ == "__main__":
    main_compress()
